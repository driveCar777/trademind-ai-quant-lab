"""V26.1 ML1_TOP20_MANUAL book: top-N names, lot rounding, min commission. Contract docs/research_engine/V26_1_ML1_TOP20_MANUAL_CONTRACT.md.

Shared by the historical read (frozen ML1 scores, research+validation only) and the V29 forward shadow ledger.
"""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.cost import COMMISSION, SLIPPAGE, TRANSFER, stamp_duty_sell
from research_engine.cn_a_share_alpha_v2.books import ew_overlapping
from research_engine.cn_a_share_ml_v25 import OUT
from research_engine.cn_a_share_strategy_v14_1.capital_ref import exec_reason

N_NAMES = 20
MIN_FEE = 5.0
LOT = 100
DEFAULT_CAPITAL = 100_000.0
HOLD = 20
TAG = "V26_1_TOP20"


def _fee(notional):
    return max(MIN_FEE, notional * COMMISSION) + notional * TRANSFER


BOARD_SETS = {
    "ALL": None,
    "MAIN_CHINEXT": ("sh.60", "sz.00", "sz.30"),  # no STAR (sh.688), no BSE (bj.)
    "MAIN": ("sh.60", "sz.00"),
}


def board_mask(symbols, boards):
    pref = BOARD_SETS[boards]
    if pref is None:
        return np.ones(len(symbols), dtype=bool)
    return np.array([s.startswith(pref) for s in symbols], dtype=bool)


