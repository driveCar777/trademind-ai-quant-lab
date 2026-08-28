"""EIA inventory WoW z-cross. Friday week-ending, Wednesday knowledge. No z_cut search."""
from __future__ import print_function

import math

from research_engine.inventory import Z_CUT, Z_LOOKBACK


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
    wow_hist = []
    prev_z = None
    last_key = None
    i = 0
    while i < len(bars):
        bar = bars[i]
        row = last_known(series, bar.get("timestamp_utc") or "")
        wow = None if row is None else row.get("wow")
        key = None if row is None else row.get("knowledge_time_utc")
        if row is not None and key != last_key:
            if wow is not None:
                wow_hist.append(wow)
            last_key = key
        bar["inv"] = None if row is None else row.get("value")
        bar["inv_wow"] = wow
        z = _z(wow_hist[-Z_LOOKBACK:], wow) if len(wow_hist) >= Z_LOOKBACK else None
        bar["inv_wow_z"] = z
        bar["is_inv_draw_cross"] = bool(z is not None and z < -Z_CUT and (prev_z is None or prev_z >= -Z_CUT))
        bar["is_inv_build_cross"] = bool(z is not None and z > Z_CUT and (prev_z is None or prev_z <= Z_CUT))
        prev_z = z
        i += 1
    return bars
