"""252-day z of log(GOLD/SILVER). No z_cut search. Not SMA60."""
from __future__ import print_function

import math

from research_engine.cross_metal import Z_CUT, Z_LOOKBACK


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


def _date_of(bar):
    return bar.get("date") or (bar.get("timestamp_utc") or "")[:10]


def _closes(bars):
    out = {}
    i = 0
    while i < len(bars):
        d = _date_of(bars[i])
        px = bars[i].get("close")
        if d and px is not None and px > 0:
            out[d] = px
        i += 1
    return out


def ratio_events(gold_bars, silver_bars):
    gmap = _closes(gold_bars)
    smap = _closes(silver_bars)
    dates = sorted(set(gmap.keys()) & set(smap.keys()))
    hist = []
    prev_z = None
    by_date = {}
    i = 0
    while i < len(dates):
        d = dates[i]
        ratio = math.log(gmap[d] / smap[d])
        hist.append(ratio)
        z = _z(hist[-Z_LOOKBACK:], ratio) if len(hist) >= Z_LOOKBACK else None
        rich = bool(z is not None and z > Z_CUT and (prev_z is None or prev_z <= Z_CUT))
        cheap = bool(z is not None and z < -Z_CUT and (prev_z is None or prev_z >= -Z_CUT))
        by_date[d] = {"gs_ratio": ratio, "gs_ratio_z": z, "is_ratio_rich_cross": rich, "is_ratio_cheap_cross": cheap}
        prev_z = z
        i += 1
    return by_date


def tag_bars(bars, by_date):
    i = 0
    while i < len(bars):
        bar = bars[i]
        row = by_date.get(_date_of(bar))
        if row is None:
            bar["gs_ratio"] = None
            bar["gs_ratio_z"] = None
            bar["is_ratio_rich_cross"] = False
            bar["is_ratio_cheap_cross"] = False
        else:
            bar["gs_ratio"] = row["gs_ratio"]
            bar["gs_ratio_z"] = row["gs_ratio_z"]
            bar["is_ratio_rich_cross"] = row["is_ratio_rich_cross"]
            bar["is_ratio_cheap_cross"] = row["is_ratio_cheap_cross"]
        i += 1
    return bars
