"""Predictive overlapping MEAN_FORWARD_RETURN and canonical capital. Dual books."""
from __future__ import print_function

import math

import numpy as np

from research_engine.cn_a_share_alpha.cost import round_trip_cost
from research_engine.cn_a_share_alpha_v2 import INITIAL, MIN_CROSS_SECTION, QUANTILE, SEED
from research_engine.cn_a_share_strategy_v14_1.capital_ref import (
    buy_rate,
    exec_reason,
    period_capital,
    sell_rate,
)
from research_engine.cn_a_share_strategy_v14_1.scores import pick_lexsort


def _fills(pack, js, t0, t1, xok):
    js = np.asarray(js, dtype=np.int32)
    good = np.array(xok[t0, js]) & np.array(xok[t1, js])
    filled = js[good]
    if filled.size == 0:
        return filled, np.array([]), int(js.size)
    a = np.array(pack["open"][t0, filled], dtype=np.float64)
    b = np.array(pack["open"][t1, filled], dtype=np.float64)
    return filled, b / a - 1.0, int(js.size - filled.size)


def overlapping_predictive(pack, scores, elig, xok, start, end, hold, state=None):
    """Overlapping H-day mean of fills minus one RT. Metric name: MEAN_FORWARD_RETURN. Not CAGR."""
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    rows = []
    for t in range(i0, i1 + 1):
        t0 = t + 1
        t1 = t + 1 + hold
        if t1 >= len(dates):
            break
        if state is not None and not bool(state[t]):
            continue
        js = pick_lexsort(scores[t], elig[t])
        if js is None:
            continue
        filled, rets, n_skip = _fills(pack, js, t0, t1, xok)
        if filled.size == 0:
            continue
        raw = float(np.mean(rets))
        rt = round_trip_cost(dates[t0], dates[t1])
        rows.append(
            {
                "date": dates[t],
                "entry": dates[t0],
                "exit": dates[t1],
                "n_sel": int(js.size),
                "n_fill": int(filled.size),
                "n_skip": n_skip,
                "raw": raw,
                "cost": rt,
                "MEAN_FORWARD_RETURN": raw - rt,
            }
        )
    return rows


def ew_overlapping(pack, elig, xok, start, end, hold):
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    rows = []
    for t in range(i0, i1 + 1):
        t0 = t + 1
        t1 = t + 1 + hold
        if t1 >= len(dates):
            break
        js = np.where(elig[t])[0]
        if js.size < MIN_CROSS_SECTION:
            continue
        filled, rets, n_skip = _fills(pack, js, t0, t1, xok)
        if filled.size < MIN_CROSS_SECTION:
            continue
        raw = float(np.mean(rets))
        rt = round_trip_cost(dates[t0], dates[t1])
        rows.append({"date": dates[t], "MEAN_FORWARD_RETURN": raw - rt, "raw": raw})
    return rows


def random_overlapping(pack, elig, xok, start, end, hold, seed=SEED):
    rng = np.random.RandomState(seed)
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    rows = []
    for t in range(i0, i1 + 1):
        t0 = t + 1
        t1 = t + 1 + hold
        if t1 >= len(dates):
            break
        idx = np.where(elig[t] & np.isfinite(elig[t]))[0]
        if idx.size < MIN_CROSS_SECTION:
            continue
        n = int(max(1, round(idx.size * QUANTILE)))
        js = rng.choice(idx, size=n, replace=False)
        filled, rets, n_skip = _fills(pack, js, t0, t1, xok)
        if filled.size == 0:
            continue
        raw = float(np.mean(rets))
        rt = round_trip_cost(dates[t0], dates[t1])
        rows.append({"date": dates[t], "MEAN_FORWARD_RETURN": raw - rt})
    return rows


def forward_open(pack, t, hold):
    t0 = t + 1
    t1 = t + 1 + hold
    if t1 >= len(pack["dates"]):
        return None
    a = np.array(pack["open"][t0], dtype=np.float64)
    b = np.array(pack["open"][t1], dtype=np.float64)
    out = np.full(a.shape, np.nan)
    good = np.isfinite(a) & np.isfinite(b) & (a > 0)
    out[good] = b[good] / a[good] - 1.0
    return out


def spearman_ic(scores, elig, fwd):
    mask = elig & np.isfinite(scores) & np.isfinite(fwd)
    if int(np.sum(mask)) < 30:
        return None
    a = scores[mask]
    b = fwd[mask]
    ra = np.argsort(np.argsort(a)).astype(np.float64)
    rb = np.argsort(np.argsort(b)).astype(np.float64)
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float(np.sum(ra * ra) * np.sum(rb * rb)))
    if den == 0:
        return None
    return float(np.sum(ra * rb) / den)


def ic_series(pack, scores, elig, start, end, hold, state=None):
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    ics = []
    for t in range(i0, i1 + 1):
        if state is not None and not bool(state[t]):
            continue
        fwd = forward_open(pack, t, hold)
        if fwd is None:
            continue
        ic = spearman_ic(scores[t], elig[t], fwd)
        if ic is not None:
            ics.append(ic)
    return ics