def top_n_period(pack, scores_t, elig_t, xok, t, equity, n=N_NAMES, boards="ALL", max_price=None):
    """One period from signal t. Returns dict with net return on equity and fills, or None if no signal."""
    dates = pack["dates"]
    elig_t = elig_t & board_mask(pack["symbols"], boards)
    if max_price is not None:
        c = np.asarray(pack["close"][t], dtype=float)
        elig_t = elig_t & np.isfinite(c) & (c <= max_price)
    t0, t1 = t + 1, t + 1 + HOLD
    if t1 >= len(dates):
        return None
    idx = np.where(elig_t & np.isfinite(scores_t))[0]
    if idx.size < 200:
        return None
    order = idx[np.lexsort((idx, scores_t[idx]))][::-1]  # score desc, symbol index asc on ties
    alloc = equity / float(n)
    picks, skipped_lot = [], 0
    for j in order:
        j = int(j)
        o0 = float(pack["open"][t0, j])
        if not np.isfinite(o0) or o0 <= 0:
            picks.append((j, 0, "NO_OPEN"))
        else:
            lots = int(alloc // (LOT * o0))
            if lots == 0:
                skipped_lot += 1
                continue
            picks.append((j, lots, None))
        if len(picks) >= n:
            break
    pnl, invested, n_fill, names = 0.0, 0.0, 0, []
    for j, lots, pre in picks:
        reason = pre or ("FILL" if bool(xok[t0, j]) else exec_reason(pack, t0, j))
        if reason == "FILL":
            reason = "FILL" if bool(xok[t1, j]) else exec_reason(pack, t1, j)
        if reason != "FILL":
            names.append({"symbol": pack["symbols"][j], "lots": lots, "status": reason, "net": 0.0})
            continue
        o0, o1 = float(pack["open"][t0, j]), float(pack["open"][t1, j])
        shares = lots * LOT
        buy_px = o0 * (1.0 + SLIPPAGE)
        sell_px = o1 * (1.0 - SLIPPAGE)
        cost_in = shares * buy_px
        proceeds = shares * sell_px
        fees = _fee(cost_in) + _fee(proceeds) + proceeds * stamp_duty_sell(dates[t1])
        net = proceeds - cost_in - fees
        pnl += net
        invested += cost_in
        n_fill += 1
        names.append({"symbol": pack["symbols"][j], "lots": lots, "status": "FILL", "net": round(net, 2)})
    return {"signal_date": dates[t], "entry": dates[t0], "exit": dates[t1], "n_sel": len(picks), "n_fill": n_fill, "skipped_no_lot": skipped_lot,
            "invested": round(invested, 2), "cash_idle_frac": round(1.0 - invested / equity, 4), "pnl": round(pnl, 2), "ret": pnl / equity, "names": names}


def one_lot_period(pack, scores_t, elig_t, xok, t, equity, exposure=0.70, boards="MAIN", max_price=100.0):
    """V26.3: scan by score; buy exactly 1 lot if 100*open <= remaining deployable cash (exposure*equity), else skip. N is emergent."""
    dates = pack["dates"]
    elig_t = elig_t & board_mask(pack["symbols"], boards)
    c = np.asarray(pack["close"][t], dtype=float)
    elig_t = elig_t & np.isfinite(c) & (c <= max_price)
    t0, t1 = t + 1, t + 1 + HOLD
    if t1 >= len(dates):
        return None
    idx = np.where(elig_t & np.isfinite(scores_t))[0]
    if idx.size < 200:
        return None
    order = idx[np.lexsort((idx, scores_t[idx]))][::-1]
    remaining = exposure * equity
    picks, skipped = [], 0
    for j in order:
        j = int(j)
        o0 = float(pack["open"][t0, j])
        if not np.isfinite(o0) or o0 <= 0:
            continue
        cost = LOT * o0 * (1.0 + SLIPPAGE)
        if cost > remaining:
            skipped += 1
            continue
        picks.append((j, 1, None))
        remaining -= cost
    pnl, invested, n_fill, names = 0.0, 0.0, 0, []
    for j, lots, pre in picks:
        reason = "FILL" if bool(xok[t0, j]) else exec_reason(pack, t0, j)
        if reason == "FILL":
            reason = "FILL" if bool(xok[t1, j]) else exec_reason(pack, t1, j)
        if reason != "FILL":
            names.append({"symbol": pack["symbols"][j], "lots": 1, "status": reason, "net": 0.0})
            continue
        o0, o1 = float(pack["open"][t0, j]), float(pack["open"][t1, j])
        cost_in = LOT * o0 * (1.0 + SLIPPAGE)
        proceeds = LOT * o1 * (1.0 - SLIPPAGE)
        fees = _fee(cost_in) + _fee(proceeds) + proceeds * stamp_duty_sell(dates[t1])
        net = proceeds - cost_in - fees
        pnl += net
        invested += cost_in
        n_fill += 1
        names.append({"symbol": pack["symbols"][j], "lots": 1, "status": "FILL", "net": round(net, 2), "lot_yuan": round(cost_in, 2)})
    return {"signal_date": dates[t], "entry": dates[t0], "exit": dates[t1], "n_sel": len(picks), "n_fill": n_fill, "skipped_no_lot": skipped,
            "invested": round(invested, 2), "cash_idle_frac": round(1.0 - invested / equity, 4), "pnl": round(pnl, 2), "ret": pnl / equity, "names": names}


UNIT_YUAN = 2000.0
EXIT_CARRY_MAX = 10


def _exit_fill(pack, xok, t1, j):
    """V26.4 realistic exit: if blocked at planned open, carry forward day by day (max EXIT_CARRY_MAX); else mark at last close (STUCK)."""
    dates = pack["dates"]
    for k in range(EXIT_CARRY_MAX + 1):
        tk = t1 + k
        if tk >= len(dates):
            return None, None, "END_OF_DATA"
        if bool(xok[tk, j]):
            return float(pack["open"][tk, j]), dates[tk], ("FILL" if k == 0 else "FILL_CARRY_%d" % k)
    tk = min(t1 + EXIT_CARRY_MAX, len(dates) - 1)
    c = float(pack["close"][tk, j])
    return (c if np.isfinite(c) and c > 0 else None), dates[tk], "STUCK"


def eq_money_period(pack, scores_t, elig_t, xok, t, equity, exposure=0.70, unit=UNIT_YUAN, boards="MAIN", max_price=100.0, hold=HOLD):
    """V26.4: N = floor(exposure*equity/unit); equal money per name; lots = floor(unit/(100*open)); realistic carried exit."""
    dates = pack["dates"]
    elig_t = elig_t & board_mask(pack["symbols"], boards)
    c = np.asarray(pack["close"][t], dtype=float)
    elig_t = elig_t & np.isfinite(c) & (c <= max_price)
    t0, t1 = t + 1, t + 1 + hold
    if t1 >= len(dates):
        return None
    idx = np.where(elig_t & np.isfinite(scores_t))[0]
    if idx.size < 200:
        return None
    n = int((exposure * equity) // unit)
    if n < 1:
        return None
    order = idx[np.lexsort((idx, scores_t[idx]))][::-1]
    picks, skipped = [], 0
    for j in order:
        j = int(j)
        o0 = float(pack["open"][t0, j])
        if not np.isfinite(o0) or o0 <= 0:
            continue
        lots = int(unit // (LOT * o0 * (1.0 + SLIPPAGE)))
        if lots == 0:
            skipped += 1
            continue
        picks.append((j, lots))
        if len(picks) >= n:
            break
    pnl, pnl_v14, invested, n_fill, n_carry, n_stuck, names = 0.0, 0.0, 0.0, 0, 0, 0, []
    for j, lots in picks:
        r0 = "FILL" if bool(xok[t0, j]) else exec_reason(pack, t0, j)
        if r0 != "FILL":
            names.append({"symbol": pack["symbols"][j], "lots": lots, "status": r0, "net": 0.0})
            continue
        o0 = float(pack["open"][t0, j])
        shares = lots * LOT
        cost_in = shares * o0 * (1.0 + SLIPPAGE)
        px1, exit_day, r1 = _exit_fill(pack, xok, t1, j)
        if px1 is None:
            names.append({"symbol": pack["symbols"][j], "lots": lots, "status": r1, "net": 0.0})
            continue
        proceeds = shares * px1 * (1.0 - SLIPPAGE)
        fees = _fee(cost_in) + _fee(proceeds) + proceeds * stamp_duty_sell(exit_day)
        net = proceeds - cost_in - fees
        pnl += net
        invested += cost_in
        n_fill += 1
        if r1.startswith("FILL_CARRY"):
            n_carry += 1
        if r1 == "STUCK":
            n_stuck += 1
        # V14.1 convention diagnostic: blocked exit => trade dropped entirely
        if r1 == "FILL":
            pnl_v14 += net
        names.append({"symbol": pack["symbols"][j], "lots": lots, "status": r1, "exit": exit_day, "net": round(net, 2), "yuan": round(cost_in, 2)})
    return {"signal_date": dates[t], "entry": dates[t0], "exit": dates[t1], "n_target": n, "n_sel": len(picks), "n_fill": n_fill, "n_exit_carry": n_carry, "n_stuck": n_stuck,
            "skipped_no_lot": skipped, "invested": round(invested, 2), "cash_idle_frac": round(1.0 - invested / equity, 4), "pnl": round(pnl, 2), "ret": pnl / equity,
            "pnl_v14_convention": round(pnl_v14, 2), "names": names}


def top_n_book(pack, scores, elig, xok, start, end, capital=DEFAULT_CAPITAL, n=N_NAMES, boards="ALL", max_price=None, one_lot=False, exposure=0.70, eq_money=False, hold=HOLD):
    dates = pack["dates"]
    i0, i1 = dates.index(start), dates.index(end)
    equity, trades, t = float(capital), [], i0
    while t <= i1:
        if eq_money:
            per = eq_money_period(pack, scores[t], elig[t], xok, t, equity, exposure, UNIT_YUAN, boards, max_price, hold)
        elif one_lot:
            per = one_lot_period(pack, scores[t], elig[t], xok, t, equity, exposure, boards, max_price)
        else:
            per = top_n_period(pack, scores[t], elig[t], xok, t, equity, n, boards, max_price)
        if per is None:
            if t + 1 + hold >= len(dates):
                break
            t += 1
            continue
        equity += per["pnl"]
        per["equity"] = round(equity, 2)
        trades.append(per)
        t = t + 1 + hold
    return {"trades": trades, "total": equity / capital - 1.0, "equity_end": equity}


def summarize(book, ewm, hold=HOLD):
    tr = book["trades"]
    r = np.array([x["ret"] for x in tr])
    ew = np.array([ewm.get(x["signal_date"], np.nan) for x in tr])
    eq = np.array([x["equity"] for x in tr])
    yrs = len(tr) * (hold + 1) / 242.0
    dd = float(np.min(eq / np.maximum.accumulate(eq) - 1.0)) if len(eq) else None
    ex = r - ew
    ok = np.isfinite(ex)
    return {"n_periods": len(tr), "total": book["total"], "cagr": float((1 + book["total"]) ** (1 / yrs) - 1) if yrs > 0 else None,
            "maxdd": dd, "mean_ret": float(r.mean()) if len(r) else None, "mean_ew": float(np.nanmean(ew)) if len(ew) else None,
            "mean_excess_vs_ew": float(ex[ok].mean()) if ok.any() else None, "t_excess": float(ex[ok].mean() / (ex[ok].std(ddof=1) / np.sqrt(ok.sum()))) if ok.sum() > 2 else None,
            "beat_ew_periods": int((ex[ok] > 0).sum()), "mean_fill": float(np.mean([x["n_fill"] for x in tr])) if tr else None,
            "mean_cash_idle": float(np.mean([x["cash_idle_frac"] for x in tr])) if tr else None}


def main(boards="ALL", n=N_NAMES, capital=DEFAULT_CAPITAL, max_price=None, name=None, one_lot=False, exposure=0.70, contract=None, eq_money=False):
    from research_engine.cn_a_share_alpha.pack import load_pack
    from research_engine.cn_a_share_ml_v25 import RESEARCH, VALIDATION
    from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix

    pack = load_pack()
    scores = np.load(os.path.join(OUT, "SCORES_ML1_LGBM.npy"), mmap_mode="r")
    elig, xok = eligible(pack, 20), exec_ok_matrix(pack)
    contract = contract or ("V26_2_ML1_TOP10_20K_MAIN_CONTRACT.md" if name else "V26_1_ML1_TOP20_MANUAL_CONTRACT.md")
    res = {"contract": contract, "n_names": ("EMERGENT" if (one_lot or eq_money) else n), "one_lot": one_lot, "eq_money": eq_money, "unit_yuan": (UNIT_YUAN if eq_money else None),
           "exposure": (exposure if (one_lot or eq_money) else 1.0), "min_fee": MIN_FEE, "capital": capital, "max_price": max_price, "denied_window_read": False, "boards": boards}
    for key, (a, b) in (("research", RESEARCH), ("validation", VALIDATION)):
        bk = top_n_book(pack, scores, elig, xok, a, b, capital=capital, n=n, boards=boards, max_price=max_price, one_lot=one_lot, exposure=exposure, eq_money=eq_money)
        ew = ew_overlapping(pack, elig, xok, a, pack["dates"][pack["dates"].index(b) - HOLD - 1], HOLD)
        ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
        res[key] = summarize(bk, ewm)
        if eq_money:
            tr = bk["trades"]
            res[key]["exit_carry_trades"] = int(sum(x["n_exit_carry"] for x in tr))
            res[key]["stuck_trades"] = int(sum(x["n_stuck"] for x in tr))
            res[key]["fills"] = int(sum(x["n_fill"] for x in tr))
            eq_v14 = capital
            for x in tr:
                eq_v14 += x["pnl_v14_convention"] * (eq_v14 / (x["equity"] - x["pnl"]))  # scale to that path's equity
            res[key]["total_v14_exit_convention_DIAG"] = eq_v14 / capital - 1.0
        res[key + "_trades"] = [dict((k, v) for k, v in tr.items() if k != "names") for tr in bk["trades"]]
        print(TAG, key, res[key], flush=True)
    v = res["validation"]
    viable = bool(v["total"] > 0 and v["mean_excess_vs_ew"] is not None and v["mean_excess_vs_ew"] > 0)
    stem = name or "ML1_TOP20_MANUAL"
    res["label"] = stem + ("_VIABLE_HISTORICAL" if viable else "_NOT_VIABLE")
    fn = ("%s_READ.json" % name) if name else ("TOP20_MANUAL_READ%s.json" % ("" if boards == "ALL" else "_" + boards))
    dump_json(os.path.join(OUT, fn), res)
    print(TAG, "DONE", boards, res["label"], flush=True)


def recent_diag(name, exposure, boards="MAIN", max_price=100.0, capital=20_000.0):
    """Diagnostic only, no decision: the owner-constrained shell on the window V28 already consumed (2024-03..2026-08), REFIT_240 gate scores."""
    from research_engine.cn_a_share_alpha.pack import load_pack
    from research_engine.cn_a_share_ml_v25 import DENIED
    from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix

    pack = load_pack()
    dates = pack["dates"]
    scores = np.load(os.path.join(OUT, "SCORES_FINAL_OOS_GATE_REFIT240.npy"), mmap_mode="r")
    assert scores.shape[0] == len(dates), "scores/pack misaligned"
    elig, xok = eligible(pack, 20), exec_ok_matrix(pack)
    c = np.asarray(pack["close"], dtype=float)
    elig_shell = elig & board_mask(pack["symbols"], boards)[None, :] & np.isfinite(c) & (c <= max_price)
    i_start = next(i for i, d in enumerate(dates) if d >= DENIED[0])
    i_last_sig = len(dates) - 1 - HOLD - 1
    end_sig = dates[i_last_sig]
    bk = top_n_book(pack, scores, elig, xok, dates[i_start], end_sig, capital=capital, boards=boards, max_price=max_price, eq_money=True, exposure=exposure)
    ew = ew_overlapping(pack, elig_shell, xok, dates[i_start], end_sig, HOLD)
    ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
    out = {"contract": name, "kind": "DIAGNOSTIC_REPORT_NO_DECISION", "scores": "SCORES_FINAL_OOS_GATE_REFIT240 (V28 gate)", "benchmark": "EW of eligible %s close<=%.0f" % (boards, max_price),
           "note": "window already consumed by V28; reported on owner request; nothing tuned; not a gate"}
    tr = bk["trades"]

    def _slice(label, since):
        sub = [x for x in tr if x["signal_date"] >= since]
        if not sub:
            return None
        eq0 = sub[0]["equity"] - sub[0]["pnl"]
        b = {"trades": sub, "total": sub[-1]["equity"] / eq0 - 1.0}
        s = summarize(b, ewm)
        s["from"] = sub[0]["signal_date"]
        return s

    out["full_%s.." % DENIED[0]] = _slice("full", DENIED[0])
    out["last_12m_from_2025-08"] = _slice("12m", "2025-08-01")
    out["last_6m_from_2026-02"] = _slice("6m", "2026-02-01")
    out["periods"] = [dict((k, v) for k, v in x.items() if k != "names") for x in tr]
    dump_json(os.path.join(OUT, "%s_RECENT_DIAG.json" % name), out)
    for k in ("full_%s.." % DENIED[0], "last_12m_from_2025-08", "last_6m_from_2026-02"):
        s = out[k]
        print(TAG, "DIAG", k, s and {kk: (round(s[kk], 4) if isinstance(s[kk], float) else s[kk]) for kk in ("n_periods", "total", "maxdd", "mean_ret", "mean_ew", "mean_excess_vs_ew", "t_excess", "beat_ew_periods")}, flush=True)
    return out


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "V26_5":
        # V26.5: V26.4 with 80% exposure (owner 00:30). Single read + one recent-window diagnostic (no decision).
        if os.path.isfile(os.path.join(OUT, "ML1_EQMONEY_80PCT_MAIN_READ.json")):
            raise SystemExit("V26.5 already read once; refusing (single-read contract)")
        main("MAIN", capital=20_000.0, max_price=100.0, name="ML1_EQMONEY_80PCT_MAIN", eq_money=True, exposure=0.80, contract="V26_5_ML1_EQMONEY_80PCT_MAIN_CONTRACT.md")
        recent_diag("ML1_EQMONEY_80PCT_MAIN", 0.80)
    elif len(sys.argv) > 1 and sys.argv[1] == "V26_4":
        # V26.4: main board, close <= 100, 70% exposure, equal money 2000/name (N = floor(0.7*equity/2000)), realistic carried exit. Single read.
        if os.path.isfile(os.path.join(OUT, "ML1_EQMONEY_70PCT_MAIN_READ.json")):
            raise SystemExit("V26.4 already read once; refusing (single-read contract)")
        main("MAIN", capital=20_000.0, max_price=100.0, name="ML1_EQMONEY_70PCT_MAIN", eq_money=True, exposure=0.70, contract="V26_4_ML1_EQMONEY_70PCT_MAIN_CONTRACT.md")
    elif len(sys.argv) > 1 and sys.argv[1] == "V26_3":
        # V26.3: main board, close <= 100, 70% exposure fixed by owner, exactly 1 lot per name, N emergent. Single read.
        if os.path.isfile(os.path.join(OUT, "ML1_ONELOT_70PCT_MAIN_READ.json")):
            raise SystemExit("V26.3 already read once; refusing (single-read contract)")
        main("MAIN", capital=20_000.0, max_price=100.0, name="ML1_ONELOT_70PCT_MAIN", one_lot=True, exposure=0.70, contract="V26_3_ML1_ONELOT_70PCT_MAIN_CONTRACT.md")
    elif len(sys.argv) > 1 and sys.argv[1] == "V26_2":
        # V26.2: owner's real constraints — main board, ¥20k, price <= ¥20, N = 20000 / 2000 = 10
        main("MAIN", n=10, capital=20_000.0, max_price=20.0, name="ML1_TOP10_20K_MAIN")
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else "ALL")
