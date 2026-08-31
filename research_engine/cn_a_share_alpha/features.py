"""Causal cross-sectional features. t uses only data through close(t)."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_alpha import EXCLUDE_ST, MIN_HISTORY_PAD, MIN_CROSS_SECTION
from research_engine.cn_a_share_alpha.pack import limit_pct_for


def _rolling_sum(x, w):
    valid = np.isfinite(x)
    x0 = np.where(valid, x, 0.0)
    c = np.cumsum(x0, axis=0)
    n = np.cumsum(valid.astype(np.int32), axis=0)
    s = c.copy()
    cnt = n.copy()
    s[w:] = c[w:] - c[:-w]
    cnt[w:] = n[w:] - n[:-w]
    s[: w - 1] = np.nan
    cnt[: w - 1] = 0
    return s, cnt


def daily_return(close):
    out = np.full(close.shape, np.nan, dtype=np.float64)
    prev = close[:-1]
    cur = close[1:]
    good = np.isfinite(prev) & np.isfinite(cur) & (prev > 0)
    out[1:] = np.where(good, cur / prev - 1.0, np.nan)
    return out


def feature_matrix(pack, family, lookback):
    close = np.array(pack["close"], dtype=np.float64, copy=False)
    turn = np.array(pack["turn"], dtype=np.float64, copy=False)
    ret = daily_return(close)
    if family in ("CROSS_SECTIONAL_MOMENTUM", "CROSS_SECTIONAL_REVERSAL"):
        s, cnt = _rolling_sum(ret, lookback)
        score = np.where(cnt == lookback, s, np.nan)
        if family == "CROSS_SECTIONAL_REVERSAL":
            score = -score
        return score
    if family == "CROSS_SECTIONAL_ACTIVITY":
        s, cnt = _rolling_sum(turn, lookback)
        mean = np.where(cnt == lookback, s / float(lookback), np.nan)
        return -mean
    if family == "CROSS_SECTIONAL_VOLATILITY":
        s, cnt = _rolling_sum(ret, lookback)
        s2, cnt2 = _rolling_sum(ret * ret, lookback)
        var = np.where(
            (cnt == lookback) & (cnt2 == lookback),
            s2 / float(lookback) - (s / float(lookback)) ** 2,
            np.nan,
        )
        vol = np.sqrt(np.maximum(var, 0.0))
        return -vol
    raise ValueError(family)


def naive_1d_score(pack):
    close = np.array(pack["close"], dtype=np.float64, copy=False)
    return daily_return(close)


def eligible_mask(pack, lookback):
    dates = pack["dates"]
    symbols = pack["symbols"]
    listed = np.array(pack["listed"])
    st = np.array(pack["isST"])
    status = np.array(pack["tradestatus"])
    close = np.array(pack["close"])
    vol = np.array(pack["volume"])
    t, n = close.shape
    hist = np.isfinite(close).astype(np.int32)
    hist = np.cumsum(hist, axis=0)
    need = lookback + MIN_HISTORY_PAD
    elig = (
        (listed == 1)
        & (status == 1)
        & np.isfinite(close)
        & (vol > 0)
        & (hist >= need)
    )
    if EXCLUDE_ST:
        elig = elig & (st == 0)
    return elig


def exec_mask(pack):
    """True where open is an executable fill. Built once."""
    dates = pack["dates"]
    symbols = pack["symbols"]
    listed = np.array(pack["listed"]) == 1
    status = np.array(pack["tradestatus"]) == 1
    o = np.array(pack["open"], dtype=np.float64)
    pre = np.array(pack["preclose"], dtype=np.float64)
    v = np.array(pack["volume"], dtype=np.float64)
    st = np.array(pack["isST"]) == 1
    lim = np.full(o.shape, 0.10, dtype=np.float64)
    day_arr = np.array(dates)
    chi_20 = day_arr >= "2020-08-24"
    for j, symbol in enumerate(symbols):
        if symbol.startswith("bj."):
            lim[:, j] = 0.30
        elif symbol.startswith("sh.688"):
            lim[:, j] = 0.20
        elif symbol.startswith("sz.30"):
            lim[:, j] = np.where(chi_20, 0.20, 0.10)
    lim = np.where(st, 0.05, lim)
    move = np.abs(o / pre - 1.0)
    ok = listed & status & np.isfinite(o) & (o > 0) & np.isfinite(pre) & (pre > 0) & np.isfinite(v) & (v > 0)
    ok = ok & (move < (lim - 0.002))
    return ok


def exec_ok(pack, t, j, mask=None):
    if mask is None:
        o = float(pack["open"][t, j])
        pre = float(pack["preclose"][t, j])
        v = float(pack["volume"][t, j])
        if int(pack["listed"][t, j]) != 1 or int(pack["tradestatus"][t, j]) != 1:
            return False
        if not np.isfinite(o) or o <= 0 or not np.isfinite(pre) or pre <= 0 or not np.isfinite(v) or v <= 0:
            return False
        st = int(pack["isST"][t, j]) == 1
        lim = limit_pct_for(pack["symbols"][j], st, pack["dates"][t])
        return abs(o / pre - 1.0) < lim - 0.002
    return bool(mask[t, j])