def capital_book(pack, scores, elig, xok, start, end, hold, initial=INITIAL, state=None, cost_k=1.0, slip_k=1.0):
    """Non-overlapping capital. Unfilled stays cash. Independent of V14 simulate()."""
    dates = pack["dates"]
    symbols = pack["symbols"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    equity = float(initial)
    trades = []
    ledger = []
    reasons = {}
    t = i0
    while t <= i1:
        t0 = t + 1
        t1 = t + 1 + hold
        if t1 >= len(dates):
            break
        if state is not None and not bool(state[t]):
            t += 1
            continue
        js = pick_lexsort(scores[t], elig[t])
        if js is None:
            t += 1
            continue
        raws = []
        fills = []
        why = []
        for j in js:
            j = int(j)
            c0 = "FILL" if bool(xok[t0, j]) else exec_reason(pack, t0, j)
            if c0 == "FILL":
                c1 = "FILL" if bool(xok[t1, j]) else exec_reason(pack, t1, j)
            else:
                c1 = c0
            reason = c0 if c0 != "FILL" else c1
            filled = reason == "FILL"
            raw = 0.0
            if filled:
                a = float(pack["open"][t0, j])
                b = float(pack["open"][t1, j])
                raw = b / a - 1.0
            else:
                reasons[reason] = reasons.get(reason, 0) + 1
            raws.append(raw)
            fills.append(filled)
            why.append(reason)
        if not any(fills):
            t += 1
            continue
        rec = period_capital(equity, raws, fills, dates[t1])
        # period_capital uses locked 1x rates; scale via net approximation if stressed
        if cost_k != 1.0 or slip_k != 1.0:
            filled_raws = [r for r, f in zip(raws, fills) if f]
            br = buy_rate() * 0 + (0.00025 + 0.00001) * cost_k + 0.0010 * slip_k
            sr = (0.00025 + 0.00001) * cost_k + 0.0010 * slip_k
            # rebuild with scaled rates
            n = len(fills)
            w = 1.0 / float(n)
            nets = []
            for raw, filled in zip(raws, fills):
                alloc = equity * w
                if not filled:
                    nets.append(0.0)
                    continue
                notional = alloc / (1.0 + br)
                cash_out = notional * (1.0 + br)
                sell_notional = notional * (1.0 + raw)
                st = sell_notional * (0.0005 if dates[t1] >= "2023-08-28" else 0.0010) * cost_k
                cash_in = sell_notional * (1.0 - (0.00025 + 0.00001) * cost_k - 0.0010 * slip_k) - st
                nets.append(cash_in - cash_out)
            rec = {
                "end": equity + float(sum(nets)),
                "ret": (equity + float(sum(nets))) / equity - 1.0,
                "n_filled": int(sum(1 for f in fills if f)),
                "name_nets": nets,
                "fees": 0.0,
                "slippage": 0.0,
                "stamp": 0.0,
                "name_gross": [0.0] * n,
                "name_fees": [0.0] * n,
                "name_slip": [0.0] * n,
                "name_stamp": [0.0] * n,
                "cash_frac": 1.0 - w * int(sum(1 for f in fills if f)),
            }
        w = 1.0 / float(len(js))
        for k, j in enumerate(js):
            ledger.append(
                {
                    "signal_date": dates[t],
                    "symbol": symbols[int(j)],
                    "filled": 1 if fills[k] else 0,
                    "reason": why[k],
                    "net": rec["name_nets"][k],
                    "weight": w,
                }
            )
        start_eq = equity
        equity = rec["end"]
        trades.append(
            {
                "signal_date": dates[t],
                "entry": dates[t0],
                "exit": dates[t1],
                "n_sel": int(len(js)),
                "n_fill": rec["n_filled"],
                "capital_ret": rec["ret"],
                "net_yuan": equity - start_eq,
                "equity": equity,
            }
        )
        t += hold
    n_sel = sum(tr["n_sel"] for tr in trades)
    n_uf = sum(tr["n_sel"] - tr["n_fill"] for tr in trades)
    return {
        "start": initial,
        "end": equity,
        "total": equity / initial - 1.0 if initial else None,
        "trades": trades,
        "ledger": ledger,
        "reasons": reasons,
        "unfilled_rate": (float(n_uf) / n_sel) if n_sel else None,
        "n_trades": len(trades),
        "recon_ok": abs(equity - (initial + sum(tr["net_yuan"] for tr in trades))) < 1e-4,
    }


def capital_cagr(start, end, n_days, year_days=242.0):
    if start <= 0 or end <= 0 or n_days <= 0:
        return None
    return (end / start) ** (year_days / float(n_days)) - 1.0


def maxdd_from_trades(trades, start_eq, start_date):
    peak = start_eq
    dd = 0.0
    peak_d = start_date
    trough_d = None
    last_peak = start_date
    eq = start_eq
    for tr in trades:
        eq = tr["equity"]
        if eq > peak:
            peak = eq
            last_peak = tr["exit"]
        if peak > 0:
            cur = eq / peak - 1.0
            if cur < dd:
                dd = cur
                peak_d = last_peak
                trough_d = tr["exit"]
    return {"maxdd": dd, "peak_date": peak_d, "trough_date": trough_d}
