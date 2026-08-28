"""Progressive history probe. Do not request a crash-sized dump."""
from __future__ import print_function

import time
from datetime import datetime, timezone

from research_engine.mt5_history import PROBE_STEPS, TF_ATTR


def tf_const(mt5, timeframe):
    attr = TF_ATTR.get(timeframe)
    if not attr or not hasattr(mt5, attr):
        return None
    return getattr(mt5, attr)


def unix_utc(unix):
    if unix is None:
        return None
    return datetime.fromtimestamp(int(unix), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def years_span(first_unix, last_unix):
    if not first_unix or not last_unix or last_unix <= first_unix:
        return 0.0
    return (float(last_unix) - float(first_unix)) / (365.25 * 24 * 3600)


def probe_from_pos(mt5, symbol, timeframe, max_count, sleep_s=0.12):
    const = tf_const(mt5, timeframe)
    if const is None:
        return {"status": "NOT_AVAILABLE", "reason": "timeframe_const", "timeframe": timeframe}
    last = None
    for step in PROBE_STEPS:
        if step > int(max_count):
            break
        rates = mt5.copy_rates_from_pos(symbol, const, 0, int(step))
        if rates is None:
            err = None
            try:
                err = mt5.last_error()
            except Exception:
                err = None
            return {
                "status": "NOT_AVAILABLE",
                "reason": "copy_rates_from_pos_none",
                "last_error": str(err),
                "timeframe": timeframe,
                "requested": step,
            }
        n = len(rates)
        first_unix = int(rates[0]["time"])
        last_unix = int(rates[-1]["time"])
        last = {
            "status": "OK",
            "method": "copy_rates_from_pos",
            "requested": step,
            "bar_count": n,
            "first_bar": unix_utc(first_unix),
            "last_bar": unix_utc(last_unix),
            "first_unix": first_unix,
            "last_unix": last_unix,
            "calendar_span": years_span(first_unix, last_unix),
            "hit_ceiling": n < int(step * 0.98),
            "timeframe": timeframe,
            "symbol": symbol,
        }
        if last["hit_ceiling"]:
            return last
        time.sleep(sleep_s)
    return last or {"status": "NOT_AVAILABLE", "reason": "empty", "timeframe": timeframe}


def probe_range(mt5, symbol, timeframe, start, end):
    const = tf_const(mt5, timeframe)
    if const is None:
        return {"status": "NOT_AVAILABLE", "reason": "timeframe_const", "timeframe": timeframe}
    rates = mt5.copy_rates_range(symbol, const, start, end)
    if rates is None:
        err = None
        try:
            err = mt5.last_error()
        except Exception:
            err = None
        return {
            "status": "NOT_AVAILABLE",
            "reason": "copy_rates_range_none",
            "last_error": str(err),
            "timeframe": timeframe,
        }
    n = len(rates)
    if n == 0:
        return {"status": "NOT_AVAILABLE", "reason": "empty_range", "timeframe": timeframe, "bar_count": 0}
    first_unix = int(rates[0]["time"])
    last_unix = int(rates[-1]["time"])
    return {
        "status": "OK",
        "method": "copy_rates_range",
        "bar_count": n,
        "first_bar": unix_utc(first_unix),
        "last_bar": unix_utc(last_unix),
        "first_unix": first_unix,
        "last_unix": last_unix,
        "calendar_span": years_span(first_unix, last_unix),
        "timeframe": timeframe,
        "symbol": symbol,
    }


def merge_best(pos_row, range_row):
    candidates = [row for row in (pos_row, range_row) if row and row.get("status") == "OK"]
    if not candidates:
        return pos_row or range_row
    best = candidates[0]
    for row in candidates[1:]:
        if float(row.get("calendar_span") or 0) > float(best.get("calendar_span") or 0):
            best = row
        elif float(row.get("calendar_span") or 0) == float(best.get("calendar_span") or 0):
            if int(row.get("bar_count") or 0) > int(best.get("bar_count") or 0):
                best = row
    best = dict(best)
    best["pos_count"] = (pos_row or {}).get("bar_count")
    best["range_count"] = (range_row or {}).get("bar_count")
    best["methods"] = [row.get("method") for row in candidates]
    return best
