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


def top_n_period(pack, scores_t, elig_t, xok, t, equity, n=N_NAMES, boards="ALL"):
    """One period from signal t. Returns dict with net return on equity and fills, or None if no signal."""
    dates = pack["dates"]
    elig_t = elig_t & board_mask(pack["symbols"], boards)
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


def top_n_book(pack, scores, elig, xok, start, end, capital=DEFAULT_CAPITAL, n=N_NAMES, boards="ALL"):
    dates = pack["dates"]
    i0, i1 = dates.index(start), dates.index(end)
    equity, trades, t = float(capital), [], i0
    while t <= i1:
        per = top_n_period(pack, scores[t], elig[t], xok, t, equity, n, boards)
        if per is None:
            if t + 1 + HOLD >= len(dates):
                break
            t += 1
            continue
        equity += per["pnl"]
        per["equity"] = round(equity, 2)
        trades.append(per)
        t = t + 1 + HOLD
    return {"trades": trades, "total": equity / capital - 1.0, "equity_end": equity}


def summarize(book, ewm):
    tr = book["trades"]
    r = np.array([x["ret"] for x in tr])
    ew = np.array([ewm.get(x["signal_date"], np.nan) for x in tr])
    eq = np.array([x["equity"] for x in tr])
    yrs = len(tr) * (HOLD + 1) / 242.0
    dd = float(np.min(eq / np.maximum.accumulate(eq) - 1.0)) if len(eq) else None
    ex = r - ew
    ok = np.isfinite(ex)
    return {"n_periods": len(tr), "total": book["total"], "cagr": float((1 + book["total"]) ** (1 / yrs) - 1) if yrs > 0 else None,
            "maxdd": dd, "mean_ret": float(r.mean()) if len(r) else None, "mean_ew": float(np.nanmean(ew)) if len(ew) else None,
            "mean_excess_vs_ew": float(ex[ok].mean()) if ok.any() else None, "t_excess": float(ex[ok].mean() / (ex[ok].std(ddof=1) / np.sqrt(ok.sum()))) if ok.sum() > 2 else None,
            "beat_ew_periods": int((ex[ok] > 0).sum()), "mean_fill": float(np.mean([x["n_fill"] for x in tr])) if tr else None,
            "mean_cash_idle": float(np.mean([x["cash_idle_frac"] for x in tr])) if tr else None}


def main(boards="ALL", n=N_NAMES, capital=DEFAULT_CAPITAL, suffix=""):
    from research_engine.cn_a_share_alpha.pack import load_pack
    from research_engine.cn_a_share_ml_v25 import RESEARCH, VALIDATION
    from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix

    pack = load_pack()
    scores = np.load(os.path.join(OUT, "SCORES_ML1_LGBM.npy"), mmap_mode="r")
    elig, xok = eligible(pack, 20), exec_ok_matrix(pack)
    res = {"contract": "V26_1_ML1_TOP20_MANUAL_CONTRACT.md" if not suffix else "V26_2 addendum", "n_names": n, "min_fee": MIN_FEE, "capital": capital, "denied_window_read": False, "boards": boards}
    for key, (a, b) in (("research", RESEARCH), ("validation", VALIDATION)):
        bk = top_n_book(pack, scores, elig, xok, a, b, capital=capital, n=n, boards=boards)
        ew = ew_overlapping(pack, elig, xok, a, pack["dates"][pack["dates"].index(b) - HOLD - 1], HOLD)
        ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
        res[key] = summarize(bk, ewm)
        res[key + "_trades"] = [dict((k, v) for k, v in tr.items() if k != "names") for tr in bk["trades"]]
        print(TAG, key, res[key], flush=True)
    v = res["validation"]
    viable = bool(v["total"] > 0 and v["mean_excess_vs_ew"] is not None and v["mean_excess_vs_ew"] > 0)
    res["label"] = "ML1_TOP20_MANUAL_VIABLE_HISTORICAL" if viable else "ML1_TOP20_MANUAL_NOT_VIABLE"
    dump_json(os.path.join(OUT, "TOP20_MANUAL_READ%s%s.json" % ("" if boards == "ALL" else "_" + boards, suffix)), res)
    print(TAG, "DONE", boards, n, capital, res["label"], flush=True)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("boards", nargs="?", default="ALL")
    ap.add_argument("--n", type=int, default=N_NAMES)
    ap.add_argument("--capital", type=float, default=DEFAULT_CAPITAL)
    ap.add_argument("--suffix", default="")
    a = ap.parse_args()
    main(a.boards, a.n, a.capital, a.suffix)
