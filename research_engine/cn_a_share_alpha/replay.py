"""Quintile books. Signal close(t), fill open(t+1). No pretend fills."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_alpha import HOLD_DAYS, MIN_CROSS_SECTION, QUANTILE, SEED
from research_engine.cn_a_share_alpha.cost import round_trip_cost
from research_engine.cn_a_share_alpha.features import eligible_mask, exec_ok, feature_matrix, naive_1d_score


def _pick(scores, mask, top=True):
    idx = np.where(mask & np.isfinite(scores))[0]
    if idx.size < MIN_CROSS_SECTION:
        return None
    vals = scores[idx]
    order = np.argsort(vals)
    n = int(max(1, round(idx.size * QUANTILE)))
    chosen = order[-n:] if top else order[:n]
    return idx[chosen]


def _h_return(pack, js, t_signal):
    """Mean open(t+1) -> open(t+1+H) among executable names."""
    t0 = t_signal + 1
    t1 = t_signal + 1 + HOLD_DAYS
    dates = pack["dates"]
    if t1 >= len(dates):
        return None, 0, 0
    filled = []
    skipped = 0
    for j in js:
        if not exec_ok(pack, t0, j) or not exec_ok(pack, t1, j):
            skipped += 1
            continue
        a = float(pack["open"][t0, j])
        b = float(pack["open"][t1, j])
        filled.append(b / a - 1.0)
    if not filled:
        return None, 0, skipped
    return float(np.mean(filled)), len(filled), skipped


def _adv(pack, js, t_signal):
    t0 = t_signal + 1
    vals = []
    for j in js:
        amt = float(pack["amount"][t0, j]) if t0 < len(pack["dates"]) else np.nan
        if np.isfinite(amt) and amt > 0:
            vals.append(amt)
    if not vals:
        return None
    return float(np.median(vals))


def day_book(pack, scores, elig, t, top=True):
    js = _pick(scores[t], elig[t], top=top)
    if js is None:
        return None
    ret, n_fill, n_skip = _h_return(pack, js, t)
    if ret is None:
        return None
    entry = pack["dates"][t + 1]
    exit_d = pack["dates"][t + 1 + HOLD_DAYS]
    cost = round_trip_cost(entry, exit_d)
    return {
        "n_fill": n_fill,
        "n_skip": n_skip,
        "raw": ret,
        "cost": cost,
        "net": ret - cost,
        "adv": _adv(pack, js, t),
        "n_names": int(js.size),
    }


def overlapping_series(pack, family, lookback, start, end, top=True, scores=None, elig=None):
    if scores is None:
        scores = feature_matrix(pack, family, lookback)
    if elig is None:
        elig = eligible_mask(pack, lookback)
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    rows = []
    for t in range(i0, i1 + 1):
        if t + 1 + HOLD_DAYS >= len(dates):
            break
        rec = day_book(pack, scores, elig, t, top=top)
        if rec is None:
            continue
        rec["date"] = dates[t]
        rec["entry"] = dates[t + 1]
        rec["exit"] = dates[t + 1 + HOLD_DAYS]
        rows.append(rec)
    return rows


def ew_market_series(pack, start, end, lookback=20):
    """B0: equal-weight all eligible executable names, same H-day open-to-open."""
    dates = pack["dates"]
    elig = eligible_mask(pack, lookback)
    i0 = dates.index(start)
    i1 = dates.index(end)
    rows = []
    for t in range(i0, i1 + 1):
        if t + 1 + HOLD_DAYS >= len(dates):
            break
        js = np.where(elig[t])[0]
        if js.size < MIN_CROSS_SECTION:
            continue
        ret, n_fill, n_skip = _h_return(pack, js, t)
        if ret is None:
            continue
        entry = dates[t + 1]
        exit_d = dates[t + 1 + HOLD_DAYS]
        cost = round_trip_cost(entry, exit_d)
        rows.append({"date": dates[t], "raw": ret, "net": ret - cost, "cost": cost, "n_fill": n_fill})
    return rows


def random_quintile_series(pack, start, end, lookback=20, seed=SEED):
    elig = eligible_mask(pack, lookback)
    rng = np.random.RandomState(seed)
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    rows = []
    for t in range(i0, i1 + 1):
        if t + 1 + HOLD_DAYS >= len(dates):
            break
        idx = np.where(elig[t])[0]
        if idx.size < MIN_CROSS_SECTION:
            continue
        n = int(max(1, round(idx.size * QUANTILE)))
        js = rng.choice(idx, size=n, replace=False)
        ret, n_fill, n_skip = _h_return(pack, js, t)
        if ret is None:
            continue
        entry = dates[t + 1]
        exit_d = dates[t + 1 + HOLD_DAYS]
        cost = round_trip_cost(entry, exit_d)
        rows.append({"date": dates[t], "raw": ret, "net": ret - cost, "cost": cost, "n_fill": n_fill})
    return rows


def naive_1d_series(pack, start, end):
    scores = naive_1d_score(pack)
    elig = eligible_mask(pack, 20)
    return overlapping_series(pack, "CROSS_SECTIONAL_MOMENTUM", 20, start, end, top=True, scores=scores, elig=elig)


def nonoverlap_equity(pack, family, lookback, start, end, top=True):
    scores = feature_matrix(pack, family, lookback)
    elig = eligible_mask(pack, lookback)
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    equity = 1.0
    curve = [{"date": start, "equity": 1.0}]
    trades = []
    t = i0
    while t <= i1:
        if t + 1 + HOLD_DAYS >= len(dates):
            break
        rec = day_book(pack, scores, elig, t, top=top)
        if rec is None:
            t += 1
            continue
        equity *= 1.0 + rec["net"]
        curve.append({"date": rec["exit"] if False else dates[t + 1 + HOLD_DAYS], "equity": equity})
        trades.append(
            {
                "signal_date": dates[t],
                "entry": dates[t + 1],
                "exit": dates[t + 1 + HOLD_DAYS],
                "n_fill": rec["n_fill"],
                "n_skip": rec["n_skip"],
                "raw": rec["raw"],
                "cost": rec["cost"],
                "net": rec["net"],
                "adv": rec["adv"],
            }
        )
        t += HOLD_DAYS
    return curve, trades
