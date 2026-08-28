from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator


class MarketData(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=32)
    timeframe: str = Field(default="M15", max_length=16)
    open: List[float] = Field(default_factory=list)
    high: List[float] = Field(default_factory=list)
    low: List[float] = Field(default_factory=list)
    close: List[float] = Field(..., min_items=1)
    volume: Optional[List[float]] = None
    timestamp: Optional[List[int]] = None

    @root_validator
    def validate_series(cls, values):
        series = {
            "open": values.get("open") or [],
            "high": values.get("high") or [],
            "low": values.get("low") or [],
            "close": values.get("close") or [],
        }
        lengths = {name: len(items) for name, items in series.items() if items}
        if lengths and len(set(lengths.values())) > 1:
            raise ValueError("All provided price series must have the same length")
        return values


class IndicatorRequest(BaseModel):
    indicator: str = Field(..., min_length=2, max_length=16)
    data: MarketData
    params: Dict[str, Any] = Field(default_factory=dict)


class IndicatorResponse(BaseModel):
    success: bool = True
    request_id: str
    indicator: str
    symbol: str
    timeframe: str
    result: Dict[str, Any]
    calculation_time_ms: float
    timestamp: datetime


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    worker_id: str
    uptime_seconds: float
    timestamp: datetime


class ReadyResponse(BaseModel):
    status: str
    worker: str
    queue: int


class VersionResponse(BaseModel):
    name: str
    version: str
    build: str
    python: str
    platform: str
