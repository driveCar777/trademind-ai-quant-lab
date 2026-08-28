"""Unit tests for technical indicators."""

import time

import pytest

from app.core.indicators import (
    SUPPORTED_INDICATORS,
    calculate_ema,
    calculate_indicator,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
)

CLOSE = [
    44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
    45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00,
    46.03, 46.41, 46.22, 45.64,
]


def test_supported_indicators():
    assert SUPPORTED_INDICATORS == {"SMA", "EMA", "RSI", "MACD"}


def test_calculate_sma_returns_latest():
    result = calculate_sma(CLOSE, period=5)
    assert result["period"] == 5
    assert len(result["values"]) == len(CLOSE)
    assert result["latest"] is not None


def test_calculate_ema_returns_latest():
    result = calculate_ema(CLOSE, period=5)
    assert result["period"] == 5
    assert result["latest"] is not None


def test_calculate_rsi_returns_latest():
    result = calculate_rsi(CLOSE, period=14)
    assert result["period"] == 14
    assert result["latest"] is not None
    assert 0 <= result["latest"] <= 100


def test_calculate_macd_structure():
    extended = CLOSE * 3
    result = calculate_macd(extended)
    assert "macd" in result
    assert "signal" in result
    assert "histogram" in result
    assert result["latest"]["macd"] is not None


def test_calculate_indicator_unsupported():
    with pytest.raises(ValueError, match="Unsupported indicator"):
        calculate_indicator("BOLL", CLOSE)


def test_calculate_indicator_insufficient_data():
    with pytest.raises(ValueError, match="requires at least"):
        calculate_indicator("SMA", CLOSE[:3], params={"period": 10})


def test_calculate_indicator_empty_close():
    with pytest.raises(ValueError, match="requires at least"):
        calculate_indicator("SMA", [], params={"period": 5})


def test_calculate_indicator_invalid_period():
    with pytest.raises(ValueError, match="period must be >= 1"):
        calculate_indicator("SMA", CLOSE, params={"period": 0})


def test_calculate_sma_large_dataset_performance():
    close = [100.0 + (i % 50) * 0.1 for i in range(100_000)]
    start = time.perf_counter()
    result = calculate_sma(close, period=20)
    elapsed = time.perf_counter() - start
    assert result["latest"] is not None
    assert elapsed < 10.0
