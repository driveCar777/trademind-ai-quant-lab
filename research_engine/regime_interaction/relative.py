"""Relative GOLD/OIL realized-vol. Uses only bars at or before t."""
from __future__ import print_function

from research_engine.regime_interaction import RV_N, SELF_N
from research_engine.statistics import mean, stdev


def _ret(bar):
    op = bar.get("open")
    cl = bar.get("close")
    if op is None or cl is None or float(op) == 0:
        return None
    return float(cl) / float(op) - 1.0


def _roll_std(values, n):
    if len(values) < n:
        return None
    window = values[-n:]
    if any(v is None for v in window):
        return None
    return stdev(window)


def tag_relative(gold_bars, oil_bars, rv_n=RV_N, self_n=SELF_N):
    gmap = dict((b.get("timestamp_utc"), b) for b in gold_bars)
    omap = dict((b.get("timestamp_utc"), b) for b in oil_bars)
    common = [ts for ts in sorted(gmap.keys()) if ts in omap]
    g_rets = []
    o_rets = []
    g_rv_hist = []
    o_rv_hist = []
    prev_rel = None
    i = 0
    while i < len(common):
        ts = common[i]
        gb = gmap[ts]
        ob = omap[ts]
        gb["is_gold_cheap"] = False
        gb["is_oil_cheap"] = False
        gb["is_joint_vol"] = False
        ob["is_gold_cheap"] = False
        ob["is_oil_cheap"] = False
        ob["is_joint_vol"] = False
        g_rets.append(_ret(gb))
        o_rets.append(_ret(ob))
        if len(g_rets) > rv_n * 4:
            g_rets = g_rets[-rv_n:]
            o_rets = o_rets[-rv_n:]
        g_rv = _roll_std(g_rets, rv_n)
        o_rv = _roll_std(o_rets, rv_n)
        rel = None
        if g_rv and o_rv and o_rv != 0:
            rel = g_rv / float(o_rv)
        if prev_rel is not None and rel is not None:
            if prev_rel >= 1.0 and rel < 1.0:
                gb["is_gold_cheap"] = True
                ob["is_gold_cheap"] = True
            if prev_rel <= 1.0 and rel > 1.0:
                gb["is_oil_cheap"] = True
                ob["is_oil_cheap"] = True
        if g_rv is not None:
            g_rv_hist.append(g_rv)
            if len(g_rv_hist) > self_n:
                g_rv_hist = g_rv_hist[-self_n:]
        if o_rv is not None:
            o_rv_hist.append(o_rv)
            if len(o_rv_hist) > self_n:
                o_rv_hist = o_rv_hist[-self_n:]
        if g_rv is not None and o_rv is not None and len(g_rv_hist) >= self_n and len(o_rv_hist) >= self_n:
            g_mu = mean(g_rv_hist)
            o_mu = mean(o_rv_hist)
            g_sd = stdev(g_rv_hist)
            o_sd = stdev(o_rv_hist)
            if g_sd and o_sd and g_rv > g_mu + g_sd and o_rv > o_mu + o_sd:
                gb["is_joint_vol"] = True
                ob["is_joint_vol"] = True
        prev_rel = rel
        i += 1
    return gold_bars, oil_bars
