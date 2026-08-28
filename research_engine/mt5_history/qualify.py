"""Qualify a fetched bar list without changing data_layer timeframe freeze."""
from __future__ import print_function

from research_engine.mt5_history import TF_MINUTES
from data_layer.validation import validate_bars


def qualify_bars(bars, timeframe):
    if timeframe in ("M15", "H1", "H4", "D1"):
        return validate_bars(bars, timeframe)
    minutes = TF_MINUTES.get(timeframe)
    if minutes is None:
        return {"validation_status": "FAIL", "fail_reasons": ["unknown_timeframe"], "row_count": len(bars)}
    # Reuse D1 structural checks by temporarily mapping minutes via H4/D1-like path:
    # call validate_bars on a supported TF only for OHLC/dupes is wrong (gap math).
    return _lite_validate(bars, minutes)


def _lite_validate(bars, minutes):
    fail = []
    warn = []
    seen = {}
    dup = 0
    bad_ohlc = 0
    prev = None
    for bar in bars:
        ts = bar.get("timestamp_unix")
        if ts in seen:
            dup += 1
        seen[ts] = True
        o, h, l, c = bar.get("open"), bar.get("high"), bar.get("low"), bar.get("close")
        try:
            if not (h >= max(o, c) and l <= min(o, c) and h >= l and min(o, h, l, c) > 0):
                bad_ohlc += 1
        except Exception:
            bad_ohlc += 1
        if prev is not None and ts is not None and ts < prev:
            fail.append("out_of_order")
            break
        prev = ts
    if dup:
        fail.append("duplicates:%s" % dup)
    if bad_ohlc:
        fail.append("invalid_ohlc:%s" % bad_ohlc)
    if not bars:
        fail.append("empty")
    status = "FAIL" if fail else "PASS"
    if status == "PASS":
        warn.append("gap_not_interpolated")
        warn.append("weekend_holiday_kept")
    return {
        "validation_status": status,
        "fail_reasons": fail,
        "warn_reasons": warn,
        "row_count": len(bars),
        "duplicate_count": dup,
        "invalid_ohlc_count": bad_ohlc,
        "expected_seconds": minutes * 60,
        "look_ahead_guard": "broker_bar_time_as_timestamp",
    }
