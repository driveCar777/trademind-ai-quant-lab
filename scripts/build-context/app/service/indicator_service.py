"""Indicator calculation service layer."""

import time
import uuid
from datetime import datetime

from app.core import indicators, worker_state
from app.model.schemas import IndicatorRequest, IndicatorResponse


def process_indicator_request(request: IndicatorRequest) -> IndicatorResponse:
    with worker_state.task_slot():
        start = time.perf_counter()
        result = indicators.calculate_indicator(
            indicator=request.indicator.upper(),
            close=request.data.close,
            high=request.data.high or None,
            low=request.data.low or None,
            params=request.params,
        )
        duration_ms = (time.perf_counter() - start) * 1000

    return IndicatorResponse(
        request_id=str(uuid.uuid4()),
        indicator=request.indicator.upper(),
        symbol=request.data.symbol,
        timeframe=request.data.timeframe,
        result=result,
        calculation_time_ms=round(duration_ms, 3),
        timestamp=datetime.utcnow(),
    )


def list_supported_indicators():
    return sorted(indicators.SUPPORTED_INDICATORS)
