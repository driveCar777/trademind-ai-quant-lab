"""Independent V14 strategy calculator. Does not call V13 feature_matrix / day_book."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_strategy_v14 import (
    EXCLUDE_ST,
    HOLD_DAYS,
    INITIAL_CAPITAL,
    MIN_CROSS_SECTION,
    MIN_HISTORY_PAD,
    QUANTILE,
)
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, TRANSFER, buy_rate, stamp_duty_sell

FILL = 0
LIMIT_LOCK = 1
SUSPENDED = 2
DELISTED = 3
ZERO_VOLUME = 4
MISSING_OPEN = 5
REASON = {
    FILL: "FILL",
    LIMIT_LOCK: "LIMIT_LOCK",
    SUSPENDED: "SUSPENDED",
    DELISTED: "DELISTED",
    ZERO_VOLUME: "ZERO_VOLUME",
    MISSING_OPEN: "MISSING_OPEN",
}


def daily_return(close):
    out = np.full(close.shape, np.nan, dtype=np.float64)
    prev = close[:-1]
    cur = close[1:]
    ok = np.isfinite(prev) & np.isfinite(cur) & (prev > 0)
    out[1:] = np.where(ok, cur / prev - 1.0, np.nan)
    return out


def vol_score(close, lookback):
    """Population window std of raw close returns, negated. Local cumsum, not V13 _rolling_sum."""
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
    s[:lookback] = np.nan
    var = s2 / float(lookback) - (s / float(lookback)) ** 2
    good = cnt == lookback
    vol = np.sqrt(np.maximum(var, 0.0))
    return np.where(good, -vol, np.nan)


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


def pick_low_vol(scores, mask):
    idx = np.where(mask & np.isfinite(scores))[0]
    if idx.size < MIN_CROSS_SECTION:
        return None
    n = int(max(1, round(idx.size * QUANTILE)))
    order = np.lexsort((idx, scores[idx]))
    chosen = idx[order[-n:]]
    ranks = {}
    for r, j in enumerate(chosen[np.argsort(-scores[chosen])], start=1):
        ranks[int(j)] = r
    return chosen, ranks


def _limit_pct(symbol, is_st, day):
    if is_st:
        return 0.05
    if symbol.startswith("bj."):
        return 0.30
    if symbol.startswith("sh.688"):
        return 0.20
    if symbol.startswith("sz.30"):
        return 0.20 if day >= "2020-08-24" else 0.10
    return 0.10


def exec_code(pack, t, j):
    if int(pack["listed"][t, j]) != 1:
        return DELISTED
    if int(pack["tradestatus"][t, j]) != 1:
        return SUSPENDED
    o = float(pack["open"][t, j])
    pre = float(pack["preclose"][t, j])
    v = float(pack["volume"][t, j])
    if not np.isfinite(o) or o <= 0 or not np.isfinite(pre) or pre <= 0:
        return MISSING_OPEN
    if not np.isfinite(v) or v <= 0:
        return ZERO_VOLUME
    st = int(pack["isST"][t, j]) == 1
    lim = _limit_pct(pack["symbols"][j], st, pack["dates"][t])
    if abs(o / pre - 1.0) >= (lim - 0.002):
        return LIMIT_LOCK
    return FILL


def simulate(pack, scores, elig, start, end, cost_k=1.0, slip_k=1.0, initial=INITIAL_CAPITAL, daily_mtm=True):
    dates = pack["dates"]
    symbols = pack["symbols"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    cash = float(initial)
    equity = float(initial)
    curve = [{"date": start, "equity": equity, "cash": cash, "invested": 0.0}]
    trades = []
    ledger = []
    unfilled = {k: 0 for k in REASON if k != FILL}
    n_selected = 0
    n_filled = 0
    t = i0
    while t <= i1:
        t0 = t + 1
        t1 = t + 1 + HOLD_DAYS
        if t1 >= len(dates):
            break
        picked = pick_low_vol(scores[t], elig[t])
        if picked is None:
            t += 1
            continue
        js, ranks = picked
        n_sel = int(js.size)
        n_selected += n_sel
        fills = []
        for j in js:
            j = int(j)
            c0 = exec_code(pack, t0, j)
            c1 = exec_code(pack, t1, j) if c0 == FILL else c0
            code = c0 if c0 != FILL else c1
            if code != FILL:
                unfilled[code] = unfilled.get(code, 0) + 1
                ledger.append(
                    {
                        "signal_date": dates[t],
                        "entry": dates[t0],
                        "exit": dates[t1],
                        "symbol": symbols[j],
                        "signal_rank": ranks[j],
                        "weight": 1.0 / n_sel,
                        "expected_price": None,
                        "execution_price": None,
                        "filled": 0,
                        "reason": REASON[code],
                        "gross_pnl": 0.0,
                        "fees": 0.0,
                        "slippage": 0.0,
                        "stamp": 0.0,
                        "net_pnl": 0.0,
                    }
                )
                continue
            fills.append(j)
        if not fills:
            t += 1
            continue
        w = 1.0 / n_sel
        br = buy_rate(cost_k, slip_k)
        start_eq = equity
        leftover = start_eq
        held_j = []
        held_shares = []
        period_gross = 0.0
        period_net = 0.0
        period_fees = 0.0
        period_slip = 0.0
        period_stamp = 0.0
        for j in fills:
            o0 = float(pack["open"][t0, j])
            o1 = float(pack["open"][t1, j])
            alloc = start_eq * w
            notional = alloc / (1.0 + br)
            shares = notional / o0
            leftover -= notional * (1.0 + br)
            buy_fee = notional * (COMMISSION + TRANSFER) * cost_k
            buy_slip = notional * SLIPPAGE * slip_k
            sell_notional = shares * o1
            stamp = sell_notional * stamp_duty_sell(dates[t1]) * cost_k
            sell_slip = sell_notional * SLIPPAGE * slip_k
            sell_fee = sell_notional * (COMMISSION + TRANSFER) * cost_k
            cash_out = notional * (1.0 + br)
            cash_in = sell_notional - sell_fee - sell_slip - stamp
            net = cash_in - cash_out
            gross = sell_notional - notional
            fees = buy_fee + sell_fee + stamp
            slip = buy_slip + sell_slip
            period_gross += gross
            period_net += net
            period_fees += fees
            period_slip += slip
            period_stamp += stamp
            n_filled += 1
            amt = float(pack["amount"][t0, j])
            ledger.append(
                {
                    "signal_date": dates[t],
                    "entry": dates[t0],
                    "exit": dates[t1],
                    "symbol": symbols[j],
                    "signal_rank": ranks[j],
                    "weight": w,
                    "expected_price": o0,
                    "execution_price": o0,
                    "filled": 1,
                    "reason": "FILL",
                    "gross_pnl": gross,
                    "fees": fees,
                    "slippage": slip,
                    "stamp": stamp,
                    "net_pnl": net,
                    "adv_amount": amt if np.isfinite(amt) else None,
                    "position_value": notional,
                }
            )
            held_j.append(j)
            held_shares.append(shares)
        if daily_mtm and held_j:
            js = np.asarray(held_j, dtype=np.int32)
            sh = np.asarray(held_shares, dtype=np.float64)
            block = np.array(pack["close"][t0:t1, js], dtype=np.float64)
            o0s = np.array(pack["open"][t0, js], dtype=np.float64)
            bad = ~np.isfinite(block) | (block <= 0)
            block = np.where(bad, o0s, block)
            invs = np.sum(block * sh, axis=1)
            for k, d in enumerate(range(t0, t1)):
                curve.append({"date": dates[d], "equity": leftover + float(invs[k]), "cash": leftover, "invested": float(invs[k])})
        cash = leftover
        for j, shares in zip(held_j, held_shares):
            o1 = float(pack["open"][t1, j])
            sell_notional = shares * o1
            stamp = sell_notional * stamp_duty_sell(dates[t1]) * cost_k
            sell_slip = sell_notional * SLIPPAGE * slip_k
            sell_fee = sell_notional * (COMMISSION + TRANSFER) * cost_k
            cash += sell_notional - sell_fee - sell_slip - stamp
        equity = cash
        curve.append({"date": dates[t1], "equity": equity, "cash": cash, "invested": 0.0})
        trades.append(
            {
                "signal_date": dates[t],
                "entry": dates[t0],
                "exit": dates[t1],
                "n_selected": n_sel,
                "n_filled": len(fills),
                "n_unfilled": n_sel - len(fills),
                "gross": period_gross,
                "net": period_net,
                "fees": period_fees,
                "slippage": period_slip,
                "stamp": period_stamp,
                "equity": equity,
                "ret": (equity / start_eq - 1.0) if start_eq else 0.0,
            }
        )
        t += HOLD_DAYS
    u_total = int(sum(unfilled.values()))
    return {
        "curve": curve,
        "trades": trades,
        "ledger": ledger,
        "start": initial,
        "end": equity,
        "n_selected": n_selected,
        "n_filled": n_filled,
        "n_unfilled": u_total,
        "unfilled_reasons": dict((REASON[k], int(v)) for k, v in unfilled.items()),
        "unfilled_rate": (float(u_total) / float(n_selected)) if n_selected else None,
        "limit_lock_rate": (float(unfilled.get(LIMIT_LOCK, 0)) / float(n_selected)) if n_selected else None,
    }


def ew_market_curve(pack, elig, start, end, initial=1.0):
    """EW eligible open-to-open proxy. Ignores limit-lock. Not a purchased index."""
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    eq = float(initial)
    curve = [{"date": start, "equity": eq}]
    t = i0
    while t <= i1:
        t0 = t + 1
        t1 = t + 1 + HOLD_DAYS
        if t1 >= len(dates):
            break
        js = np.where(elig[t])[0]
        if js.size < MIN_CROSS_SECTION:
            t += 1
            continue
        a = np.array(pack["open"][t0, js], dtype=np.float64)
        b = np.array(pack["open"][t1, js], dtype=np.float64)
        good = np.isfinite(a) & np.isfinite(b) & (a > 0)
        if int(np.sum(good)) < MIN_CROSS_SECTION:
            t += 1
            continue
        eq *= 1.0 + float(np.mean(b[good] / a[good] - 1.0))
        curve.append({"date": dates[t1], "equity": eq})
        t += HOLD_DAYS
    return curve
