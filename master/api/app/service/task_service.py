"""Task orchestration service for TradeMind Master API v1.2."""

import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from app.config.settings import Settings, get_settings
from app.model.schemas import TaskCreateData, TaskDetailData, TaskRequest, TaskStatus, WorkerInfo, WorkerStatus
from app.service.exceptions import TaskFailedError, TaskNotFoundError, TaskTimeoutError, WorkerNotFoundError, WorkerOfflineError
from app.service.task_storage import StorageError, TaskStorage
from app.service.worker_registry import WorkerRegistry


class TaskService:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        registry: Optional[WorkerRegistry] = None,
        storage: Optional[TaskStorage] = None,
    ):
        self._settings = settings or get_settings()
        self._registry = registry or WorkerRegistry(self._settings)
        self._storage = storage or TaskStorage(self._settings)

    def submit_task(self, request: TaskRequest) -> TaskCreateData:
        created_at = TaskStorage.now()
        task_id = self._storage.generate_task_id(created_at)
        result_path = self._storage.plan_result_path(task_id, created_at)
        request_payload = request.model_dump()

        # Per-request timeout override via params.timeout_seconds
        request_timeout = request.params.pop("timeout_seconds", None)

        metadata = self._storage.create_metadata(
            task_id=task_id,
            worker_type=request.worker_type,
            result_path=result_path,
            created_at=created_at,
            request=request_payload,
        )

        worker = self._resolve_worker(request.worker_type)
        if isinstance(worker, WorkerNotFoundError):
            finished_at = TaskStorage.now()
            self._storage.transition_status(
                metadata,
                TaskStatus.FAILED.value,
                error=str(worker),
                finished_at=finished_at,
            )
            task_data = TaskCreateData(task_id=task_id, status=TaskStatus.FAILED, worker_id=None)
            raise WorkerNotFoundError(request.worker_type, task_data=task_data)

        if isinstance(worker, WorkerOfflineError):
            finished_at = TaskStorage.now()
            self._storage.transition_status(
                metadata,
                TaskStatus.FAILED.value,
                error=str(worker),
                finished_at=finished_at,
            )
            task_data = TaskCreateData(task_id=task_id, status=TaskStatus.FAILED, worker_id=None)
            raise WorkerOfflineError(request.worker_type, task_data=task_data)

        started_at = TaskStorage.now()
        metadata = self._storage.transition_status(
            metadata,
            TaskStatus.RUNNING.value,
            worker_id=self._worker_id(worker),
            started_at=started_at,
        )

        payload = self._build_worker_payload(request.worker_type, request)

        try:
            result = self._call_worker(worker, payload, timeout=request_timeout)
            self._storage.save_result(result_path, result)
            finished_at = TaskStorage.now()
            metadata = self._storage.transition_status(
                metadata,
                TaskStatus.COMPLETED.value,
                finished_at=finished_at,
            )
            return TaskCreateData(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                worker_id=metadata["worker_id"],
            )
        except TaskFailedError as exc:
            finished_at = TaskStorage.now()
            metadata = self._storage.transition_status(
                metadata,
                TaskStatus.FAILED.value,
                error=str(exc),
                finished_at=finished_at,
            )
            task_data = TaskCreateData(
                task_id=task_id,
                status=TaskStatus.FAILED,
                worker_id=metadata.get("worker_id"),
            )
            exc.task_data = task_data
            raise
        except TaskTimeoutError as exc:
            finished_at = TaskStorage.now()
            metadata = self._storage.transition_status(
                metadata,
                TaskStatus.FAILED.value,
                error=str(exc),
                finished_at=finished_at,
            )
            task_data = TaskCreateData(
                task_id=task_id,
                status=TaskStatus.FAILED,
                worker_id=metadata.get("worker_id"),
            )
            exc.task_data = task_data
            raise

    def get_task(self, task_id: str) -> TaskDetailData:
        record = self._storage.load_metadata(task_id)
        if record is None:
            raise TaskNotFoundError(task_id)

        created_at = self._parse_timestamp(record["created_at"])
        completed_at = None
        if record.get("finished_at"):
            completed_at = self._parse_timestamp(record["finished_at"])

        result_path = record.get("result_path")
        result_exists = bool(result_path and self._storage.result_exists(result_path))
        result = self._load_result_body(result_path, result_exists)

        return TaskDetailData(
            task_id=record["task_id"],
            status=TaskStatus(record["status"]),
            worker_type=record["worker_type"],
            worker_id=record.get("worker_id"),
            request=record.get("request", {}),
            result_path=result_path,
            result_exists=result_exists,
            result=result,
            error=record.get("error"),
            created_at=created_at,
            completed_at=completed_at,
            duration_ms=record.get("duration_ms"),
        )

    def list_tasks(self, limit: int = 50) -> list:
        records = self._storage.list_tasks()
        tasks = []
        for record in records[-limit:]:
            created_at = self._parse_timestamp(record["created_at"])
            completed_at = None
            if record.get("finished_at"):
                completed_at = self._parse_timestamp(record["finished_at"])
            result_path = record.get("result_path")
            result_exists = bool(result_path and self._storage.result_exists(result_path))
            tasks.append(TaskDetailData(
                task_id=record["task_id"],
                status=TaskStatus(record["status"]),
                worker_type=record["worker_type"],
                worker_id=record.get("worker_id"),
                request=record.get("request", {}),
                result_path=result_path,
                result_exists=result_exists,
                error=record.get("error"),
                created_at=created_at,
                completed_at=completed_at,
                duration_ms=record.get("duration_ms"),
            ))
        return tasks

    def _load_result_body(self, result_path: Optional[str], result_exists: bool):
        """Load result JSON for GET /task/{id} only. Never raise to the route."""
        if not result_exists or not result_path:
            return None
        try:
            return self._storage.load_result(result_path)
        except StorageError:
            return None

    def _resolve_worker(self, worker_type: str):
        try:
            workers = self._registry.list_workers()
        except Exception:
            return WorkerNotFoundError(worker_type)

        matched = [worker for worker in workers if worker.worker_type == worker_type]
        if not matched:
            return WorkerNotFoundError(worker_type)

        online = [worker for worker in matched if worker.status == WorkerStatus.ONLINE]
        if not online:
            return WorkerOfflineError(worker_type)

        return online[0]

    _ENDPOINT_MAP = {
        "indicator-worker": "/api/v1/indicator/calculate",
        "stock-factor-worker": "/factor",
        "backtest-worker": "/backtest",
        "monitor-worker": "/monitor",
    }

    def _build_worker_payload(self, worker_type: str, request: "TaskRequest") -> Dict[str, Any]:
        """Translate Master task request into worker-native payload format."""
        if worker_type == "stock-factor-worker":
            return {"stock": request.data.get("stock", ""), "date": request.data.get("date", "")}
        if worker_type == "backtest-worker":
            payload = dict(request.data) if request.data else {}
            if request.params:
                payload["params"] = request.params
            return payload
        if worker_type == "monitor-worker":
            return {"type": request.data.get("type", "metrics")}
        return {"indicator": request.indicator, "data": request.data, "params": request.params}

    def _call_worker(self, worker: WorkerInfo, payload: Dict[str, Any], timeout: Optional[int] = None, retry: int = 1) -> Dict[str, Any]:
        """Call worker with retry and timeout control.

        Args:
            worker: Target worker info.
            payload: Request payload.
            timeout: Per-request timeout in seconds (overrides settings default).
            retry: Number of retries on failure (default 1 = one retry after initial failure).
        """
        endpoint = self._ENDPOINT_MAP.get(worker.worker_type, "/api/v1/indicator/calculate")
        url = f"{self._registry.worker_base_url(worker)}{endpoint}"
        effective_timeout = timeout or self._settings.worker.request_timeout_seconds

        last_exc = None
        for attempt in range(1 + retry):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=effective_timeout,
                )
                response.raise_for_status()
                return response.json()
            except requests.ConnectionError as exc:
                last_exc = exc
                if attempt < retry:
                    time.sleep(0.5)
                    continue
                raise TaskFailedError(
                    f"Connection failed to {worker.host}:{worker.port}: {exc}"
                ) from exc
            except requests.Timeout as exc:
                last_exc = exc
                if attempt < retry:
                    time.sleep(0.5)
                    continue
                raise TaskTimeoutError(
                    f"Worker {worker.id} ({worker.host}:{worker.port}) timed out after {effective_timeout}s"
                ) from exc
            except requests.RequestException as exc:
                error_message = str(exc)
                if hasattr(exc, "response") and exc.response is not None:
                    try:
                        error_message = exc.response.text or str(exc)
                    except Exception:
                        error_message = str(exc)
                last_exc = exc
                if attempt < retry:
                    time.sleep(0.5)
                    continue
                raise TaskFailedError(error_message) from exc

    @staticmethod
    def _worker_id(worker: WorkerInfo) -> str:
        return worker.id

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", ""))