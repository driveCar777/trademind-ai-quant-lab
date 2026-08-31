"""Independent vol / eligibility / exec. Does not call V13 feature_matrix."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_strategy_v14_1 import EXCLUDE_ST, MIN_CROSS_SECTION, MIN_HISTORY_PAD, QUANTILE


def daily_return(close):
    out = np.full(close.shape, np.nan, dtype=np.float64)
    prev = close[:-1]
    cur = close[1:]
    ok = np.isfinite(prev) & np.isfinite(cur) & (prev > 0)
    out[1:] = np.where(ok, cur / prev - 1.0, np.nan)
    return out


def _vol_block(close, lookback):
    ret = daily_return(close)
    valid = np.isfinite(ret)
    x0 = np.where(valid, ret, 0.0)
    c = np.cumsum(x0, axis=0)
    c2 = np.cumsum(x0 * x0, axis=0)
    n = np.cumsum(valid.astype(np.int32), axis=0)
    s = c.copy()
    s2 = c2.copy()
    cnt = n.copy()
    s[lookback:] = c[lookback:] - c[:-lookback]
    s2[lookback:] = c2[lookback:] - c2[:-lookback]
    cnt[lookback:] = n[lookback:] - n[:-lookback]
    s[: lookback - 1] = np.nan
    var = s2 / float(lookback) - (s / float(lookback)) ** 2
    good = cnt == lookback
    return np.where(good, -np.sqrt(np.maximum(var, 0.0)), np.nan)


def vol_score(close, lookback, chunk=400):
    """Negated window std of raw close-to-close. Column chunks keep RAM down."""
    t, n = close.shape
    out = np.full((t, n), np.nan, dtype=np.float64)
    for j in range(0, n, chunk):
        block = np.array(close[:, j : j + chunk], dtype=np.float64)
        out[:, j : j + chunk] = _vol_block(block, lookback)
        print("VOL", lookback, j, "/", n, flush=True)
    return out


def eligible(pack, lookback):
    listed = np.array(pack["listed"]) == 1
    status = np.array(pack["tradestatus"]) == 1
    close = np.array(pack["close"])
    volume = np.array(pack["volume"])
    st = np.array(pack["isST"]) == 1
    hist = np.cumsum(np.isfinite(close).astype(np.int32), axis=0)
    elig = listed & status & np.isfinite(close) & (volume > 0) & (hist >= lookback + MIN_HISTORY_PAD)
    if EXCLUDE_ST:
        elig = elig & (~st)
    return elig


def _limit_col(symbol, dates):
    if symbol.startswith("bj."):
        return np.full(len(dates), 0.30, dtype=np.float64)
    if symbol.startswith("sh.688"):
        return np.full(len(dates), 0.20, dtype=np.float64)
    if symbol.startswith("sz.30"):
        return np.where(np.array(dates) >= "2020-08-24", 0.20, 0.10).astype(np.float64)
    return np.full(len(dates), 0.10, dtype=np.float64)


def exec_ok_matrix(pack, chunk=400):
    dates = pack["dates"]
    symbols = pack["symbols"]
    t, n = pack["open"].shape
    out = np.zeros((t, n), dtype=bool)
    listed = np.array(pack["listed"]) == 1
    status = np.array(pack["tradestatus"]) == 1
    st = np.array(pack["isST"]) == 1
    for j0 in range(0, n, chunk):
        j1 = min(n, j0 + chunk)
        o = np.array(pack["open"][:, j0:j1], dtype=np.float64)
        pre = np.array(pack["preclose"][:, j0:j1], dtype=np.float64)
        v = np.array(pack["volume"][:, j0:j1], dtype=np.float64)
        lim = np.stack([_limit_col(symbols[j], dates) for j in range(j0, j1)], axis=1)
        lim = np.where(st[:, j0:j1], 0.05, lim)
        move = np.abs(o / pre - 1.0)
        ok = listed[:, j0:j1] & status[:, j0:j1]
        ok = ok & np.isfinite(o) & (o > 0) & np.isfinite(pre) & (pre > 0) & np.isfinite(v) & (v > 0)
        ok = ok & (move < (lim - 0.002))
        out[:, j0:j1] = ok
        print("EXEC", j0, "/", n, flush=True)
    return out


def pick_lexsort(scores, mask):
    idx = np.where(mask & np.isfinite(scores))[0]
    if idx.size < MIN_CROSS_SECTION:
        return None
    n = int(max(1, round(idx.size * QUANTILE)))
    order = np.lexsort((idx, scores[idx]))
    return idx[order[-n:]]


def pick_argsort(scores, mask):
    idx = np.where(mask & np.isfinite(scores))[0]
    if idx.size < MIN_CROSS_SECTION:
        return None
    n = int(max(1, round(idx.size * QUANTILE)))
    order = np.argsort(scores[idx])
    return idx[order[-n:]]
