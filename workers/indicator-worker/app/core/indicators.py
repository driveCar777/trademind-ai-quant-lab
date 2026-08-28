"""Technical indicator calculations using numpy/pandas."""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

SUPPORTED_INDICATORS = {"SMA", "EMA", "RSI", "MACD"}


def _as_series(values: List[float]) -> pd.Series:
    return pd.Series(values, dtype=float)


def calculate_sma(close: List[float], period: int = 14) -> Dict[str, Any]:
    series = _as_series(close)
    sma = series.rolling(window=period, min_periods=period).mean()
    return {
        "period": period,
        "values": _to_list(sma),
        "latest": _latest(sma),
    }


def calculate_ema(close: List[float], period: int = 14) -> Dict[str, Any]:
    series = _as_series(close)
    ema = series.ewm(span=period, adjust=False, min_periods=period).mean()
    return {
        "period": period,
        "values": _to_list(ema),
        "latest": _latest(ema),
    }


def calculate_rsi(close: List[float], period: int = 14) -> Dict[str, Any]:
    series = _as_series(close)
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return {
        "period": period,
        "values": _to_list(rsi),
        "latest": _latest(rsi),
    }


def calculate_macd(
    close: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Dict[str, Any]:
    series = _as_series(close)
    ema_fast = series.ewm(span=fast_period, adjust=False, min_periods=fast_period).mean()
    ema_slow = series.ewm(span=slow_period, adjust=False, min_periods=slow_period).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False, min_periods=signal_period).mean()
    histogram = macd_line - signal_line
    return {
        "fast_period": fast_period,
        "slow_period": slow_period,
        "signal_period": signal_period,
        "macd": _to_list(macd_line),
        "signal": _to_list(signal_line),
        "histogram": _to_list(histogram),
        "latest": {
            "macd": _latest(macd_line),
            "signal": _latest(signal_line),
            "histogram": _latest(histogram),
        },
    }


def calculate_indicator(
    indicator: str,
    close: List[float],
    high: Optional[List[float]] = None,
    low: Optional[List[float]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    params = params or {}
    name = indicator.upper()
    if name not in SUPPORTED_INDICATORS:
        raise ValueError(f"Unsupported indicator: {indicator}. Supported: {sorted(SUPPORTED_INDICATORS)}")

    if name == "SMA":
        period = int(params.get("period", 14))
        if period < 1:
            raise ValueError("period must be >= 1")
        if len(close) < period:
            raise ValueError(f"SMA requires at least {period} data points")
        return calculate_sma(close, period)

    if name == "EMA":
        period = int(params.get("period", 14))
        if period < 1:
            raise ValueError("period must be >= 1")
        if len(close) < period:
            raise ValueError(f"EMA requires at least {period} data points")
        return calculate_ema(close, period)

    if name == "RSI":
        period = int(params.get("period", 14))
        if period < 1:
            raise ValueError("period must be >= 1")
        if len(close) < period + 1:
            raise ValueError(f"RSI requires at least {period + 1} data points")
        return calculate_rsi(close, period)

    if name == "MACD":
        fast_period = int(params.get("fast_period", 12))
        slow_period = int(params.get("slow_period", 26))
        signal_period = int(params.get("signal_period", 9))
        min_points = max(slow_period, fast_period) + signal_period
        if len(close) < min_points:
            raise ValueError(f"MACD requires at least {min_points} data points")
        return calculate_macd(close, fast_period, slow_period, signal_period)

    raise ValueError(f"Unsupported indicator: {indicator}")


def _to_list(series: pd.Series) -> List[Optional[float]]:
    return [None if pd.isna(value) else float(value) for value in series.tolist()]


def _latest(series: pd.Series) -> Optional[float]:
    if series.empty:
        return None
    value = series.iloc[-1]
    if pd.isna(value):
        return None
    return float(value)
