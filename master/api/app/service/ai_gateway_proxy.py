"""REST proxy from Master API to the standalone AI Gateway process."""

from typing import Any, Dict, Optional

import requests
from fastapi.responses import JSONResponse

from app.config.settings import Settings, get_settings
from app.model.schemas import ErrorCode


class AIGatewayProxy:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()

    @property
    def base_url(self) -> str:
        return self._settings.ai_gateway.url.rstrip("/")

    @property
    def timeout(self) -> int:
        return int(self._settings.ai_gateway.timeout_seconds)

    def forward(self, method: str, path: str, json_body: Optional[Dict[str, Any]] = None) -> JSONResponse:
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(
                method=method,
                url=url,
                json=json_body,
                timeout=self.timeout,
            )
        except requests.Timeout:
            return _error(504, ErrorCode.TIMEOUT, "AI Gateway timeout")
        except requests.ConnectionError:
            return _error(503, ErrorCode.WORKER_OFFLINE, "AI Gateway offline")
        except requests.RequestException as exc:
            return _error(502, ErrorCode.TASK_FAILED, f"AI Gateway request failed: {exc}")

        try:
            payload = response.json()
        except ValueError:
            return _error(502, ErrorCode.TASK_FAILED, "AI Gateway invalid response")

        if not isinstance(payload, dict):
            return _error(502, ErrorCode.TASK_FAILED, "AI Gateway invalid response")
        return JSONResponse(status_code=response.status_code, content=payload)


def _error(status_code: int, code: ErrorCode, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "code": code.value,
            "data": None,
        },
    )
