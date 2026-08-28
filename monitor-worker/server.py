#!/usr/bin/env python3
"""TradeMind Monitor Worker v1.0 — Zero-dependency system monitoring server.

Pure Python stdlib. No pip, no Docker, no third-party packages.
Designed for AGX Xavier bare-metal deployment.

Port: 8080
Endpoints:
  GET  /health    — Health check
  GET  /metrics   — Current system metrics (CPU, RAM, disk, network, GPU)
  GET  /services  — Cluster-wide worker health probe
  GET  /cluster   — Cluster topology and status
  GET  /version   — Version info
"""

import json
import os
import re
import socket
import struct
import sys
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError

PORT = 8080
SERVICE_NAME = "monitor-worker"
VERSION = "1.0.0"
WORKER_ID = "xavier-worker-04"
_start_time = datetime.utcnow()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

# Cluster node definitions
CLUSTER_NODES = [
    {"id": "worker-01", "name": "Indicator Worker",  "host": "192.168.1.200", "port": 8080, "role": "indicator"},
    {"id": "worker-02", "name": "Stock Factor Worker", "host": "192.168.1.201", "port": 8080, "role": "factor"},
    {"id": "worker-03", "name": "Backtest Worker",   "host": "192.168.1.202", "port": 8080, "role": "backtest"},
    {"id": "worker-04", "name": "Monitor Worker",    "host": "192.168.1.203", "port": 8080, "role": "monitor"},
]

# Cache for last probe results
_probe_cache = {"last_check": None, "results": []}


# ── System Metrics (Linux /proc, /sys) ────────────────────────────────

def _read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except (IOError, OSError):
        return None


def _read_cpu_times():
    """Parse /proc/stat for CPU times."""
    line = _read_file("/proc/stat")
    if not line:
        return None
    parts = line.split()
    if len(parts) < 5:
        return None
    # user, nice, system, idle, iowait, irq, softirq, steal
    vals = [int(x) for x in parts[1:9]]
    idle = vals[3] + vals[4]
    total = sum(vals)
    return {"idle": idle, "total": total}


def _get_cpu_percent():
    """Calculate CPU usage from two /proc/stat snapshots."""
    t1 = _read_cpu_times()
    if not t1:
        return 0.0
    time.sleep(0.1)
    t2 = _read_cpu_times()
    if not t2:
        return 0.0
    d_idle = t2["idle"] - t1["idle"]
    d_total = t2["total"] - t1["total"]
    if d_total == 0:
        return 0.0
    return round((1.0 - d_idle / d_total) * 100.0, 1)


def _get_memory():
    """Parse /proc/meminfo for memory stats."""
    data = _read_file("/proc/meminfo")
    if not data:
        return {}
    info = {}
    for line in data.split("\n"):
        parts = line.split(":")
        if len(parts) == 2:
            key = parts[0].strip()
            val = parts[1].strip().split()[0]
            info[key] = int(val)
    total = info.get("MemTotal", 0)
    available = info.get("MemAvailable", info.get("MemFree", 0))
    used = total - available
    return {
        "total_kb": total,
        "used_kb": used,
        "available_kb": available,
        "total_gb": round(total / 1048576.0, 2),
        "used_gb": round(used / 1048576.0, 2),
        "percent": round(used / total * 100.0, 1) if total > 0 else 0.0,
        "swap_total_kb": info.get("SwapTotal", 0),
        "swap_used_kb": info.get("SwapTotal", 0) - info.get("SwapFree", 0),
    }


def _get_disk():
    """Get disk usage for / partition."""
    try:
        stat = os.statvfs("/")
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bavail * stat.f_frsize
        used = total - free
        return {
            "total_gb": round(total / (1024 ** 3), 2),
            "used_gb": round(used / (1024 ** 3), 2),
            "free_gb": round(free / (1024 ** 3), 2),
            "percent": round(used / total * 100.0, 1) if total > 0 else 0.0,
        }
    except (OSError, IOError):
        return {}


def _get_network():
    """Parse /proc/net/dev for network stats."""
    data = _read_file("/proc/net/dev")
    if not data:
        return {}
    interfaces = {}
    for line in data.split("\n")[2:]:
        line = line.strip()
        if not line or ":" not in line:
            continue
        iface, rest = line.split(":", 1)
        iface = iface.strip()
        if iface == "lo":
            continue
        vals = rest.split()
        if len(vals) >= 10:
            interfaces[iface] = {
                "rx_bytes": int(vals[0]),
                "rx_packets": int(vals[1]),
                "tx_bytes": int(vals[8]),
                "tx_packets": int(vals[9]),
            }
    return interfaces


