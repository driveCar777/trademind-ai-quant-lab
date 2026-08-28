"""Global API exception handlers for TradeMind Master API v1.1."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.model.schemas import ErrorCode, api_error
from app.service.exceptions import (
    TaskFailedError,
    TaskNotFoundError,
    TaskTimeoutError,
    WorkerBusyError,
    WorkerNotFoundError,
    WorkerOfflineError,
)
from app.service.task_storage import StorageError


def _api_json_response(payload, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def register_exception_handlers(app) -> None:
    @app.exception_handler(StorageError)
    async def handle_storage_error(_: Request, exc: StorageError):
        return _api_json_response(
            api_error(ErrorCode.TASK_FAILED, str(exc)),
            status_code=500,
        )

    @app.exception_handler(TaskNotFoundError)
    async def handle_task_not_found(_: Request, exc: TaskNotFoundError):
        return _api_json_response(
            api_error(ErrorCode.TASK_FAILED, str(exc)),
            status_code=404,
        )

    @app.exception_handler(WorkerNotFoundError)
    async def handle_worker_not_found(_: Request, exc: WorkerNotFoundError):
        return _api_json_response(
            api_error(ErrorCode.WORKER_NOT_FOUND, str(exc), exc.task_data),
        )

    @app.exception_handler(WorkerOfflineError)
    async def handle_worker_offline(_: Request, exc: WorkerOfflineError):
        return _api_json_response(
            api_error(ErrorCode.WORKER_OFFLINE, str(exc), exc.task_data),
        )

    @app.exception_handler(TaskFailedError)
    async def handle_task_failed(_: Request, exc: TaskFailedError):
        return _api_json_response(
            api_error(ErrorCode.TASK_FAILED, str(exc), exc.task_data),
        )

    @app.exception_handler(TaskTimeoutError)
    async def handle_task_timeout(_: Request, exc: TaskTimeoutError):
        return _api_json_response(
            api_error(ErrorCode.TIMEOUT, str(exc), exc.task_data),
            status_code=504,
        )

    @app.exception_handler(WorkerBusyError)
    async def handle_worker_busy(_: Request, exc: WorkerBusyError):
        return _api_json_response(
            api_error(ErrorCode.WORKER_BUSY, str(exc), exc.task_data),
            status_code=429,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError):
        message = "; ".join(
            f"{'.'.join(str(part) for part in err.get('loc', []))}: {err.get('msg', 'invalid')}"
            for err in exc.errors()
        )
        return _api_json_response(
            api_error(ErrorCode.TASK_FAILED, message),
            status_code=422,
        )