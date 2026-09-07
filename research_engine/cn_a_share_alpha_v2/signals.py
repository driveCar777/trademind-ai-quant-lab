"""V15 signals. Residual / dispersion state / price-activity disagreement. Causal through close(t)."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_alpha_v2 import MIN_CROSS_SECTION
from research_engine.cn_a_share_strategy_v14_1.scores import daily_return, eligible


def _rolling_sum(x, w):
    """Window sum and finite count. Count stays int32 so a second 8714x5549 int64 is not allocated."""
    valid = np.isfinite(x)
    x0 = np.where(valid, x, 0.0)
    c = np.cumsum(x0, axis=0, dtype=np.float64)
    n = np.cumsum(valid, axis=0, dtype=np.int32)
    s = np.empty(c.shape, dtype=np.float64)
    cnt = np.empty(n.shape, dtype=np.int32)
    s[: w - 1] = np.nan
    cnt[: w - 1] = 0
    s[w - 1 :] = c[w - 1 :]
    cnt[w - 1 :] = n[w - 1 :]
    if w < c.shape[0]:
        s[w:] = c[w:] - c[:-w]
        cnt[w:] = n[w:] - n[:-w]
    return s, cnt


def residual_pack(pack, lookback=20):
    """EW-market residual of raw close-to-close. Market is today's eligible mean."""
    ret = daily_return(np.array(pack["close"], dtype=np.float64))
    elig = eligible(pack, lookback)
    t, n = ret.shape
    market = np.full(t, np.nan, dtype=np.float64)
    resid = np.full((t, n), np.nan, dtype=np.float64)
    for i in range(t):
        m = elig[i] & np.isfinite(ret[i])
        if int(np.sum(m)) < MIN_CROSS_SECTION:
            continue
        mu = float(np.mean(ret[i, m]))
        market[i] = mu
        resid[i] = np.where(m, ret[i] - mu, np.nan)
    return {"ret": ret, "elig": elig, "market": market, "resid": resid}


def neg_residual_sum(resid, lookback):
    s, cnt = _rolling_sum(resid, lookback)
    return np.where(cnt == lookback, -s, np.nan)


def cs_dispersion(resid, elig):
    t = resid.shape[0]
    out = np.full(t, np.nan, dtype=np.float64)
    for i in range(t):
        m = elig[i] & np.isfinite(resid[i])
        if int(np.sum(m)) < MIN_CROSS_SECTION:
            continue
        out[i] = float(np.std(resid[i, m]))
    return out


def cs_breadth(ret, elig):
    t = ret.shape[0]
    out = np.full(t, np.nan, dtype=np.float64)
    for i in range(t):
        m = elig[i] & np.isfinite(ret[i])
        if int(np.sum(m)) < MIN_CROSS_SECTION:
            continue
        out[i] = float(np.mean(ret[i, m] > 0))
    return out


def trailing_median(x, w):
    out = np.full(x.shape, np.nan, dtype=np.float64)
    for i in range(w - 1, len(x)):
        wdw = x[i - w + 1 : i + 1]
        fin = wdw[np.isfinite(wdw)]
        if fin.size >= max(8, w // 2):
            out[i] = float(np.median(fin))
    return out


def state_mask(kind, disp, breadth, state_lookback):
    if kind is None:
        return None
    if kind == "DISP_HIGH_MEDIAN_60":
        med = trailing_median(disp, state_lookback)
        return np.isfinite(disp) & np.isfinite(med) & (disp >= med)
    if kind == "DISP_RISING_20":
        out = np.zeros(disp.shape, dtype=bool)
        lag = state_lookback
        out[lag:] = np.isfinite(disp[lag:]) & np.isfinite(disp[:-lag]) & (disp[lag:] > disp[:-lag])
        return out
    if kind == "DISP_HIGH_AND_BREADTH_LOW":
        dmed = trailing_median(disp, state_lookback)
        bmed = trailing_median(breadth, state_lookback)
        return (
            np.isfinite(disp)
            & np.isfinite(dmed)
            & np.isfinite(breadth)
            & np.isfinite(bmed)
            & (disp >= dmed)
            & (breadth <= bmed)
        )
    raise ValueError(kind)


def _cs_rank(row):
    out = np.full(row.shape, np.nan, dtype=np.float64)
    ok = np.isfinite(row)
    if int(np.sum(ok)) < MIN_CROSS_SECTION:
        return out
    vals = row[ok]
    order = np.argsort(np.argsort(vals)).astype(np.float64)
    out[ok] = order
    return out


def capitulation_score(ret, amount, lookback):
    rs, rc = _rolling_sum(ret, lookback)
    am = np.array(amount, dtype=np.float64)
    am = np.where(np.isfinite(am) & (am > 0), am, np.nan)
    as_, ac = _rolling_sum(am, lookback)
    ret_sum = np.where(rc == lookback, rs, np.nan)
    amt_sum = np.where(ac == lookback, as_, np.nan)
    t = ret_sum.shape[0]
    score = np.full(ret_sum.shape, np.nan, dtype=np.float64)
    for i in range(t):
        score[i] = _cs_rank(-ret_sum[i]) + _cs_rank(amt_sum[i])
    return score


def dlog_amount(amount):
    am = np.array(amount, dtype=np.float64)
    out = np.full(am.shape, np.nan, dtype=np.float64)
    prev = am[:-1]
    cur = am[1:]
    ok = np.isfinite(prev) & np.isfinite(cur) & (prev > 0) & (cur > 0)
    step = np.full(cur.shape, np.nan, dtype=np.float64)
    step[ok] = np.log(cur[ok] / prev[ok])
    out[1:] = step
    return out


def _corr_chunk(ret, y, lookback):
    sx, nx = _rolling_sum(ret, lookback)
    sy, ny = _rolling_sum(y, lookback)
    sxy, nxy = _rolling_sum(ret * y, lookback)
    sx2, _ = _rolling_sum(ret * ret, lookback)
    sy2, _ = _rolling_sum(y * y, lookback)
    good = (nx == lookback) & (ny == lookback) & (nxy == lookback)
    L = float(lookback)
    num = sxy - sx * sy / L
    den = np.sqrt(np.maximum(sx2 - sx * sx / L, 0.0) * np.maximum(sy2 - sy * sy / L, 0.0))
    return np.where(good & (den > 0), num / den, np.nan)


def neg_ret_amount_corr(ret, amount, lookback, chunk=256):
    """Column-chunked so five rolling panels are never allocated at full 8714x5549."""
    t, n = ret.shape
    out = np.full((t, n), np.nan, dtype=np.float64)
    for j0 in range(0, n, chunk):
        j1 = min(n, j0 + chunk)
        r = np.array(ret[:, j0:j1], dtype=np.float64)
        y = dlog_amount(amount[:, j0:j1])
        out[:, j0:j1] = -_corr_chunk(r, y, lookback)
    return out


def score_for(hyp, cache):
    sig = hyp["signal"]
    L = hyp["lookback"]
    if sig == "NEG_RESIDUAL_SUM":
        return neg_residual_sum(cache["resid"], L)
    if sig == "RANK_NEG_RET_PLUS_RANK_AMOUNT":
        return capitulation_score(cache["ret"], cache["amount"], L)
    if sig == "NEG_RET_DLOG_AMOUNT_CORR":
        return neg_ret_amount_corr(cache["ret"], cache["amount"], L)
    raise ValueError(sig)
