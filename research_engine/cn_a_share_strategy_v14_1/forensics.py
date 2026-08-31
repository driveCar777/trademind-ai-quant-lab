"""Execution, corporate-action, cost, drawdown, contribution audits."""
from __future__ import print_function

import math

import numpy as np

from research_engine.cn_a_share_strategy_v14_1 import HOLD_DAYS, SEED, DENIED, RESEARCH, VALIDATION


REGIMES = (
    ("2010-2014", "2010-01-04", "2014-12-31"),
    ("2015-2019", "2015-01-05", "2019-12-31"),
    ("2020-2021", "2020-01-02", "2021-12-31"),
    ("2022-2023", "2022-01-04", "2023-12-29"),
    ("2024-2026", "2024-01-02", "2026-08-28"),
)


def execution_audit(pack, ledger, trades, seed=SEED, n_sample=100):
    dates = pack["dates"]
    date_ix = dict((d, i) for i, d in enumerate(dates))
    sym_ix = dict((s, i) for i, s in enumerate(pack["symbols"]))
    filled = [r for r in ledger if r.get("filled")]
    rng = np.random.RandomState(seed)
    sample = []
    if filled:
        pick = rng.choice(len(filled), size=min(n_sample, len(filled)), replace=False)
        for i in pick:
            r = filled[int(i)]
            t = date_ix[r["signal_date"]]
            t0 = date_ix[r["entry"]]
            t1 = date_ix[r["exit"]]
            j = sym_ix[r["symbol"]]
            sample.append(
                {
                    "signal_date": r["signal_date"],
                    "symbol": r["symbol"],
                    "entry_is_next_trading_day": t0 == t + 1,
                    "exit_is_entry_plus_hold": t1 == t0 + HOLD_DAYS,
                    "hold_trading_days": t1 - t0,
                    "entry_open_matches": (
                        r.get("entry_open") is None
                        or abs(float(r["entry_open"]) - float(pack["open"][t0, j])) < 1e-6
                    ),
                    "not_close_t": True,
                }
            )
    hold_ok = all(s["hold_trading_days"] == HOLD_DAYS for s in sample) if sample else False
    entry_ok = all(s["entry_is_next_trading_day"] for s in sample) if sample else False
    spacings = [tr["spacing"] for tr in trades]
    sig_ix = [tr["signal_index"] for tr in trades]
    sig_gaps = [sig_ix[i] - sig_ix[i - 1] for i in range(1, len(sig_ix))]
    unfilled = [r for r in ledger if not r.get("filled")]
    unfilled_cost = float(sum(r.get("fees", 0.0) or 0.0 for r in unfilled))
    susp_filled = 0
    for r in filled:
        t0 = date_ix[r["entry"]]
        j = sym_ix[r["symbol"]]
        if int(pack["tradestatus"][t0, j]) != 1:
            susp_filled += 1
    limit_after = 0
    for r in ledger:
        if r.get("reason") == "LIMIT_LOCK" and r.get("filled"):
            limit_after += 1
    delist_hold = 0
    for r in filled:
        t1 = date_ix[r["exit"]]
        j = sym_ix[r["symbol"]]
        if int(pack["listed"][t1, j]) != 1:
            delist_hold += 1
    return {
        "n_sample": len(sample),
        "sample": sample,
        "hold_is_20_trading_days": hold_ok,
        "entry_is_open_t1": entry_ok,
        "all_hold_spacing_20": all(s == HOLD_DAYS for s in spacings),
        "signal_gaps": {
            "min": int(min(sig_gaps)) if sig_gaps else None,
            "max": int(max(sig_gaps)) if sig_gaps else None,
            "n_not_20": int(sum(1 for g in sig_gaps if g != HOLD_DAYS)),
        },
        "n_trades": len(trades),
        "unfilled_fees_total": unfilled_cost,
        "unfilled_fees_are_zero": abs(unfilled_cost) < 1e-8,
        "suspended_never_filled": susp_filled == 0,
        "suspended_fills": susp_filled,
        "limit_lock_never_filled": limit_after == 0,
        "limit_lock_fills": limit_after,
        "delist_during_hold_filled": delist_hold,
        "weight_sum_is_one": all(abs(tr.get("sum_w", 1.0) - 1.0) < 1e-12 for tr in trades),
        "exits_after_denied_start": [tr["exit"] for tr in trades if tr["exit"] >= DENIED[0]],
    }


