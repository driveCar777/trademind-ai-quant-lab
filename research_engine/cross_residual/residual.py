"""log(GOLD/OIL) minus SMA60. Stationarity / shock / mean-reversion diagnostics."""
from __future__ import print_function

import math

from research_engine.cross_residual import SMA_N
from research_engine.holdout import assert_role_allowed


def log_ratio(gold_close, oil_close):
    if gold_close is None or oil_close is None:
        return None
    if gold_close <= 0 or oil_close <= 0:
        return None
    return math.log(float(gold_close) / float(oil_close))


def sma(values, n, t):
    if t + 1 < n:
        return None
    acc = 0.0
    i = t - n + 1
    while i <= t:
        x = values[i]
        if x is None:
            return None
        acc += x
        i += 1
    return acc / float(n)


def build_residual(aligned_rows, sma_n=SMA_N):
    ratios = []
    i = 0
    while i < len(aligned_rows):
        row = aligned_rows[i]
        ratios.append(log_ratio(row.get("GOLD_close"), row.get("OIL_close")))
        i += 1
    out = []
    i = 0
    while i < len(aligned_rows):
        mid = sma(ratios, sma_n, i)
        resid = None
        if mid is not None and ratios[i] is not None:
            resid = ratios[i] - mid
        rec = dict(aligned_rows[i])
        rec["log_ratio"] = ratios[i]
        rec["sma"] = mid
        rec["resid"] = resid
        out.append(rec)
        i += 1
    return out


def freeze_residual_cuts(rows):
    assert_role_allowed("research")
    vals = []
    for row in rows:
        if row.get("role") != "research":
            continue
        x = row.get("resid")
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            vals.append(float(x))
    vals.sort()
    if len(vals) < 6:
        return {"p33": None, "p67": None, "n": len(vals)}
    return {
        "p33": vals[int(0.33 * (len(vals) - 1))],
        "p67": vals[int(0.67 * (len(vals) - 1))],
        "n": len(vals),
    }


def adf_like_stat(values):
    """Stdlib AR(1) residual persistence. Not a full ADF. Diagnostic only."""
    xs = [x for x in values if isinstance(x, (int, float)) and not isinstance(x, bool)]
    if len(xs) < 8:
        return None
    dy = []
    lag = []
    i = 1
    while i < len(xs):
        dy.append(xs[i] - xs[i - 1])
        lag.append(xs[i - 1])
        i += 1
    n = len(lag)
    mx = sum(lag) / float(n)
    my = sum(dy) / float(n)
    num = 0.0
    den = 0.0
    i = 0
    while i < n:
        num += (lag[i] - mx) * (dy[i] - my)
        den += (lag[i] - mx) ** 2
        i += 1
    if den == 0:
        return None
    beta = num / den
    return {"ar1_delta_beta": beta, "n": n, "mean_resid": sum(xs) / float(len(xs))}


def signal_at(row, spec, cuts):
    resid = row.get("resid")
    if resid is None or cuts.get("p33") is None or cuts.get("p67") is None:
        return 0
    kind = spec.get("kind")
    if kind == "RICH":
        return -1 if resid >= cuts["p67"] else 0
    if kind == "CHEAP":
        return 1 if resid <= cuts["p33"] else 0
    if kind == "JOINT_RISKOFF":
        g = row.get("GOLD_ret")
        o = row.get("OIL_ret")
        outer = resid <= cuts["p33"] or resid >= cuts["p67"]
        if g is None or o is None or not outer:
            return 0
        if g < 0 and o < 0:
            return -1 if resid > 0 else 1
        return 0
    return 0
