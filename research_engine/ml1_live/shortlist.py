"""V26.1 manual-execution shortlist + TOP20 shadow ledger (contract V26_1_ML1_TOP20_MANUAL_CONTRACT.md).

The shortlist is what the owner types into an ordinary brokerage account by hand. Nothing here places orders.
"""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha_v2.books import ew_overlapping
from research_engine.cn_a_share_ml_v25.top_n_book import HOLD, LOT, N_NAMES, UNIT_YUAN, board_mask, summarize, top_n_book
from research_engine.ml1_live import LEDGER_DIR, SIGNALS

TAG = "ML1_LIVE_TOP20"
MANUAL_CAPITAL = 100_000.0


def write_shortlist(pack, scores_t, elig_t, t, capital=MANUAL_CAPITAL, tag="SHORTLIST", boards="MAIN_CHINEXT", n=N_NAMES, max_price=None):
    """Top-N by score within the boards/price the owner can trade; lots estimated from today's close."""
    dates, symbols = pack["dates"], pack["symbols"]
    m = elig_t & board_mask(symbols, boards) & np.isfinite(scores_t)
    if max_price is not None:
        c = np.asarray(pack["close"][t], dtype=float)
        m = m & np.isfinite(c) & (c <= max_price)
    idx = np.where(m)[0]
    order = idx[np.lexsort((idx, scores_t[idx]))][::-1]
    alloc = capital / float(n)
    rows, skipped = [], []
    for j in order:
        j = int(j)
        px = float(pack["close"][t, j])
        lots = int(alloc // (LOT * px)) if np.isfinite(px) and px > 0 else 0
        if lots == 0:
            skipped.append(symbols[j])
            continue
        rows.append({"rank": len(rows) + 1, "symbol": symbols[j], "score": float(scores_t[j]), "last_close": px, "lots_100_est": lots,
                     "est_yuan": round(lots * LOT * px, 2)})
        if len(rows) >= n:
            break
    out = {"kind": tag, "contract": "ML1_TOP%d_MANUAL" % n, "boards": boards, "max_price": max_price, "signal_date": dates[t], "act": "buy at next session open, hold %d sessions, sell at open" % HOLD,
           "capital_yuan": capital, "alloc_per_name": alloc, "n_names": len(rows), "skipped_price_too_high_for_one_lot": skipped[:50],
           "names": rows, "execution": "MANUAL by owner in ordinary account; no API, no automation", "orders_sent": False,
           "note": "lots estimated from close; recompute at open: lots = floor(alloc / (100 * open)); skip if 0"}
    dump_json(os.path.join(SIGNALS, "%s_%s.json" % (tag, dates[t])), out)
    write_csv(os.path.join(SIGNALS, "%s_%s.csv" % (tag, dates[t])), ("rank", "symbol", "last_close", "lots_100_est", "est_yuan", "score"), rows)
    print(TAG, tag, dates[t], len(rows), "names", flush=True)
    return out


def write_shortlist_one_lot(pack, scores_t, elig_t, t, capital=20_000.0, exposure=0.70, boards="MAIN", max_price=100.0, tag="SHORTLIST"):
    """V26.3 ML1_ONELOT_70PCT_MAIN: scan by score, 1 lot each while 100*close <= remaining deployable cash. N emergent."""
    dates, symbols = pack["dates"], pack["symbols"]
    c = np.asarray(pack["close"][t], dtype=float)
    m = elig_t & board_mask(symbols, boards) & np.isfinite(scores_t) & np.isfinite(c) & (c <= max_price)
    idx = np.where(m)[0]
    order = idx[np.lexsort((idx, scores_t[idx]))][::-1]
    remaining, rows, skipped = exposure * capital, [], 0
    for j in order:
        j = int(j)
        px = float(c[j])
        cost = LOT * px
        if cost > remaining:
            skipped += 1
            continue
        remaining -= cost
        rows.append({"rank": len(rows) + 1, "symbol": symbols[j], "score": float(scores_t[j]), "last_close": px, "lots_100_est": 1, "est_yuan": round(cost, 2),
                     "cum_yuan": round(exposure * capital - remaining, 2)})
    out = {"kind": tag, "contract": "ML1_ONELOT_70PCT_MAIN", "boards": boards, "max_price": max_price, "exposure": exposure, "signal_date": dates[t],
           "act": "buy 1 lot each at next session open, in rank order, stop when deployable cash is used; hold %d sessions, sell at open" % HOLD,
           "capital_yuan": capital, "deployable_yuan": exposure * capital, "cash_reserve_yuan": round(remaining + (1 - exposure) * capital, 2),
           "n_names": len(rows), "skipped_unaffordable": skipped, "names": rows,
           "execution": "MANUAL by owner in ordinary account; no API, no automation", "orders_sent": False,
           "note": "estimated from close; at open re-check 100*open <= remaining deployable cash, skip if not; N is whatever fits, never chosen"}
    dump_json(os.path.join(SIGNALS, "%s_%s.json" % (tag, dates[t])), out)
    write_csv(os.path.join(SIGNALS, "%s_%s.csv" % (tag, dates[t])), ("rank", "symbol", "last_close", "lots_100_est", "est_yuan", "cum_yuan", "score"), rows)
    print(TAG, tag, dates[t], len(rows), "names one-lot", flush=True)
    return out


def write_shortlist_eq_money(pack, scores_t, elig_t, t, capital=20_000.0, exposure=0.70, boards="MAIN", max_price=100.0, tag="SHORTLIST", topup=False):
    """V26.4 ML1_EQMONEY_70PCT_MAIN: N = floor(exposure*capital/2000); 2000 yuan per name; lots from close (recheck at open).
    topup=True (V26.6): second pass fills the exposure budget with extra lots on the same names, in score order, 1 lot per cycle."""
    dates, symbols = pack["dates"], pack["symbols"]
    c = np.asarray(pack["close"][t], dtype=float)
    m = elig_t & board_mask(symbols, boards) & np.isfinite(scores_t) & np.isfinite(c) & (c <= max_price)
    idx = np.where(m)[0]
    order = idx[np.lexsort((idx, scores_t[idx]))][::-1]
    n = int((exposure * capital) // UNIT_YUAN)
    rows, skipped = [], 0
    for j in order:
        j = int(j)
        px = float(c[j])
        lots = int(UNIT_YUAN // (LOT * px)) if px > 0 else 0
        if lots == 0:
            skipped += 1
            continue
        rows.append({"rank": len(rows) + 1, "symbol": symbols[j], "score": float(scores_t[j]), "last_close": px, "lots_100_est": lots, "est_yuan": round(lots * LOT * px, 2)})
        if len(rows) >= n:
            break
    if topup and rows:
        budget = exposure * capital - sum(r["est_yuan"] for r in rows)
        while True:
            added = False
            for r in rows:
                lc = LOT * r["last_close"]
                if lc <= budget:
                    r["lots_100_est"] += 1
                    r["est_yuan"] = round(r["est_yuan"] + lc, 2)
                    budget -= lc
                    added = True
            if not added:
                break
    act = ("next session open: buy lots=floor(2000/(100*open)) of each; then fill the remaining %d%% budget with extra lots on the same names in rank order, 1 lot per pass; "
           "hold %d sessions; sell at open; if sell blocked (limit-down/suspended) keep trying next opens" % (round(exposure * 100), HOLD)) if topup else \
          ("next session open: buy lots=floor(2000/(100*open)) of each; hold %d sessions; sell at open; if sell blocked (limit-down/suspended) keep trying next opens" % HOLD)
    out = {"kind": tag, "contract": "ML1_EQMONEY_%dPCT_%sMAIN" % (round(exposure * 100), "TOPUP_" if topup else ""), "boards": boards, "max_price": max_price, "exposure": exposure, "unit_yuan": UNIT_YUAN, "signal_date": dates[t],
           "topup": topup, "est_invested_yuan": round(sum(r["est_yuan"] for r in rows), 2), "act": act,
           "capital_yuan": capital, "n_target": n, "n_names": len(rows), "skipped_price_too_high_for_2000": skipped, "names": rows,
           "execution": "MANUAL by owner in ordinary account; no API, no automation", "orders_sent": False}
    dump_json(os.path.join(SIGNALS, "%s_%s.json" % (tag, dates[t])), out)
    write_csv(os.path.join(SIGNALS, "%s_%s.csv" % (tag, dates[t])), ("rank", "symbol", "last_close", "lots_100_est", "est_yuan", "score"), rows)
    print(TAG, tag, dates[t], len(rows), "names eq-money", flush=True)
    return out


def update_top20_ledger(pack, S, elig, xok, first_signal_index, capital=MANUAL_CAPITAL, boards="MAIN_CHINEXT", n=N_NAMES, max_price=None, one_lot=False, exposure=0.70, eq_money=False, topup=False):
    dates = pack["dates"]
    last = len(dates) - 1
    start = dates[first_signal_index]
    bk = top_n_book(pack, S, elig, xok, start, dates[last], capital=capital, n=n, boards=boards, max_price=max_price, one_lot=one_lot, exposure=exposure, eq_money=eq_money, topup=topup)
    ewm = {}
    ew_end_i = last - HOLD - 1
    if ew_end_i >= first_signal_index:
        ew = ew_overlapping(pack, elig, xok, start, dates[ew_end_i], HOLD)
        ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
    summ = summarize(bk, ewm) if bk["trades"] else {"n_periods": 0}
    if eq_money and topup:
        contract, gate = "ML1_EQMONEY_%dPCT_TOPUP_MAIN" % round(exposure * 100), "VIABLE_HISTORICAL (V26.6 single read 2026-09-06: validation +33.9%, t 2.56)"
    elif eq_money:
        contract, gate = "ML1_EQMONEY_%dPCT_MAIN" % round(exposure * 100), "VIABLE_HISTORICAL (V26.4 70%% / V26.5 80%% single reads 2026-09-06)"
    elif one_lot:
        contract, gate = "ML1_ONELOT_%dPCT_MAIN" % round(exposure * 100), "NOT_VIABLE (V26.3 single read 2026-09-05)"
    else:
        contract, gate = "ML1_TOP%d_MANUAL" % n, None
    summ.update({"contract": contract, "boards": boards, "max_price": max_price, "capital_yuan": capital, "n_names": ("EMERGENT" if (one_lot or eq_money) else n),
                 "exposure": (exposure if (one_lot or eq_money) else 1.0), "money": "NONE (shadow)", "orders_sent": False, "historical_gate": gate})
    out = {"summary": summ, "periods": [dict((k, v) for k, v in tr.items() if k != "names") for tr in bk["trades"]],
           "fills_by_period": dict((tr["signal_date"], tr["names"]) for tr in bk["trades"])}
    dump_json(os.path.join(LEDGER_DIR, "LEDGER_TOP20.json"), out)
    print(TAG, "ledger closed", summ.get("n_periods", 0), flush=True)
    return out
