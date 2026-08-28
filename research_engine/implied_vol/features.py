"""IV z-cross and VRP-rich cross. Lookbacks frozen. No threshold search."""
from __future__ import print_function

import math

from research_engine.implied_vol import RV_LOOKBACK, VRP_SD_LOOKBACK, VRP_SD_MULT, Z_CUT, Z_LOOKBACK


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


def realized_vol_points(closes):
    if closes is None or len(closes) < (RV_LOOKBACK + 1):
        return None
    rets = []
    i = 1
    while i < len(closes):
        prev = closes[i - 1]
        cur = closes[i]
        if prev is None or cur is None or prev <= 0 or cur <= 0:
            return None
        rets.append(math.log(cur / prev))
        i += 1
    if len(rets) < RV_LOOKBACK:
        return None
    sd = _std(rets)
    if sd is None:
        return None
    return sd * math.sqrt(252.0) * 100.0


def tag_features(bars, iv_by_date):
    """Attach last known IV with date <= bar date. Features ignore future IV."""
    iv_hist = []
    vrp_hist = []
    prev_z = None
    prev_vrp_stat = None
    i = 0
    while i < len(bars):
        bar = bars[i]
        day = bar.get("date")
        iv = iv_by_date.get(day)
        if iv is None:
            # last known on or before day
            j = i
            while j >= 0:
                prior = bars[j].get("date")
                if prior in iv_by_date:
                    iv = iv_by_date[prior]
                    break
                j -= 1
        bar["iv"] = iv
        if iv is not None:
            iv_hist.append(iv)
        window = iv_hist[-Z_LOOKBACK:] if len(iv_hist) >= Z_LOOKBACK else None
        z = _z(window, iv) if window is not None else None
        bar["iv_z"] = z
        bar["is_iv_z_cross"] = bool(z is not None and z > Z_CUT and (prev_z is None or prev_z <= Z_CUT))
        closes = []
        start = i - (RV_LOOKBACK + 1)
        k = start
        while k < i:
            if k >= 0:
                closes.append(bars[k].get("close"))
            k += 1
        rv = realized_vol_points(closes) if len(closes) == (RV_LOOKBACK + 1) else None
        vrp = None
        if iv is not None and rv is not None:
            vrp = iv - rv
            vrp_hist.append(vrp)
        bar["rv20"] = rv
        bar["vrp"] = vrp
        rich = False
        if vrp is not None and len(vrp_hist) >= VRP_SD_LOOKBACK:
            trail = vrp_hist[-VRP_SD_LOOKBACK:]
            sd = _std(trail)
            mu = _mean(trail)
            if sd and mu is not None:
                stat = (vrp - mu) / sd
                rich = stat > VRP_SD_MULT and (prev_vrp_stat is None or prev_vrp_stat <= VRP_SD_MULT)
                prev_vrp_stat = stat
            else:
                prev_vrp_stat = None
        else:
            prev_vrp_stat = None
        bar["is_vrp_rich_cross"] = rich
        prev_z = z
        i += 1
    return bars
