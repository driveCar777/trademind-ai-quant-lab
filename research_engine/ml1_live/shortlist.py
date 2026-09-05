"""V26.1 manual-execution shortlist + TOP20 shadow ledger (contract V26_1_ML1_TOP20_MANUAL_CONTRACT.md).

The shortlist is what the owner types into an ordinary brokerage account by hand. Nothing here places orders.
"""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha_v2.books import ew_overlapping
from research_engine.cn_a_share_ml_v25.top_n_book import HOLD, LOT, N_NAMES, board_mask, summarize, top_n_book
from research_engine.ml1_live import LEDGER_DIR, SIGNALS

TAG = "ML1_LIVE_TOP20"
MANUAL_CAPITAL = 100_000.0


def write_shortlist(pack, scores_t, elig_t, t, capital=MANUAL_CAPITAL, tag="SHORTLIST", boards="MAIN_CHINEXT"):
    """Top-N by score within the boards the owner is permitted to trade; lots estimated from today's close."""
    dates, symbols = pack["dates"], pack["symbols"]
    idx = np.where(elig_t & board_mask(symbols, boards) & np.isfinite(scores_t))[0]
    order = idx[np.lexsort((idx, scores_t[idx]))][::-1]
    alloc = capital / float(N_NAMES)
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
        if len(rows) >= N_NAMES:
            break
    out = {"kind": tag, "contract": "ML1_TOP20_MANUAL", "boards": boards, "signal_date": dates[t], "act": "buy at next session open, hold %d sessions, sell at open" % HOLD,
           "capital_yuan": capital, "alloc_per_name": alloc, "n_names": len(rows), "skipped_price_too_high_for_one_lot": skipped[:50],
           "names": rows, "execution": "MANUAL by owner in ordinary account; no API, no automation", "orders_sent": False,
           "note": "lots estimated from close; recompute at open: lots = floor(alloc / (100 * open)); skip if 0"}
    dump_json(os.path.join(SIGNALS, "%s_%s.json" % (tag, dates[t])), out)
    write_csv(os.path.join(SIGNALS, "%s_%s.csv" % (tag, dates[t])), ("rank", "symbol", "last_close", "lots_100_est", "est_yuan", "score"), rows)
    print(TAG, tag, dates[t], len(rows), "names", flush=True)
    return out


def update_top20_ledger(pack, S, elig, xok, first_signal_index, capital=MANUAL_CAPITAL, boards="MAIN_CHINEXT"):
    dates = pack["dates"]
    last = len(dates) - 1
    start = dates[first_signal_index]
    bk = top_n_book(pack, S, elig, xok, start, dates[last], capital=capital, boards=boards)
    ewm = {}
    ew_end_i = last - HOLD - 1
    if ew_end_i >= first_signal_index:
        ew = ew_overlapping(pack, elig, xok, start, dates[ew_end_i], HOLD)
        ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
    summ = summarize(bk, ewm) if bk["trades"] else {"n_periods": 0}
    summ.update({"contract": "ML1_TOP20_MANUAL", "boards": boards, "capital_yuan": capital, "n_names": N_NAMES, "money": "NONE (shadow)", "orders_sent": False})
    out = {"summary": summ, "periods": [dict((k, v) for k, v in tr.items() if k != "names") for tr in bk["trades"]],
           "fills_by_period": dict((tr["signal_date"], tr["names"]) for tr in bk["trades"])}
    dump_json(os.path.join(LEDGER_DIR, "LEDGER_TOP20.json"), out)
    print(TAG, "ledger closed", summ.get("n_periods", 0), flush=True)
    return out
