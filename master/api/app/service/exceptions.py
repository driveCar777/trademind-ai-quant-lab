"""Business exceptions for TradeMind Master API v1.1."""

from typing import Optional

from app.model.schemas import TaskCreateData


class TaskNotFoundError(Exception):
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Task '{task_id}' not found")


class WorkerNotFoundError(Exception):
    def __init__(self, worker_type: str, task_data: Optional[TaskCreateData] = None):
        self.worker_type = worker_type
        self.task_data = task_data
        super().__init__(f"No worker registered for type '{worker_type}'")


class WorkerOfflineError(Exception):
    def __init__(self, worker_type: str, task_data: Optional[TaskCreateData] = None):
        self.worker_type = worker_type
        self.task_data = task_data
        super().__init__(f"Worker for type '{worker_type}' is offline")


class TaskFailedError(Exception):
    def __init__(self, message: str, task_data: Optional[TaskCreateData] = None):
        self.task_data = task_data
        super().__init__(message)


class TaskTimeoutError(Exception):
    def __init__(self, message: str = "Worker request timed out", task_data: Optional[TaskCreateData] = None):
        self.task_data = task_data
        super().__init__(message)


class WorkerBusyError(Exception):
    def __init__(self, worker_type: str, task_data: Optional[TaskCreateData] = None):
        self.worker_type = worker_type
        self.task_data = task_data
        super().__init__(f"Worker for type '{worker_type}' is busy")