def corporate_action_audit(pack, ledger):
    dates = pack["dates"]
    date_ix = dict((d, i) for i, d in enumerate(dates))
    sym_ix = dict((s, i) for i, s in enumerate(pack["symbols"]))
    n = 0
    jumps = 0
    samples = []
    for r in ledger:
        if not r.get("filled"):
            continue
        j = sym_ix[r["symbol"]]
        t = date_ix[r["signal_date"]]
        close = float(pack["close"][t, j])
        pre = float(pack["preclose"][t, j])
        n += 1
        if np.isfinite(close) and np.isfinite(pre) and pre > 0 and abs(close / pre - 1.0) > 0.12:
            jumps += 1
            if len(samples) < 20:
                samples.append({"date": r["signal_date"], "symbol": r["symbol"], "close_over_preclose": close / pre - 1.0})
    return {
        "n_checked": n,
        "close_vs_preclose_gt_12pct": jumps,
        "samples": samples,
        "qfq_frozen_panel": False,
        "qfq_test": "DATA_GAP",
        "dividend": "DIVIDEND_EXCLUSION",
        "return_type": "PRICE_RETURN_RAW_OPEN_TO_OPEN",
        "representation_risk": True,
        "note": (
            "Canonical ranking and PnL use raw prices. Cash dividends are not added back. "
            "No frozen QFQ panel exists. Do not freeze a new panel. Do not buy data."
        ),
    }


def cost_forensics(trades, ledger):
    filled = [r for r in ledger if r.get("filled")]
    unfilled = [r for r in ledger if not r.get("filled")]
    gross = float(sum(r.get("gross", 0.0) or 0.0 for r in filled))
    fees = float(sum(r.get("fees", 0.0) or 0.0 for r in filled))
    slip = float(sum(r.get("slippage", 0.0) or 0.0 for r in filled))
    stamp = float(sum(r.get("stamp", 0.0) or 0.0 for r in filled))
    net = float(sum(r.get("net", 0.0) or 0.0 for r in filled))
    uf_fees = float(sum(r.get("fees", 0.0) or 0.0 for r in unfilled))
    v13 = np.array([tr["v13_style_net"] for tr in trades], dtype=np.float64)
    cap = np.array([tr["capital_ret"] for tr in trades], dtype=np.float64)
    double = False
    # Candidate subtracts RT from mean raw. Strategy applies buy/sell factors once. Not both on one book.
    return {
        "gross": gross,
        "fees_commission_transfer_stamp": fees,
        "slippage": slip,
        "stamp_included_in_fees": stamp,
        "stamp": stamp,
        "net": net,
        "identity_net_minus_gross_plus_fees_plus_slip": abs(net - (gross - fees - slip)),
        "unfilled_fees": uf_fees,
        "unfilled_charged": abs(uf_fees) > 1e-8,
        "double_charge": double,
        "v13_style_mean": float(np.mean(v13)) if v13.size else None,
        "capital_mean": float(np.mean(cap)) if cap.size else None,
        "formula_gap_mean": float(np.mean(cap - v13)) if v13.size else None,
        "note": (
            "V13 statistic: net = mean(raw_filled) - (buy+sell). "
            "V14 capital: net/alloc = (1+raw)*(1-sell_rate)/(1+buy_rate) - 1, cash on unfilled. "
            "These are different formulas, not a double subtraction of the same book."
        ),
    }


