"""UST 10y z-cross. Same-day yield known at 21:00Z. No z_cut search."""
from __future__ import print_function

import math

from research_engine.rates import Z_CUT, Z_LOOKBACK


def _mean(xs):
    if not xs:
        return None
    return sum(xs) / float(len(xs))


def _std(xs):
    if xs is None or len(xs) < 2:
        return None
    m = _mean(xs)
    acc = 0.0
    i = 0
    while i < len(xs):
        acc += (xs[i] - m) ** 2
        i += 1
    return math.sqrt(acc / float(len(xs) - 1))


def _z(window, value):
    if value is None or window is None or len(window) < Z_LOOKBACK:
        return None
    sd = _std(window)
    if sd is None or sd == 0:
        return None
    return (value - _mean(window)) / sd


def last_known(series, bar_ts):
    last = None
    i = 0
    while i < len(series):
        kt = series[i].get("knowledge_time_utc") or ""
        if kt and kt <= bar_ts:
            last = series[i]
        else:
            if kt > bar_ts:
                break
        i += 1
    return last


def tag_features(bars, series):
    hist = []
    prev_z = None
    last_key = None
    i = 0
    while i < len(bars):
        bar = bars[i]
        row = last_known(series, bar.get("timestamp_utc") or "")
        value = None if row is None else row.get("value")
        key = None if row is None else row.get("knowledge_time_utc")
        if row is not None and key != last_key:
            if value is not None:
                hist.append(value)
            last_key = key
        bar["dgs10"] = value
        z = _z(hist[-Z_LOOKBACK:], value) if len(hist) >= Z_LOOKBACK else None
        bar["dgs10_z"] = z
        bar["is_rate_up_cross"] = bool(z is not None and z > Z_CUT and (prev_z is None or prev_z <= Z_CUT))
        bar["is_rate_down_cross"] = bool(z is not None and z < -Z_CUT and (prev_z is None or prev_z >= -Z_CUT))
        prev_z = z
        i += 1
    return bars
