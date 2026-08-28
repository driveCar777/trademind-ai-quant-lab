"""EIA production WoW and utilization z-cross. Not inventory stocks. No z_cut search."""
from __future__ import print_function

import math

from research_engine.supply import Z_CUT, Z_LOOKBACK


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


def _cross_tag(bars, series, value_key, z_key, hist_key, down_flag, up_flag, use_wow):
    hist = []
    prev_z = None
    last_key = None
    i = 0
    while i < len(bars):
        bar = bars[i]
        row = last_known(series, bar.get("timestamp_utc") or "")
        raw = None if row is None else row.get("wow" if use_wow else "value")
        key = None if row is None else row.get("knowledge_time_utc")
        if row is not None and key != last_key:
            if raw is not None:
                hist.append(raw)
            last_key = key
        bar[value_key] = None if row is None else row.get("value")
        bar[hist_key] = raw
        z = _z(hist[-Z_LOOKBACK:], raw) if len(hist) >= Z_LOOKBACK else None
        bar[z_key] = z
        if down_flag:
            bar[down_flag] = bool(
                z is not None and z < -Z_CUT and (prev_z is None or prev_z >= -Z_CUT)
            )
        if up_flag:
            bar[up_flag] = bool(
                z is not None and z > Z_CUT and (prev_z is None or prev_z <= Z_CUT)
            )
        prev_z = z
        i += 1


def tag_features(bars, packs):
    _cross_tag(
        bars,
        packs["PROD"],
        "prod",
        "prod_wow_z",
        "prod_wow",
        "is_prod_drop_cross",
        None,
        True,
    )
    _cross_tag(
        bars,
        packs["UTIL"],
        "util",
        "util_z",
        "util_level",
        None,
        "is_util_up_cross",
        False,
    )
    return bars
