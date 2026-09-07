"""Set-membership books. Do not use quintile-of-binary (that dilutes the set)."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_alpha.cost import round_trip_cost
from research_engine.cn_a_share_alpha_v2.books import _fills
from research_engine.cn_a_share_index_v20 import INITIAL
from research_engine.cn_a_share_strategy_v14_1.capital_ref import exec_reason, period_capital


def pick_set(scores, mask, min_n=80):
    idx = np.where(mask & np.isfinite(scores) & (scores > 0.0))[0]
    if idx.size < min_n:
        return None
    return idx


def overlapping_predictive_set(pack, scores, elig, xok, start, end, hold, min_n=80):
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    rows = []
    for t in range(i0, i1 + 1):
        t0 = t + 1
        t1 = t + 1 + hold
        if t1 >= len(dates):
            break
        js = pick_set(scores[t], elig[t], min_n)
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


def capital_book_set(pack, scores, elig, xok, start, end, hold, min_n=80, initial=INITIAL):
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
        js = pick_set(scores[t], elig[t], min_n)
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
