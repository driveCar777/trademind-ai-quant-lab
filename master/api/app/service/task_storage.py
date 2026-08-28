"""Task metadata and result persistence for TradeMind Master API v1.1.

All file I/O for tasks/results/counter goes through this module.
Writes use atomic tmp -> fsync -> rename.
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.config.settings import Settings, get_settings

TASK_ID_PATTERN = re.compile(r"^tm-task-(\d{8})-(\d{6})$")

ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "CREATED": {"RUNNING", "FAILED"},
    "RUNNING": {"COMPLETED", "FAILED"},
    "COMPLETED": set(),
    "FAILED": set(),
}


class StorageError(Exception):
    """Raised when persisted storage data is missing, unreadable, or corrupt."""


class InvalidStatusTransitionError(ValueError):
    """Raised when a task status change violates the state machine."""


class TaskStorage:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._tasks_path = self._settings.tasks_path
        self._results_path = self._settings.results_path
        self._tasks_path.mkdir(parents=True, exist_ok=True)
        self._results_path.mkdir(parents=True, exist_ok=True)
        self._counter_path = self._tasks_path / ".counter.json"

    def _task_file(self, task_id: str) -> Path:
        return self._tasks_path / f"{task_id}.json"

    @staticmethod
    def now() -> datetime:
        return datetime.utcnow()

    @staticmethod
    def validate_status_transition(current: str, target: str) -> None:
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidStatusTransitionError(
                f"Illegal status transition: {current} -> {target}"
            )

    @staticmethod
    def _fsync_file(handle) -> None:
        handle.flush()
        os.fsync(handle.fileno())

    def _atomic_write_bytes(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            with tmp_path.open("wb") as handle:
                handle.write(content)
                self._fsync_file(handle)
            os.replace(tmp_path, path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    def _atomic_write_json(self, path: Path, data: Any) -> None:
        payload = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        self._atomic_write_bytes(path, payload.encode("utf-8"))

    def _read_json_file(self, path: Path, *, label: str) -> Any:
        if not path.exists():
            raise StorageError(f"{label} not found: {path}")
        try:
            raw = path.read_bytes()
            return json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StorageError(f"Corrupt {label}: {path}") from exc

    def _lock_file(self, handle) -> None:
        if sys.platform == "win32":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)

    def _unlock_file(self, handle) -> None:
        if sys.platform == "win32":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def generate_task_id(self, created_at: Optional[datetime] = None) -> str:
        moment = created_at or self.now()
        date_key = moment.strftime("%Y%m%d")
        counter = self._next_counter(date_key)
        return f"tm-task-{date_key}-{counter:06d}"

    def _next_counter(self, date_key: str) -> int:
        self._counter_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._counter_path.exists():
            self._atomic_write_json(self._counter_path, {})

        with self._counter_path.open("r+b") as handle:
            self._lock_file(handle)
            try:
                handle.seek(0)
                raw = handle.read()
                if raw.strip():
                    counters = json.loads(raw.decode("utf-8"))
                else:
                    counters = {}
                if not isinstance(counters, dict):
                    raise StorageError("Corrupt counter file")

                next_value = int(counters.get(date_key, 0)) + 1
                counters[date_key] = next_value
                encoded = json.dumps(counters, ensure_ascii=False, indent=2).encode("utf-8")

                handle.seek(0)
                handle.write(encoded)
                handle.truncate()
                self._fsync_file(handle)
                return next_value
            finally:
                self._unlock_file(handle)

    def plan_result_path(self, task_id: str, created_at: datetime) -> str:
        match = TASK_ID_PATTERN.match(task_id)
        if not match:
            raise ValueError(f"Invalid task_id format: {task_id}")
        date_key = match.group(1)
        year = date_key[0:4]
        month = date_key[4:6]
        day = date_key[6:8]
        return f"results/{year}/{month}/{day}/{task_id}.json"

    def result_absolute_path(self, result_path: str) -> Path:
        normalized = result_path.replace("\\", "/")
        return self._settings.data_root / normalized

    def exists(self, task_id: str) -> bool:
        return self._task_file(task_id).exists()

    def save_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        task_id = metadata["task_id"]
        path = self._task_file(task_id)
        self._atomic_write_json(path, metadata)
        return metadata

    def load_metadata(self, task_id: str) -> Optional[Dict[str, Any]]:
        path = self._task_file(task_id)
        if not path.exists():
            return None
        try:
            data = self._read_json_file(path, label="metadata")
        except StorageError:
            raise
        if not isinstance(data, dict):
            raise StorageError(f"Corrupt metadata: {path}")
        return data

    def list_tasks(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for path in sorted(self._tasks_path.glob("tm-task-*.json")):
            task_id = path.stem
            metadata = self.load_metadata(task_id)
            if metadata is not None:
                records.append(metadata)

        def sort_key(item: Dict[str, Any]) -> str:
            return item.get("created_at") or ""

        records.sort(key=sort_key)
        return records

    def transition_status(
        self,
        metadata: Dict[str, Any],
        target_status: str,
        *,
        error: Optional[str] = None,
        worker_id: Optional[str] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        current_status = metadata["status"]
        self.validate_status_transition(current_status, target_status)

        metadata["status"] = target_status
        if worker_id is not None:
            metadata["worker_id"] = worker_id
        if error is not None:
            metadata["error"] = error
        if started_at is not None:
            metadata["started_at"] = started_at.isoformat() + "Z"
        if finished_at is not None:
            metadata["finished_at"] = finished_at.isoformat() + "Z"
            started_raw = metadata.get("started_at")
            if started_raw:
                started_dt = datetime.fromisoformat(started_raw.replace("Z", ""))
                metadata["duration_ms"] = int(
                    (finished_at - started_dt).total_seconds() * 1000
                )
        return self.save_metadata(metadata)

    def save_result(self, result_path: str, result: Dict[str, Any]) -> Path:
        absolute = self.result_absolute_path(result_path)
        absolute.parent.mkdir(parents=True, exist_ok=True)
        self._atomic_write_json(absolute, result)
        return absolute

    def load_result(self, result_path: str) -> Optional[Dict[str, Any]]:
        absolute = self.result_absolute_path(result_path)
        if not absolute.exists():
            return None
        try:
            data = self._read_json_file(absolute, label="result")
        except StorageError:
            raise
        if not isinstance(data, dict):
            raise StorageError(f"Corrupt result: {absolute}")
        return data

    def result_exists(self, result_path: str) -> bool:
        return self.result_absolute_path(result_path).exists()

    def cleanup(self) -> None:
        """Reserved cleanup hook. Not implemented in V1.1."""
        return None

    def create_metadata(
        self,
        *,
        task_id: str,
        worker_type: str,
        result_path: str,
        created_at: datetime,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        metadata = {
            "task_id": task_id,
            "worker_id": None,
            "worker_type": worker_type,
            "status": "CREATED",
            "created_at": created_at.isoformat() + "Z",
            "started_at": None,
            "finished_at": None,
            "duration_ms": None,
            "result_path": result_path,
            "error": None,
            "request": request,
        }
        return self.save_metadata(metadata)

    def save(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return self.save_metadata(task)

    def load(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.load_metadata(task_id)