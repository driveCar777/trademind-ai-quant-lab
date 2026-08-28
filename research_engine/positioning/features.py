"""COT z-cross on weekly series aligned by Friday knowledge_time. No threshold search."""
from __future__ import print_function

import math

from research_engine.positioning import Z_CUT, Z_LOOKBACK


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
    """series must be sorted by knowledge_time. Future COT cannot enter features."""
    mm_hist = []
    com_hist = []
    prev_mm_z = None
    prev_com_z = None
    last_key = None
    i = 0
    while i < len(bars):
        bar = bars[i]
        row = last_known(series, bar.get("timestamp_utc") or "")
        mm = None if row is None else row.get("mm_net_oi")
        com = None if row is None else row.get("com_net_oi")
        key = None if row is None else row.get("knowledge_time_utc")
        if row is not None and key != last_key:
            if mm is not None:
                mm_hist.append(mm)
            if com is not None:
                com_hist.append(com)
            last_key = key
        bar["mm_net_oi"] = mm
        bar["com_net_oi"] = com
        mm_z = _z(mm_hist[-Z_LOOKBACK:], mm) if len(mm_hist) >= Z_LOOKBACK else None
        com_z = _z(com_hist[-Z_LOOKBACK:], com) if len(com_hist) >= Z_LOOKBACK else None
        bar["mm_z"] = mm_z
        bar["com_z"] = com_z
        bar["is_mm_wash_cross"] = bool(
            mm_z is not None and mm_z < -Z_CUT and (prev_mm_z is None or prev_mm_z >= -Z_CUT)
        )
        bar["is_com_long_cross"] = bool(
            com_z is not None and com_z > Z_CUT and (prev_com_z is None or prev_com_z <= Z_CUT)
        )
        prev_mm_z = mm_z
        prev_com_z = com_z
        i += 1
    return bars