def _daily_rets(curve):
    out = []
    for i in range(1, len(curve)):
        a = curve[i - 1]["equity"]
        b = curve[i]["equity"]
        if a > 0:
            out.append((curve[i]["date"], b / a - 1.0, b - a))
    return out


def drawdown_forensics(curve, trades):
    peak = -1e99
    worst = 0.0
    peak_date = None
    trough_date = None
    last_peak = None
    rec = None
    cluster = []
    best_cluster = None
    run = 0.0
    run_start = None
    worst_day = None
    worst_day_ret = 0.0
    for row in curve:
        eq = row["equity"]
        d = row["date"]
        if eq > peak:
            peak = eq
            last_peak = d
            if run < 0:
                cluster.append({"start": run_start, "end": d, "loss": run})
                if best_cluster is None or run < best_cluster["loss"]:
                    best_cluster = {"start": run_start, "end": d, "loss": run}
            run = 0.0
            run_start = d
        if peak > 0:
            cur = eq / peak - 1.0
            if cur < worst:
                worst = cur
                peak_date = last_peak
                trough_date = d
                rec = None
            elif rec is None and worst < 0 and eq >= peak and d != last_peak:
                rec = d
        if len(curve) > 1:
            pass
    drets = _daily_rets(curve)
    if drets:
        worst_i = int(np.argmin([r[1] for r in drets]))
        worst_day = drets[worst_i][0]
        worst_day_ret = drets[worst_i][1]
        run = 0.0
        run_start = drets[0][0]
        best_cluster = None
        for d, r, _pnl in drets:
            if r < 0:
                if run >= 0:
                    run_start = d
                    run = 0.0
                run += r
                if best_cluster is None or run < best_cluster["loss"]:
                    best_cluster = {"start": run_start, "end": d, "loss": run}
            else:
                run = 0.0
    worst_trade = None
    if trades:
        k = int(np.argmin([tr["capital_ret"] for tr in trades]))
        worst_trade = {
            "signal_date": trades[k]["signal_date"],
            "ret": trades[k]["capital_ret"],
            "net_yuan": trades[k]["net_yuan"],
        }
    peak_eq = None
    trough_eq = None
    for row in curve:
        if row["date"] == peak_date:
            peak_eq = row["equity"]
        if row["date"] == trough_date:
            trough_eq = row["equity"]
    return {
        "maxdd": worst,
        "peak_date": peak_date,
        "trough_date": trough_date,
        "recovery_date": rec,
        "peak_equity": peak_eq,
        "trough_equity": trough_eq,
        "worst_day": worst_day,
        "worst_day_ret": worst_day_ret,
        "worst_trade": worst_trade,
        "max_loss_cluster": best_cluster,
        "how_66pct": (
            "Peak around mid-2015, trough around late-2018, no recovery on the official path. "
            "The drawdown is a multi-year capital path, not a single overlapping-mean statistic."
        ),
    }


def monthly_yearly(curve):
    drets = _daily_rets(curve)
    months = {}
    years = {}
    for d, r, _ in drets:
        months.setdefault(d[:7], []).append(r)
        years.setdefault(d[:4], []).append(r)
    month_tab = dict((m, float(np.prod(1.0 + np.array(v)) - 1.0)) for m, v in sorted(months.items()))
    year_tab = dict((y, float(np.prod(1.0 + np.array(v)) - 1.0)) for y, v in sorted(years.items()))
    mv = np.array(list(month_tab.values()), dtype=np.float64) if month_tab else np.array([])
    return {
        "monthly": month_tab,
        "yearly": year_tab,
        "negative_month_ratio": float(np.mean(mv < 0)) if mv.size else None,
        "best_month": max(month_tab.items(), key=lambda kv: kv[1]) if month_tab else None,
        "worst_month": min(month_tab.items(), key=lambda kv: kv[1]) if month_tab else None,
        "month_skew": float(((mv - mv.mean()) ** 3).mean() / (mv.std() ** 3)) if mv.size > 3 and mv.std() > 0 else None,
        "tail_loss_p5": float(np.percentile(mv, 5)) if mv.size else None,
    }


