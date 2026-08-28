"""Same-hour tick_volume surprise. Baseline uses only earlier bars."""
from __future__ import print_function

from research_engine.statistics import mean, stdev
from research_engine.microstructure_surprise import LOOKBACK, Z_CUT


def _hour(ts):
    if not ts or len(ts) < 13:
        return None
    try:
        return int(ts[11:13])
    except Exception:
        return None


def _abs_ret(bar):
    op = bar.get("open")
    cl = bar.get("close")
    if op is None or cl is None or float(op) == 0:
        return 0.0
    return abs(float(cl) / float(op) - 1.0)


def tag_surprise(bars, lookback=LOOKBACK, z_cut=Z_CUT):
    buckets = {}
    i = 0
    while i < 24:
        buckets[i] = []
        i += 1
    i = 0
    while i < len(bars):
        bar = bars[i]
        bar["vol_z"] = None
        bar["is_vol_surprise"] = False
        bar["is_vol_div"] = False
        hour = _hour(bar.get("timestamp_utc") or "")
        tv = bar.get("tick_volume")
        if hour is None or tv is None:
            i += 1
            continue
        hist = buckets[hour]
        if len(hist) >= lookback:
            tvs = [row[0] for row in hist[-lookback:]]
            rets = [row[1] for row in hist[-lookback:]]
            mu = mean(tvs)
            sd = stdev(tvs)
            z = 0.0 if (sd is None or sd == 0) else (float(tv) - mu) / float(sd)
            bar["vol_z"] = z
            if z > z_cut:
                bar["is_vol_surprise"] = True
                mr = mean(rets)
                if mr and _abs_ret(bar) < 0.5 * mr:
                    bar["is_vol_div"] = True
        hist.append((float(tv), _abs_ret(bar)))
        i += 1
    return bars
