"""Independent Path B. Does not call V13 feature_matrix / overlapping_series / day_book."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_alpha import EXCLUDE_ST, MIN_CROSS_SECTION, MIN_HISTORY_PAD
from research_engine.cn_a_share_alpha.cost import COMMISSION, SLIPPAGE, TRANSFER, stamp_duty_sell
from research_engine.cn_a_share_alpha_v13_1 import HOLD_DAYS, QUANTILE, SEED, SIDEWAYS_ABS_60D, STRESS_DD


def _close_ret(close):
    t, n = close.shape
    out = np.full((t, n), np.nan, dtype=np.float64)
    prev = close[:-1]
    cur = close[1:]
    ok = np.isfinite(prev) & np.isfinite(cur) & (prev > 0)
    out[1:] = np.where(ok, cur / prev - 1.0, np.nan)
    return out


def vol_score_b(close, lookback):
    """Independent vol path: window loop + nanmean (not features._rolling_sum)."""
    ret = _close_ret(close)
    t, n = ret.shape
    score = np.full((t, n), np.nan, dtype=np.float64)
    for i in range(lookback, t):
        w = ret[i - lookback + 1 : i + 1]
        finite = np.isfinite(w)
        cnt = np.sum(finite, axis=0)
        filled = np.where(finite, w, 0.0)
        mean = np.sum(filled, axis=0) / np.maximum(cnt, 1)
        second = np.sum(filled * filled, axis=0) / np.maximum(cnt, 1)
        var = second - mean * mean
        good = cnt == lookback
        vol = np.sqrt(np.maximum(var, 0.0))
        score[i] = np.where(good, -vol, np.nan)
        if i % 2000 == 0:
            print("VOL_B", lookback, i, "/", t, flush=True)
    return score


def eligible_b(pack, lookback):
    listed = np.array(pack["listed"]) == 1
    status = np.array(pack["tradestatus"]) == 1
    close = np.array(pack["close"])
    vol = np.array(pack["volume"])
    st = np.array(pack["isST"]) == 1
    hist = np.cumsum(np.isfinite(close).astype(np.int32), axis=0)
    elig = listed & status & np.isfinite(close) & (vol > 0) & (hist >= lookback + MIN_HISTORY_PAD)
    if EXCLUDE_ST:
        elig = elig & (~st)
    return elig


def pick_b(scores, mask):
    idx = np.where(mask & np.isfinite(scores))[0]
    if idx.size < MIN_CROSS_SECTION:
        return None
    n = int(max(1, round(idx.size * QUANTILE)))
    # lexsort: primary score, secondary index — not np.argsort
    order = np.lexsort((idx, scores[idx]))
    return idx[order[-n:]]


def fees_b(entry, exit_d, cost_k=1.0, slip_k=1.0):
    buy = (COMMISSION + TRANSFER) * cost_k + SLIPPAGE * slip_k
    sell = (COMMISSION + TRANSFER) * cost_k + SLIPPAGE * slip_k + stamp_duty_sell(exit_d) * cost_k
    return buy, sell, buy + sell


def _fills(pack, js, t0, t1, xok):
    js = np.asarray(js, dtype=np.int32)
    good = np.array(xok[t0, js]) & np.array(xok[t1, js])
    filled = js[good]
    if filled.size == 0:
        return filled, np.array([]), int(js.size)
    a = np.array(pack["open"][t0, filled], dtype=np.float64)
    b = np.array(pack["open"][t1, filled], dtype=np.float64)
    return filled, b / a - 1.0, int(js.size - filled.size)


def overlapping_b(pack, scores, elig, xok, start, end, cost_k=1.0, slip_k=1.0):
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    rows = []
    for t in range(i0, i1 + 1):
        t0 = t + 1
        t1 = t + 1 + HOLD_DAYS
        if t1 >= len(dates):
            break
        js = pick_b(scores[t], elig[t])
        if js is None:
            continue
        filled, rets, n_skip = _fills(pack, js, t0, t1, xok)
        if filled.size == 0:
            continue
        buy, sell, rt = fees_b(dates[t0], dates[t1], cost_k, slip_k)
        raw = float(np.mean(rets))
        rows.append(
            {
                "date": dates[t],
                "entry": dates[t0],
                "exit": dates[t1],
                "n_elig": int(np.sum(elig[t])),
                "n_sel": int(js.size),
                "n_fill": int(filled.size),
                "n_skip": n_skip,
                "raw": raw,
                "cost": rt,
                "net": raw - rt,
                "gross": raw,
                "commission": (COMMISSION * 2.0) * cost_k,
                "transfer": (TRANSFER * 2.0) * cost_k,
                "stamp": stamp_duty_sell(dates[t1]) * cost_k,
                "slippage": (SLIPPAGE * 2.0) * slip_k,
            }
        )
    return rows


def nonoverlap_detail(pack, scores, elig, xok, start, end):
    dates = pack["dates"]
    symbols = pack["symbols"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    equity = 1.0
    curve = [{"date": start, "equity": 1.0}]
    trades = []
    stock = {}
    t = i0
    while t <= i1:
        t0 = t + 1
        t1 = t + 1 + HOLD_DAYS
        if t1 >= len(dates):
            break
        js = pick_b(scores[t], elig[t])
        if js is None:
            t += 1
            continue
        filled, rets, n_skip = _fills(pack, js, t0, t1, xok)
        if filled.size == 0:
            t += 1
            continue
        buy, sell, rt = fees_b(dates[t0], dates[t1])
        raw = float(np.mean(rets))
        net = raw - rt
        equity *= 1.0 + net
        curve.append({"date": dates[t1], "equity": equity})
        amts = np.array(pack["amount"][t0, filled], dtype=np.float64)
        name_pnls = []
        for k, j in enumerate(filled):
            j = int(j)
            sym = symbols[j]
            g = float(rets[k])
            n = g - rt
            rec = stock.setdefault(sym, {"trades": 0, "gross": 0.0, "net": 0.0})
            rec["trades"] += 1
            rec["gross"] += g
            rec["net"] += n
            amt = float(amts[k]) if np.isfinite(amts[k]) else None
            if amt:
                rec.setdefault("amount_sum", 0.0)
                rec["amount_sum"] += amt
            if len(name_pnls) < 8 and sum(len(tr.get("names") or []) for tr in trades) < 120:
                name_pnls.append({"symbol": sym, "gross": g, "net": n, "amount": amt})
        amts_ok = amts[np.isfinite(amts) & (amts > 0)]
        adv = float(np.median(amts_ok)) if amts_ok.size else None
        trades.append(
            {
                "signal_date": dates[t],
                "entry": dates[t0],
                "exit": dates[t1],
                "n_elig": int(np.sum(elig[t])),
                "n_sel": int(js.size),
                "n_fill": int(filled.size),
                "n_skip": n_skip,
                "raw": raw,
                "cost": rt,
                "net": net,
                "hold_days": HOLD_DAYS,
                "adv": adv,
                "names": name_pnls,
                "filled_js": [int(j) for j in filled],
            }
        )
        t += HOLD_DAYS
    return curve, trades, stock


def ew_market_b(pack, elig, xok, start, end):
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    rows = []
    for t in range(i0, i1 + 1):
        t0 = t + 1
        t1 = t + 1 + HOLD_DAYS
        if t1 >= len(dates):
            break
        js = np.where(elig[t])[0]
        if js.size < MIN_CROSS_SECTION:
            continue
        filled, rets, n_skip = _fills(pack, js, t0, t1, xok)
        if filled.size == 0:
            continue
        buy, sell, rt = fees_b(dates[t0], dates[t1])
        raw = float(np.mean(rets))
        rows.append({"date": dates[t], "raw": raw, "net": raw - rt, "cost": rt})
    return rows


def random_quintile_b(pack, elig, xok, start, end, seed=SEED):
    rng = np.random.RandomState(seed)
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    rows = []
    for t in range(i0, i1 + 1):
        t0 = t + 1
        t1 = t + 1 + HOLD_DAYS
        if t1 >= len(dates):
            break
        idx = np.where(elig[t])[0]
        if idx.size < MIN_CROSS_SECTION:
            continue
        n = int(max(1, round(idx.size * QUANTILE)))
        js = rng.choice(idx, size=n, replace=False)
        filled, rets, n_skip = _fills(pack, js, t0, t1, xok)
        if filled.size == 0:
            continue
        buy, sell, rt = fees_b(dates[t0], dates[t1])
        raw = float(np.mean(rets))
        rows.append({"date": dates[t], "raw": raw, "net": raw - rt, "cost": rt})
    return rows


def permute_mean_net(pack, scores, elig, xok, start, end, n=100, seed=SEED):
    rng = np.random.RandomState(seed)
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    means = []
    for _ in range(n):
        acc = []
        for t in range(i0, i1 + 1):
            t0 = t + 1
            t1 = t + 1 + HOLD_DAYS
            if t1 >= len(dates):
                break
            idx = np.where(elig[t] & np.isfinite(scores[t]))[0]
            if idx.size < MIN_CROSS_SECTION:
                continue
            k = int(max(1, round(idx.size * QUANTILE)))
            js = rng.choice(idx, size=k, replace=False)
            filled, rets, _s = _fills(pack, js, t0, t1, xok)
            if filled.size == 0:
                continue
            _b, _s2, rt = fees_b(dates[t0], dates[t1])
            acc.append(float(np.mean(rets)) - rt)
        if acc:
            means.append(float(np.mean(acc)))
        if (_ + 1) % 20 == 0:
            print("PERM", _ + 1, "/", n, flush=True)
    return means


def market_ew_60(pack, elig):
    close = np.array(pack["close"], dtype=np.float64)
    t = close.shape[0]
    ew = np.full(t, np.nan)
    for i in range(t):
        m = elig[i] & np.isfinite(close[i]) & (close[i] > 0)
        if int(np.sum(m)) >= MIN_CROSS_SECTION:
            ew[i] = float(np.mean(close[i, m]))
    ret = np.full(t, np.nan)
    ok = np.isfinite(ew[1:]) & np.isfinite(ew[:-1]) & (ew[:-1] > 0)
    ret[1:] = np.where(ok, ew[1:] / ew[:-1] - 1.0, np.nan)
    r60 = np.full(t, np.nan)
    peak = -1e99
    dd = np.full(t, np.nan)
    eq = 1.0
    for i in range(1, t):
        if np.isfinite(ret[i]):
            eq *= 1.0 + ret[i]
        if eq > peak:
            peak = eq
        dd[i] = eq / peak - 1.0 if peak > 0 else np.nan
        if i >= 60:
            w = ret[i - 59 : i + 1]
            if np.all(np.isfinite(w)):
                r60[i] = float(np.prod(1.0 + w) - 1.0)
    return r60, dd


def regime_label(r60, dd):
    if not np.isfinite(r60):
        return None
    stress = bool(np.isfinite(dd) and dd <= STRESS_DD)
    if abs(r60) < SIDEWAYS_ABS_60D and not stress:
        side = "SIDEWAYS"
    elif r60 > 0:
        side = "BULL"
    else:
        side = "BEAR"
    return side + ("_STRESS" if stress else "_NORMAL")
