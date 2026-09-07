"""ML7 shadow ledger on the same signal chain as ML1 (every HOLD_DAYS+1 sessions after CHAIN_ANCHOR_SIGNAL). Settled with the
frozen cost model via capital_book. Writes LEDGER_ML7.json/csv only. The contract read (>= 24 closed periods) is reported as a
countdown, never as a verdict, here."""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha_v2.books import capital_book, ew_overlapping
from research_engine.ml1_live import CHAIN_ANCHOR_SIGNAL, DEFAULT_CAPITAL, HOLD_DAYS
from research_engine.ml1_live.ledger import chain_signal_indices
from research_engine.ml7_live import LEDGER_DIR, MIN_PERIODS_TO_READ, ML7_ID
from research_engine.ml7_live.score import score_session

TAG = "ML7_LEDGER"


def update_ledger(pack, feats, elig, xok, capital=DEFAULT_CAPITAL, ml1_scores=None):
    dates = pack["dates"]
    T, N = len(dates), len(pack["symbols"])
    last = T - 1
    sig_idx = chain_signal_indices(dates, last)
    if not sig_idx:
        return {"summary": {"state": "WAITING_FIRST_SIGNAL"}, "periods": []}
    S = np.full((T, N), np.nan, dtype=np.float32)
    signals = {}
    for t in sig_idx:
        sig, sc = score_session(pack, feats, elig, xok, t, capital, tag="SIGNAL_ML7")
        S[t] = sc
        signals[dates[t]] = sig
    start = dates[sig_idx[0]]
    closed = capital_book(pack, S, elig, xok, start, dates[last], HOLD_DAYS, initial=capital)
    ew_end_i = last - HOLD_DAYS - 1
    ewm = {}
    if ew_end_i >= sig_idx[0]:
        ew = ew_overlapping(pack, elig, xok, start, dates[ew_end_i], HOLD_DAYS)
        ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
    closed_by_signal = dict((tr["signal_date"], tr) for tr in closed["trades"])
    periods = []
    for t in sig_idx:
        d = dates[t]
        sig = signals[d]
        tr = closed_by_signal.get(d)
        overlap = None
        if ml1_scores is not None and np.isfinite(ml1_scores[t]).any():
            mine = set(n["symbol"] for n in sig["names"])
            k = len(mine)
            top_ml1 = np.argsort(-np.where(np.isfinite(ml1_scores[t]), ml1_scores[t], -np.inf))[:k] if k else []
            overlap = round(len(mine & set(pack["symbols"][j] for j in top_ml1)) / max(k, 1), 3)
        if tr is not None:
            periods.append({"status": "CLOSED", "signal_date": d, "entry": tr["entry"], "exit": tr["exit"], "n_sel": tr["n_sel"], "n_fill": tr["n_fill"],
                            "capital_ret": tr["capital_ret"], "ew_ret": ewm.get(d), "lo_minus_ew": (tr["capital_ret"] - ewm[d]) if d in ewm else None,
                            "net_yuan": tr["net_yuan"], "equity": tr["equity"], "name_overlap_with_ml1": overlap})
        else:
            entry = dates[t + 1] if t + 1 <= last else None
            periods.append({"status": "OPEN" if entry else "PENDING_ENTRY", "signal_date": d, "entry": entry,
                            "exit_expected": dates[t + 1 + HOLD_DAYS] if t + 1 + HOLD_DAYS <= last else "%d sessions after %s" % (HOLD_DAYS, entry or d),
                            "n_sel": sig["n_selected"], "model_refit_date": sig["model_refit_date"], "name_overlap_with_ml1": overlap})
    lo_ew = [p["lo_minus_ew"] for p in periods if p["status"] == "CLOSED" and p.get("lo_minus_ew") is not None]
    n_closed = len(lo_ew)
    summary = {"id": ML7_ID, "state": "ACCUMULATING" if n_closed < MIN_PERIODS_TO_READ else "READ_ALLOWED_ONCE",
               "n_periods_closed": n_closed, "periods_until_read": max(MIN_PERIODS_TO_READ - n_closed, 0),
               "n_periods_open": sum(1 for p in periods if p["status"] != "CLOSED"),
               "total_capital_ret": closed["total"] if closed.get("trades") else None,
               "equity": closed["trades"][-1]["equity"] if closed.get("trades") else capital,
               "n_lo_beat_ew": sum(1 for x in lo_ew if x > 0), "capital_yuan": capital, "chain_anchor": CHAIN_ANCHOR_SIGNAL,
               "next_signal_date": dates[sig_idx[-1] + HOLD_DAYS + 1] if sig_idx[-1] + HOLD_DAYS + 1 <= last else "%d sessions after %s" % (HOLD_DAYS + 1, dates[sig_idx[-1]]),
               "money": "NONE (shadow, output-only)", "orders_sent": False, "affects_shortlist": False,
               "read_rule": "one read after >= %d closed periods: excess vs EW t >= 2, LO20 capital > 0, excess corr vs ML1 < 0.90" % MIN_PERIODS_TO_READ}
    out = {"summary": summary, "periods": periods}
    dump_json(os.path.join(LEDGER_DIR, "LEDGER_ML7.json"), out)
    cols = ("status", "signal_date", "entry", "exit", "n_sel", "n_fill", "capital_ret", "ew_ret", "lo_minus_ew", "equity", "name_overlap_with_ml1")
    write_csv(os.path.join(LEDGER_DIR, "LEDGER_ML7.csv"), cols, [dict((k, p.get(k)) for k in cols) for p in periods])
    print(TAG, summary["state"], "closed", n_closed, "open", summary["n_periods_open"], "next", summary["next_signal_date"], flush=True)
    out["_scores_matrix"] = S
    return out
