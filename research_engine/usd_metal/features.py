"""252-day z of DXY close. No z_cut search. Not FX pair return."""
from __future__ import print_function

import math

from research_engine.usd_metal import Z_CUT, Z_LOOKBACK


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


def dxy_events(dxy_bars):
    hist = []
    prev_z = None
    series = []
    i = 0
    while i < len(dxy_bars):
        bar = dxy_bars[i]
        px = bar.get("close")
        d = _date_of(bar)
        if px is None or px <= 0 or not d:
            i += 1
            continue
        hist.append(px)
        z = _z(hist[-Z_LOOKBACK:], px) if len(hist) >= Z_LOOKBACK else None
        up = bool(z is not None and z > Z_CUT and (prev_z is None or prev_z <= Z_CUT))
        down = bool(z is not None and z < -Z_CUT and (prev_z is None or prev_z >= -Z_CUT))
        series.append(
            {
                "date": d,
                "dxy": px,
                "dxy_z": z,
                "is_dxy_up_cross": up,
                "is_dxy_down_cross": down,
            }
        )
        prev_z = z
        i += 1
    return series


def last_known(series, bar_date):
    last = None
    i = 0
    while i < len(series):
        d = series[i].get("date") or ""
        if d and d <= bar_date:
            last = series[i]
        else:
            if d > bar_date:
                break
        i += 1
    return last


def tag_bars(bars, series):
    i = 0
    while i < len(bars):
        bar = bars[i]
        row = last_known(series, _date_of(bar))
        if row is None:
            bar["dxy"] = None
            bar["dxy_z"] = None
            bar["is_dxy_up_cross"] = False
            bar["is_dxy_down_cross"] = False
        else:
            bar["dxy"] = row["dxy"]
            bar["dxy_z"] = row["dxy_z"]
            bar["is_dxy_up_cross"] = row["is_dxy_up_cross"]
            bar["is_dxy_down_cross"] = row["is_dxy_down_cross"]
        i += 1
    return bars
