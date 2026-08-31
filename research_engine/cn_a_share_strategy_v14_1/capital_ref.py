"""Independent capital engine. Does not import V14 simulate()."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, TRANSFER, stamp_duty_sell
from research_engine.cn_a_share_strategy_v14_1 import HOLD_DAYS, INITIAL, QUANTILE
from research_engine.cn_a_share_strategy_v14_1.scores import pick_lexsort


def buy_rate():
    return COMMISSION + TRANSFER + SLIPPAGE


def sell_rate(day):
    return COMMISSION + TRANSFER + SLIPPAGE + stamp_duty_sell(day)


def _limit(symbol, is_st, day):
    if is_st:
        return 0.05
    if symbol.startswith("bj."):
        return 0.30
    if symbol.startswith("sh.688"):
        return 0.20
    if symbol.startswith("sz.30"):
        return 0.20 if day >= "2020-08-24" else 0.10
    return 0.10


def exec_reason(pack, t, j):
    if int(pack["listed"][t, j]) != 1:
        return "DELISTED"
    if int(pack["tradestatus"][t, j]) != 1:
        return "SUSPENDED"
    o = float(pack["open"][t, j])
    pre = float(pack["preclose"][t, j])
    v = float(pack["volume"][t, j])
    if not np.isfinite(o) or o <= 0 or not np.isfinite(pre) or pre <= 0:
        return "MISSING_OPEN"
    if not np.isfinite(v) or v <= 0:
        return "ZERO_VOLUME"
    st = int(pack["isST"][t, j]) == 1
    if abs(o / pre - 1.0) >= _limit(pack["symbols"][j], st, pack["dates"][t]) - 0.002:
        return "LIMIT_LOCK"
    return "FILL"


def period_capital(start_eq, raws, fill_mask, exit_day):
    """Equal 1/N selected. Unfilled stays cash. No cost on unfilled."""
    n = len(fill_mask)
    w = 1.0 / float(n)
    br = buy_rate()
    fees = 0.0
    slip = 0.0
    stamp = 0.0
    n_filled = 0
    name_nets = []
    name_gross = []
    name_fees = []
    name_slip = []
    name_stamp = []
    for raw, filled in zip(raws, fill_mask):
        alloc = start_eq * w
        if not filled:
            name_nets.append(0.0)
            name_gross.append(0.0)
            name_fees.append(0.0)
            name_slip.append(0.0)
            name_stamp.append(0.0)
            continue
        n_filled += 1
        notional = alloc / (1.0 + br)
        cash_out = notional * (1.0 + br)
        sell_notional = notional * (1.0 + raw)
        st = sell_notional * stamp_duty_sell(exit_day)
        buy_fee = notional * (COMMISSION + TRANSFER)
        sell_fee = sell_notional * (COMMISSION + TRANSFER)
        buy_slip = notional * SLIPPAGE
        sell_slip = sell_notional * SLIPPAGE
        cash_in = sell_notional - sell_fee - sell_slip - st
        name_nets.append(cash_in - cash_out)
        name_gross.append(sell_notional - notional)
        name_fees.append(buy_fee + sell_fee + st)
        name_slip.append(buy_slip + sell_slip)
        name_stamp.append(st)
        fees += buy_fee + sell_fee + st
        slip += buy_slip + sell_slip
        stamp += st
    end = start_eq + float(sum(name_nets))
    return {
        "end": end,
        "ret": end / start_eq - 1.0 if start_eq else 0.0,
        "n_filled": n_filled,
        "fees": fees,
        "slippage": slip,
        "stamp": stamp,
        "unfilled_fees": 0.0,
        "name_nets": name_nets,
        "name_gross": name_gross,
        "name_fees": name_fees,
        "name_slip": name_slip,
        "name_stamp": name_stamp,
        "sum_w_filled": w * n_filled,
        "cash_frac": 1.0 - w * n_filled,
    }


def run_synthetic(n, raw, fill_mask, start=1000.0, exit_day="2020-01-15"):
    raws = [raw] * n
    rec = period_capital(start, raws, fill_mask, exit_day)
    rec["recon_ok"] = abs(rec["end"] - (start + sum(rec["name_nets"]))) < 1e-8
    rec["n_filled"] = int(sum(1 for x in fill_mask if x))
    if rec["n_filled"] == 0:
        rec["fees"] = 0.0
        rec["slippage"] = 0.0
        rec["stamp"] = 0.0
    return rec


def _decide_fills(pack, js, t0, t1, xok=None):
    raws = []
    fills = []
    reasons = []
    opens0 = []
    opens1 = []
    for j in js:
        j = int(j)
        if xok is not None:
            c0 = "FILL" if bool(xok[t0, j]) else exec_reason(pack, t0, j)
            if c0 == "FILL":
                c1 = "FILL" if bool(xok[t1, j]) else exec_reason(pack, t1, j)
            else:
                c1 = c0
            reason = c0 if c0 != "FILL" else c1
        else:
            c0 = exec_reason(pack, t0, j)
            c1 = exec_reason(pack, t1, j) if c0 == "FILL" else c0
            reason = c0 if c0 != "FILL" else c1
        filled = reason == "FILL"
        raw = 0.0
        o0 = o1 = None
        if filled:
            o0 = float(pack["open"][t0, j])
            o1 = float(pack["open"][t1, j])
            raw = o1 / o0 - 1.0
        raws.append(raw)
        fills.append(filled)
        reasons.append(reason)
        opens0.append(o0)
        opens1.append(o1)
    return raws, fills, reasons, opens0, opens1


def simulate_capital(pack, scores, elig, start, end, initial=INITIAL, xok=None, daily_mtm=True):
    """Non-overlapping 20-day capital. Return-based Path A. Independent of V14 simulate()."""
    dates = pack["dates"]
    symbols = pack["symbols"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    equity = float(initial)
    trades = []
    ledger = []
    curve = [{"date": start, "equity": equity, "cash": equity, "invested": 0.0}]
    reasons = {}
    n_empty = 0
    n_nopick = 0
    hold_ok = True
    t = i0
    while t <= i1:
        t0 = t + 1
        t1 = t + 1 + HOLD_DAYS
        if t1 >= len(dates):
            break
        js = pick_lexsort(scores[t], elig[t])
        if js is None:
            n_nopick += 1
            t += 1
            continue
        if (t1 - t0) != HOLD_DAYS:
            hold_ok = False
        raws, fills, why, o0s, o1s = _decide_fills(pack, js, t0, t1, xok)
        if not any(fills):
            n_empty += 1
            for j, reason in zip(js, why):
                reasons[reason] = reasons.get(reason, 0) + 1
            t += 1
            continue
        rec = period_capital(equity, raws, fills, dates[t1])
        w = 1.0 / float(len(js))
        if abs(w * len(js) - 1.0) > 1e-12:
            hold_ok = False
        leftover = equity * rec["cash_frac"]
        held_j = []
        held_sh = []
        br = buy_rate()
        for k, j in enumerate(js):
            j = int(j)
            amt = float(pack["amount"][t0, j])
            ledger.append(
                {
                    "signal_date": dates[t],
                    "entry": dates[t0],
                    "exit": dates[t1],
                    "symbol": symbols[j],
                    "filled": 1 if fills[k] else 0,
                    "reason": why[k],
                    "raw": raws[k],
                    "gross": rec["name_gross"][k],
                    "fees": rec["name_fees"][k],
                    "slippage": rec["name_slip"][k],
                    "stamp": rec["name_stamp"][k],
                    "net": rec["name_nets"][k],
                    "weight": w,
                    "adv": amt if np.isfinite(amt) else None,
                    "hold_days": HOLD_DAYS,
                    "entry_open": o0s[k],
                    "exit_open": o1s[k],
                    "signal_close": float(pack["close"][t, j]) if np.isfinite(float(pack["close"][t, j])) else None,
                    "entry_is_open_t1": True,
                    "exit_is_open_t1h": True,
                }
            )
            if fills[k]:
                alloc = equity * w
                notional = alloc / (1.0 + br)
                held_j.append(j)
                held_sh.append(notional / o0s[k])
            else:
                reasons[why[k]] = reasons.get(why[k], 0) + 1
        if daily_mtm and held_j:
            jj = np.asarray(held_j, dtype=np.int32)
            sh = np.asarray(held_sh, dtype=np.float64)
            block = np.array(pack["close"][t0:t1, jj], dtype=np.float64)
            o0a = np.array(pack["open"][t0, jj], dtype=np.float64)
            bad = ~np.isfinite(block) | (block <= 0)
            block = np.where(bad, o0a, block)
            invs = np.sum(block * sh, axis=1)
            for k, d in enumerate(range(t0, t1)):
                curve.append(
                    {
                        "date": dates[d],
                        "equity": leftover + float(invs[k]),
                        "cash": leftover,
                        "invested": float(invs[k]),
                    }
                )
        start_eq = equity
        equity = rec["end"]
        curve.append({"date": dates[t1], "equity": equity, "cash": equity, "invested": 0.0})
        filled_raws = [r for r, f in zip(raws, fills) if f]
        v13_net = float(np.mean(filled_raws) - (buy_rate() + sell_rate(dates[t1]))) if filled_raws else 0.0
        trades.append(
            {
                "signal_date": dates[t],
                "entry": dates[t0],
                "exit": dates[t1],
                "n_sel": int(len(js)),
                "n_fill": rec["n_filled"],
                "n_elig": int(np.sum(elig[t])),
                "raw_mean_filled": float(np.mean(filled_raws)) if filled_raws else 0.0,
                "v13_style_net": v13_net,
                "capital_ret": rec["ret"],
                "net_yuan": equity - start_eq,
                "gross_yuan": float(sum(rec["name_gross"])),
                "fees": rec["fees"],
                "slippage": rec["slippage"],
                "stamp": rec["stamp"],
                "equity": equity,
                "cash_frac": rec["cash_frac"],
                "sum_w": w * len(js),
                "spacing": t1 - t0,
                "signal_index": t,
            }
        )
        t += HOLD_DAYS
    n_sel = sum(tr["n_sel"] for tr in trades)
    n_uf = sum(tr["n_sel"] - tr["n_fill"] for tr in trades)
    trade_end = initial + sum(tr["net_yuan"] for tr in trades)
    return {
        "start": initial,
        "end": equity,
        "trades": trades,
        "ledger": ledger,
        "curve": curve,
        "hold_days_locked": hold_ok and all(tr["spacing"] == HOLD_DAYS for tr in trades),
        "unfilled_rate": (float(n_uf) / n_sel) if n_sel else None,
        "reasons": reasons,
        "n_empty_all_unfilled": n_empty,
        "n_nopick": n_nopick,
        "recon_ok": abs(equity - trade_end) < 1e-4,
        "recon_abs": abs(equity - trade_end),
        "curve_end_matches": abs(curve[-1]["equity"] - equity) < 1e-6,
    }


def simulate_capital_shares(pack, scores, elig, start, end, initial=INITIAL, xok=None):
    """Share-based Path B. Same fills as return-based; shares = notional / open(t+1)."""
    dates = pack["dates"]
    symbols = pack["symbols"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    cash = float(initial)
    equity = float(initial)
    trades = []
    ledger = []
    t = i0
    while t <= i1:
        t0 = t + 1
        t1 = t + 1 + HOLD_DAYS
        if t1 >= len(dates):
            break
        js = pick_lexsort(scores[t], elig[t])
        if js is None:
            t += 1
            continue
        raws, fills, why, o0s, o1s = _decide_fills(pack, js, t0, t1, xok)
        if not any(fills):
            t += 1
            continue
        n_sel = int(len(js))
        w = 1.0 / float(n_sel)
        br = buy_rate()
        start_eq = equity
        leftover = start_eq
        period_net = 0.0
        n_fill = 0
        for k, j in enumerate(js):
            j = int(j)
            if not fills[k]:
                ledger.append(
                    {
                        "signal_date": dates[t],
                        "symbol": symbols[j],
                        "filled": 0,
                        "net": 0.0,
                        "fees": 0.0,
                    }
                )
                continue
            o0 = o0s[k]
            o1 = o1s[k]
            alloc = start_eq * w
            notional = alloc / (1.0 + br)
            shares = notional / o0
            leftover -= notional * (1.0 + br)
            sell_notional = shares * o1
            st = sell_notional * stamp_duty_sell(dates[t1])
            sell_fee = sell_notional * (COMMISSION + TRANSFER)
            sell_slip = sell_notional * SLIPPAGE
            cash_out = notional * (1.0 + br)
            cash_in = sell_notional - sell_fee - sell_slip - st
            net = cash_in - cash_out
            period_net += net
            n_fill += 1
            ledger.append({"signal_date": dates[t], "symbol": symbols[j], "filled": 1, "net": net, "fees": 0.0})
        cash = leftover
        for k, j in enumerate(js):
            if not fills[k]:
                continue
            o1 = o1s[k]
            o0 = o0s[k]
            alloc = start_eq * w
            notional = alloc / (1.0 + br)
            shares = notional / o0
            sell_notional = shares * o1
            st = sell_notional * stamp_duty_sell(dates[t1])
            sell_fee = sell_notional * (COMMISSION + TRANSFER)
            sell_slip = sell_notional * SLIPPAGE
            cash += sell_notional - sell_fee - sell_slip - st
        equity = cash
        trades.append(
            {
                "signal_date": dates[t],
                "n_sel": n_sel,
                "n_fill": n_fill,
                "capital_ret": equity / start_eq - 1.0 if start_eq else 0.0,
                "net_yuan": equity - start_eq,
                "equity": equity,
            }
        )
        t += HOLD_DAYS
    return {
        "start": initial,
        "end": equity,
        "trades": trades,
        "ledger": ledger,
        "recon_ok": abs(equity - (initial + sum(tr["net_yuan"] for tr in trades))) < 1e-4,
    }


def capital_cagr(start, end, n_days, year_days=242.0):
    if start <= 0 or end <= 0 or n_days <= 0:
        return None
    years = n_days / year_days
    return (end / start) ** (1.0 / years) - 1.0


def ew_bench(pack, elig, start, end, signal_dates):
    """EW eligible open-to-open on the same signal dates. Same calendar as strategy."""
    dates = pack["dates"]
    eq = 1.0
    rows = []
    for sd in signal_dates:
        t = dates.index(sd)
        t0 = t + 1
        t1 = t + 1 + HOLD_DAYS
        if t1 >= len(dates):
            break
        js = np.where(elig[t])[0]
        if js.size < 100:
            continue
        a = np.array(pack["open"][t0, js], dtype=np.float64)
        b = np.array(pack["open"][t1, js], dtype=np.float64)
        good = np.isfinite(a) & np.isfinite(b) & (a > 0)
        if int(np.sum(good)) < 100:
            continue
        ret = float(np.mean(b[good] / a[good] - 1.0))
        eq *= 1.0 + ret
        rows.append({"signal_date": sd, "ret": ret, "equity": eq})
    return {"end": eq, "rows": rows, "definition": "EW_ELIGIBLE_OPEN_TO_OPEN_SAME_CALENDAR"}
