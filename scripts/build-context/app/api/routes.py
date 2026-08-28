"""FastAPI route definitions."""

from datetime import datetime
import platform
import sys

from fastapi import APIRouter, HTTPException

from app.config.settings import get_settings
from app.core import worker_state
from app.model.schemas import (
    HealthResponse,
    IndicatorRequest,
    IndicatorResponse,
    ReadyResponse,
    VersionResponse,
)
from app.service.indicator_service import list_supported_indicators, process_indicator_request

router = APIRouter()
_start_time = datetime.utcnow()


@router.get("/health", response_model=HealthResponse)
def health_check():
    settings = get_settings()
    now = datetime.utcnow()
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.version,
        worker_id=settings.worker_id,
        uptime_seconds=round((now - _start_time).total_seconds(), 3),
        timestamp=now,
    )


@router.get("/ready", response_model=ReadyResponse)
def readiness_check():
    settings = get_settings()
    if not worker_state.is_ready():
        raise HTTPException(status_code=503, detail="Worker is not ready")
    return ReadyResponse(
        status="ready",
        worker=settings.worker_id,
        queue=worker_state.queue_size(),
    )


@router.get("/version", response_model=VersionResponse)
def version_info():
    settings = get_settings()
    return VersionResponse(
        name=settings.service_name,
        version=settings.version,
        build=settings.build,
        python=f"{sys.version_info.major}.{sys.version_info.minor}",
        platform=platform.machine(),
    )


@router.get("/indicators")
def get_supported_indicators():
    return {"indicators": list_supported_indicators()}


@router.post("/api/v1/indicator/calculate", response_model=IndicatorResponse)
def calculate_indicator(request: IndicatorRequest):
    if not worker_state.is_ready():
        raise HTTPException(status_code=503, detail="Worker is not ready")
    try:
        return process_indicator_request(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Indicator calculation failed") from exc