def _get_load_avg():
    """Parse /proc/loadavg."""
    data = _read_file("/proc/loadavg")
    if not data:
        return {}
    parts = data.split()
    return {
        "1min": float(parts[0]),
        "5min": float(parts[1]),
        "15min": float(parts[2]),
    }


def _get_uptime():
    """Parse /proc/uptime."""
    data = _read_file("/proc/uptime")
    if not data:
        return 0.0
    return float(data.split()[0])


def _get_gpu_info():
    """Get GPU info via nvidia-smi (best-effort on Xavier)."""
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            line = result.stdout.decode("utf-8", errors="replace").strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                return {
                    "name": parts[0],
                    "memory_used_mb": int(parts[1]),
                    "memory_total_mb": int(parts[2]),
                    "utilization_percent": int(parts[3]),
                    "temperature_c": int(parts[4]),
                }
    except (OSError, subprocess.TimeoutExpired):
        pass

    # Fallback: try thermal zone for GPU temp on Xavier
    try:
        temp_raw = _read_file("/sys/class/thermal/thermal_zone0/temp")
        if temp_raw:
            return {
                "name": "AGX Xavier (thermal fallback)",
                "temperature_c": round(int(temp_raw.strip()) / 1000.0, 1),
            }
    except (ValueError, TypeError):
        pass

    return {"name": "unavailable"}


def _get_process_count():
    """Count processes via /proc."""
    try:
        return len([d for d in os.listdir("/proc") if d.isdigit()])
    except OSError:
        return 0


def _get_hostname():
    """Get hostname."""
    try:
        return socket.gethostname()
    except OSError:
        return "unknown"


def _get_local_ip():
    """Get the local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except (OSError, socket.error):
        return "127.0.0.1"


# ── Worker Health Probe ───────────────────────────────────────────────

def _probe_worker(node, timeout=3):
    """HTTP GET /health from a worker node. Skip self to avoid deadlock."""
    if node["host"] == "192.168.1.203" or node["id"] == WORKER_ID:
        return {
            "reachable": True,
            "status": SERVICE_NAME,
            "version": VERSION,
            "probe_latency_ms": 0,
        }
    url = "http://%s:%d/health" % (node["host"], node["port"])
    t0 = time.perf_counter()
    try:
        resp = urlopen(url, timeout=timeout)
        data = json.loads(resp.read().decode("utf-8"))
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        data["probe_latency_ms"] = elapsed_ms
        data["reachable"] = True
        return data
    except (URLError, socket.timeout, OSError, json.JSONDecodeError) as e:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "reachable": False,
            "error": str(e),
            "probe_latency_ms": elapsed_ms,
        }


def _probe_all_workers():
    """Probe all cluster workers and return results."""
    this_ip = _get_local_ip()
    results = []
    for node in CLUSTER_NODES:
        if node["host"] == this_ip or node["host"] == "127.0.0.1":
            results.append({
                "node": node,
                "reachable": True,
                "probe_latency_ms": 0,
                "status": "self",
            })
            continue
        result = _probe_worker(node)
        result["node"] = node
        results.append(result)
    _probe_cache["last_check"] = datetime.utcnow().isoformat()
    _probe_cache["results"] = results
    return results


# ── Collect Full Metrics ──────────────────────────────────────────────

def _collect_all_metrics():
    """Collect all system metrics in one call."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "hostname": _get_hostname(),
        "uptime_seconds": round(_get_uptime(), 1),
        "cpu_percent": _get_cpu_percent(),
        "memory": _get_memory(),
        "disk": _get_disk(),
        "network": _get_network(),
        "load_avg": _get_load_avg(),
        "gpu": _get_gpu_info(),
        "process_count": _get_process_count(),
    }


# ── HTTP Handler ──────────────────────────────────────────────────────

class MonitorHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        sys.stderr.write("[%s] %s\n" % (ts, fmt % args))

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            now = datetime.utcnow()
            self._send_json({
                "status": "healthy",
                "service": SERVICE_NAME,
                "version": VERSION,
                "worker_id": WORKER_ID,
                "hostname": _get_hostname(),
                "uptime_seconds": round((now - _start_time).total_seconds(), 3),
                "timestamp": now.isoformat(),
            })

        elif path == "/metrics":
            metrics = _collect_all_metrics()
            self._send_json(metrics)

        elif path == "/services":
            results = _probe_all_workers()
            healthy = sum(1 for r in results if r.get("reachable"))
            self._send_json({
                "total_nodes": len(CLUSTER_NODES),
                "healthy_nodes": healthy,
                "unhealthy_nodes": len(CLUSTER_NODES) - healthy,
                "last_check": _probe_cache["last_check"],
                "nodes": [
                    {
                        "id": r["node"]["id"],
                        "name": r["node"]["name"],
                        "host": r["node"]["host"],
                        "port": r["node"]["port"],
                        "reachable": r.get("reachable", False),
                        "status": r.get("status", "unreachable"),
                        "latency_ms": r.get("probe_latency_ms", 0),
                    }
                    for r in results
                ],
            })

        elif path == "/cluster":
            metrics = _collect_all_metrics()
            probe_results = _probe_all_workers()
            healthy = sum(1 for r in probe_results if r.get("reachable"))
            self._send_json({
                "cluster": {
                    "total_nodes": len(CLUSTER_NODES),
                    "healthy_nodes": healthy,
                    "this_node": {
                        "id": WORKER_ID,
                        "host": "192.168.1.203",
                        "port": PORT,
                        "role": "monitor",
                    },
                },
                "this_node_metrics": metrics,
                "workers": [
                    {
                        "id": r["node"]["id"],
                        "name": r["node"]["name"],
                        "host": r["node"]["host"],
                        "port": r["node"]["port"],
                        "role": r["node"]["role"],
                        "reachable": r.get("reachable", False),
                        "status": r.get("status", "unreachable"),
                        "worker_version": r.get("version", None),
                        "latency_ms": r.get("probe_latency_ms", 0),
                    }
                    for r in probe_results
                ],
                "timestamp": datetime.utcnow().isoformat(),
            })

        elif path == "/version":
            self._send_json({
                "name": SERVICE_NAME,
                "version": VERSION,
                "worker_id": WORKER_ID,
                "hostname": _get_hostname(),
                "python": "%d.%d.%d" % sys.version_info[:3],
                "uptime_seconds": round((datetime.utcnow() - _start_time).total_seconds(), 1),
            })

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/monitor":
            try:
                metrics = _collect_all_metrics()
                probe_results = _probe_all_workers()
                healthy = sum(1 for r in probe_results if r.get("reachable"))
                self._send_json({
                    "success": True,
                    "cluster": {
                        "total_nodes": len(CLUSTER_NODES),
                        "healthy_nodes": healthy,
                        "this_node": {
                            "id": WORKER_ID,
                            "host": "192.168.1.203",
                            "port": PORT,
                            "role": "monitor",
                        },
                    },
                    "this_node_metrics": metrics,
                    "workers": [
                        {
                            "id": r["node"]["id"],
                            "name": r["node"]["name"],
                            "host": r["node"]["host"],
                            "port": r["node"]["port"],
                            "role": r["node"]["role"],
                            "reachable": r.get("reachable", False),
                            "status": r.get("status", "unreachable"),
                            "worker_version": r.get("version", None),
                            "latency_ms": r.get("probe_latency_ms", 0),
                        }
                        for r in probe_results
                    ],
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                sys.stderr.write("[ERROR] /monitor: %s\n%s\n" % (str(e), tb))
                sys.stderr.flush()
                self._send_json({"success": False, "error": str(e)}, 500)
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ── Main ──────────────────────────────────────────────────────────────

def main():
    server = ThreadedHTTPServer(("0.0.0.0", PORT), MonitorHandler)
    print("=" * 60)
    print("  TradeMind Monitor Worker v%s" % VERSION)
    print("  Worker ID: %s" % WORKER_ID)
    print("  Port: %d" % PORT)
    print("  Hostname: %s" % _get_hostname())
    print("  Python: %s" % sys.version.split()[0])
    print("  Started: %s" % datetime.now().isoformat())
    print("  Cluster nodes: %d" % len(CLUSTER_NODES))
    print("=" * 60)
    print("  Endpoints:")
    print("    GET  http://0.0.0.0:%d/health" % PORT)
    print("    GET  http://0.0.0.0:%d/metrics" % PORT)
    print("    GET  http://0.0.0.0:%d/services" % PORT)
    print("    GET  http://0.0.0.0:%d/cluster" % PORT)
    print("    GET  http://0.0.0.0:%d/version" % PORT)
    print("=" * 60)
    sys.stdout.flush()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[OK] Shutdown")
        server.server_close()


if __name__ == "__main__":
    main()
