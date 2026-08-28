"""Worker discovery with background health probe for TradeMind Master API v1.2.

Loads static worker definitions from workers.json. A background daemon thread
periodically probes GET /health on every worker and caches the results, so
list_workers() never blocks on network I/O.
"""

import json
import logging
import threading
import time

import requests

from app.config.settings import Settings, get_settings
from app.model.schemas import WorkerInfo, WorkerStatus

logger = logging.getLogger(__name__)

PROBE_TIMEOUT_SECONDS = 3.0
DEFAULT_PROBE_INTERVAL = 10.0


class _ProbeCache:
    __slots__ = ("status", "latency_ms", "last_seen", "consecutive_failures")

    def __init__(self):
        self.status = WorkerStatus.OFFLINE
        self.latency_ms = None
        self.last_seen = None
        self.consecutive_failures = 0


class WorkerRegistry:

    def __init__(self, settings=None):
        self._settings = settings or get_settings()
        self._cache = {}
        self._records = []
        self._records_lock = threading.Lock()
        probe_interval = getattr(self._settings.worker, "probe_interval_seconds", None)
        self._probe_interval = float(probe_interval) if probe_interval else DEFAULT_PROBE_INTERVAL
        self._start_background_probe()

    def list_workers(self):
        records = self._read_workers_json()
        with self._records_lock:
            self._records = records
        return [self._build_from_cache(r) for r in records]

    def select_worker(self, worker_type):
        for w in self.list_workers():
            if w.worker_type == worker_type and w.status == WorkerStatus.ONLINE:
                return w
        return None

    def worker_base_url(self, worker):
        return "http://{0}:{1}".format(worker.host, worker.port)

    def _start_background_probe(self):
        t = threading.Thread(target=self._probe_loop, name="health-probe")
        t.daemon = True
        t.start()
        logger.info("Background health probe started (interval=%.1fs)", self._probe_interval)

    def _probe_loop(self):
        while True:
            try:
                self._probe_all()
            except Exception:
                logger.exception("Health probe cycle failed")
            time.sleep(self._probe_interval)

    def _probe_all(self):
        records = self._read_workers_json()
        for record in records:
            static = self._static_fields(record)
            wid = static["id"]
            if wid not in self._cache:
                self._cache[wid] = _ProbeCache()
            cache = self._cache[wid]
            url = "http://{0}:{1}/health".format(static["host"], static["port"])
            started = time.perf_counter()
            try:
                resp = requests.get(url, timeout=PROBE_TIMEOUT_SECONDS)
                if resp.status_code == 200:
                    cache.latency_ms = int((time.perf_counter() - started) * 1000)
                    cache.status = WorkerStatus.ONLINE
                    cache.last_seen = time.time()
                    cache.consecutive_failures = 0
                else:
                    self._mark_offline(cache)
            except Exception:
                self._mark_offline(cache)

    @staticmethod
    def _mark_offline(cache):
        cache.status = WorkerStatus.OFFLINE
        cache.latency_ms = None
        cache.consecutive_failures += 1

    def _read_workers_json(self):
        path = self._settings.workers_path
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            return []
        return data

    @staticmethod
    def _static_fields(record):
        worker_id = record.get("id") or record.get("worker_id") or ""
        return {
            "id": worker_id,
            "name": record.get("name") or worker_id,
            "worker_type": record.get("worker_type") or record.get("type") or "",
            "host": record.get("host", ""),
            "port": int(record.get("port", 0)),
            "description": record.get("description", ""),
        }

    def _build_from_cache(self, record):
        static = self._static_fields(record)
        cache = self._cache.get(static["id"])
        return WorkerInfo(
            id=static["id"],
            name=static["name"],
            worker_type=static["worker_type"],
            host=static["host"],
            port=static["port"],
            description=static["description"],
            status=cache.status if cache else WorkerStatus.OFFLINE,
            latency_ms=cache.latency_ms if cache else None,
        )