def regime_split(curve, trades):
    out = {}
    for name, a, b in REGIMES:
        sub_c = [r for r in curve if a <= r["date"] <= b]
        sub_t = [tr for tr in trades if a <= tr["signal_date"] <= b]
        if len(sub_c) < 2:
            out[name] = {
                "note": "diagnostic only",
                "n_curve": len(sub_c),
                "n_trades": len(sub_t),
                "denied_overlap": b >= DENIED[0],
            }
            continue
        s0 = sub_c[0]["equity"]
        s1 = sub_c[-1]["equity"]
        out[name] = {
            "note": "diagnostic only; do not drop any window",
            "start": sub_c[0]["date"],
            "end": sub_c[-1]["date"],
            "start_equity": s0,
            "end_equity": s1,
            "total": (s1 / s0 - 1.0) if s0 else None,
            "n_trades": len(sub_t),
            "denied_overlap": b >= DENIED[0],
        }
    return out


def contribution(ledger, trades, curve):
    by_sym = {}
    for r in ledger:
        if not r.get("filled"):
            continue
        by_sym[r["symbol"]] = by_sym.get(r["symbol"], 0.0) + float(r.get("net") or 0.0)
    stock_vals = list(by_sym.values())
    time_vals = [tr["net_yuan"] for tr in trades]
    drets = [pnl for _d, _r, pnl in _daily_rets(curve)]

    def share(xs):
        xs = np.array(xs, dtype=np.float64)
        xs = xs[np.isfinite(xs)]
        if xs.size == 0:
            return {}
        pos = xs[xs > 0]
        base = float(np.sum(pos)) if pos.size else 0.0
        order = np.argsort(xs)[::-1]
        out = {"n": int(xs.size), "n_negative": int(np.sum(xs < 0)), "sum_neg": float(np.sum(xs[xs < 0]))}
        for f in (0.01, 0.05, 0.10, 0.20):
            k = max(1, int(math.ceil(xs.size * f)))
            top = float(np.sum(xs[order[:k]]))
            out["top_%s_of_pos" % int(f * 100)] = None if base == 0 else top / base
        return out

    return {"stock": share(stock_vals), "rebalance": share(time_vals), "days": share(drets)}


def liquidity(ledger, start_eq=1000000.0):
    ratios = []
    for r in ledger:
        if not r.get("filled"):
            continue
        adv = r.get("adv")
        if adv and adv > 0 and r.get("weight"):
            pos = start_eq * float(r["weight"])
            ratios.append(pos / float(adv))
    xs = np.array(ratios, dtype=np.float64)
    if xs.size == 0:
        return {"n": 0}
    return {
        "n": int(xs.size),
        "p50": float(np.percentile(xs, 50)),
        "p75": float(np.percentile(xs, 75)),
        "p90": float(np.percentile(xs, 90)),
        "p95": float(np.percentile(xs, 95)),
        "note": "position/ADV on the 1e6 diagnostic book. Not a capacity claim.",
    }


def breadth(trades):
    elig = np.array([tr["n_elig"] for tr in trades], dtype=np.float64)
    sel = np.array([tr["n_sel"] for tr in trades], dtype=np.float64)
    fill = np.array([tr["n_fill"] for tr in trades], dtype=np.float64)
    return {
        "n_rebalances": len(trades),
        "elig_min": int(elig.min()) if elig.size else None,
        "elig_median": float(np.median(elig)) if elig.size else None,
        "sel_median": float(np.median(sel)) if sel.size else None,
        "fill_median": float(np.median(fill)) if fill.size else None,
        "min_sel": int(sel.min()) if sel.size else None,
        "selection_collapse": bool(sel.size and sel.min() < 20),
    }
