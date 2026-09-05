"""Shadow ledger: the V26 strategy's forward record, settled on real opens with the frozen cost model. No money, no orders.

Period chain continues V28: signal every HOLD_DAYS+1 sessions after CHAIN_ANCHOR_SIGNAL (signal t -> buy open t+1 -> sell open t+21).
Closed periods are settled with cn_a_share_alpha_v2.books.capital_book (identical to every research book). Open periods show fills only.
V26 rules evaluated automatically: PAUSE_REVIEW (12-period rolling LO-EW < -8%), RETIRE (24 consecutive LO-EW <= 0).
"""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha_v2.books import capital_book, ew_overlapping
from research_engine.ml1_live import (
    CHAIN_ANCHOR_SIGNAL, DEFAULT_CAPITAL, HOLD_DAYS, LEDGER_DIR, PAUSE_ROLLING_PERIODS, PAUSE_THRESHOLD, RETIRE_CONSECUTIVE, ensure_live,
)
from research_engine.ml1_live.score import score_session

TAG = "ML1_LIVE_LEDGER"


def chain_signal_indices(dates, last_index):
    """Signal sessions after the V28 anchor, every HOLD_DAYS+1 sessions, up to last_index."""
    i = dates.index(CHAIN_ANCHOR_SIGNAL)
    out = []
    i += HOLD_DAYS + 1
    while i <= last_index:
        out.append(i)
        i += HOLD_DAYS + 1
    return out


def update_ledger(pack, feats, elig, xok, capital=DEFAULT_CAPITAL):
    ensure_live()
    dates = pack["dates"]
    T, N = len(dates), len(pack["symbols"])
    last = T - 1
    sig_idx = chain_signal_indices(dates, last)
    if not sig_idx:
        return {"periods": [], "note": "first chain signal not yet reached", "next_signal_date": None}
    S = np.full((T, N), np.nan, dtype=np.float32)
    signals = {}
    for t in sig_idx:
        sig, sc = score_session(pack, feats, elig, xok, t, capital, tag="SHADOW")
        S[t] = sc
        signals[dates[t]] = sig
    start = dates[sig_idx[0]]
    closed = capital_book(pack, S, elig, xok, start, dates[last], HOLD_DAYS, initial=capital)
    ew_end_i = last - HOLD_DAYS - 1
    ewm = {}
    if ew_end_i >= sig_idx[0]:
        ew = ew_overlapping(pack, elig, xok, start, dates[ew_end_i], HOLD_DAYS)
        ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
    periods = []
    closed_by_signal = dict((tr["signal_date"], tr) for tr in closed["trades"])
    for t in sig_idx:
        d = dates[t]
        sig = signals[d]
        tr = closed_by_signal.get(d)
        if tr is not None:
            lo_ew = tr["capital_ret"] - ewm[d] if d in ewm else None
            periods.append({"status": "CLOSED", "signal_date": d, "entry": tr["entry"], "exit": tr["exit"], "n_sel": tr["n_sel"], "n_fill": tr["n_fill"],
                            "capital_ret": tr["capital_ret"], "ew_ret": ewm.get(d), "lo_minus_ew": lo_ew, "net_yuan": tr["net_yuan"], "equity": tr["equity"]})
        else:
            entry = dates[t + 1] if t + 1 <= last else None
            fills = int(sum(1 for n in sig["names"] if entry is not None and bool(xok[t + 1, pack["symbols"].index(n["symbol"])]))) if entry else None
            exit_expected = dates[t + 1 + HOLD_DAYS] if t + 1 + HOLD_DAYS <= last else "%d sessions after %s" % (HOLD_DAYS, entry or d)
            periods.append({"status": "OPEN" if entry else "PENDING_ENTRY", "signal_date": d, "entry": entry, "exit_expected": exit_expected,
                            "n_sel": sig["n_selected"], "n_fill_entry": fills, "model_refit_date": sig["model_refit_date"]})
    # V26 rules on closed periods
    lo_ew = [p["lo_minus_ew"] for p in periods if p["status"] == "CLOSED" and p.get("lo_minus_ew") is not None]
    roll = None
    if len(lo_ew) >= PAUSE_ROLLING_PERIODS:
        roll = float(np.prod([1.0 + p["capital_ret"] for p in periods if p["status"] == "CLOSED"][-PAUSE_ROLLING_PERIODS:]) -
                     np.prod([1.0 + p["ew_ret"] for p in periods if p["status"] == "CLOSED"][-PAUSE_ROLLING_PERIODS:]))
    run = 0
    for x in lo_ew:
        run = run + 1 if x <= 0 else 0
    state = "RUNNING"
    if roll is not None and roll < PAUSE_THRESHOLD:
        state = "PAUSE_REVIEW"
    if run >= RETIRE_CONSECUTIVE:
        state = "RETIRE"
    n_closed = len(lo_ew)
    summary = {"state": state, "n_periods_closed": n_closed, "n_periods_open": sum(1 for p in periods if p["status"] != "CLOSED"),
               "total_capital_ret": (closed["total"] if closed.get("trades") else None), "equity": (closed["trades"][-1]["equity"] if closed.get("trades") else capital),
               "n_lo_beat_ew": sum(1 for x in lo_ew if x > 0), "rolling_%d_lo_minus_ew" % PAUSE_ROLLING_PERIODS: roll, "consecutive_lo_le_ew": run,
               "rules": {"pause": "%d-period rolling LO-EW < %.0f%%" % (PAUSE_ROLLING_PERIODS, PAUSE_THRESHOLD * 100), "retire": "%d consecutive LO-EW <= 0" % RETIRE_CONSECUTIVE},
               "next_signal_date": dates[sig_idx[-1] + HOLD_DAYS + 1] if sig_idx[-1] + HOLD_DAYS + 1 <= last else "%d sessions after %s" % (HOLD_DAYS + 1, dates[sig_idx[-1]]),
               "capital_yuan": capital, "chain_anchor": CHAIN_ANCHOR_SIGNAL, "money": "NONE (shadow)", "orders_sent": False}
    out = {"summary": summary, "periods": periods}
    dump_json(os.path.join(LEDGER_DIR, "LEDGER.json"), out)
    write_csv(os.path.join(LEDGER_DIR, "LEDGER.csv"), ("status", "signal_date", "entry", "exit", "n_sel", "n_fill", "capital_ret", "ew_ret", "lo_minus_ew", "equity"),
              [dict((k, p.get(k)) for k in ("status", "signal_date", "entry", "exit", "n_sel", "n_fill", "capital_ret", "ew_ret", "lo_minus_ew", "equity")) for p in periods])
    print(TAG, state, "closed", n_closed, "open", summary["n_periods_open"], "next", summary["next_signal_date"], flush=True)
    return out
