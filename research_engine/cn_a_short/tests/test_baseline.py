"""Baseline engine tests (§32): forward label, T+1/hold spacing, limit lock, suspension, top-K, PIT."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_short.baseline import (evaluate, forward_label, momentum_scores,
                                                 panel_coverage, simple_eligible, top_k_period, ew_period)
from research_engine.cn_a_short.tests.synthetic import make_pack


def test_forward_label_open_to_open():
    pack = make_pack(T=8)
    t, j, hold = 2, 0, 3
    got = forward_label(pack, t, j, hold)
    exp = float(pack["open"][t + 1 + hold, j]) / float(pack["open"][t + 1, j]) - 1.0
    assert abs(got - exp) < 1e-6


def test_forward_label_needs_t_plus_one_entry_and_hold_ge_1():
    pack = make_pack(T=8)
    assert forward_label(pack, 2, 0, 0) is None            # hold must be >= 1 (T+1 minimum)
    assert forward_label(pack, 7, 0, 1) is None            # out of range


def test_hold_spacing_and_t_plus_1_exit():
    pack = make_pack(T=8)
    scores_t = np.arange(len(pack["symbols"]), dtype=float)[::-1]  # symbol 0 best
    elig_t = np.ones(len(pack["symbols"]), dtype=bool)
    for hold in (1, 2, 3, 5):
        t = 1
        per = top_k_period(pack, scores_t, elig_t, t, hold, k=3, equity=100_000.0)
        if per is None:
            continue
        assert per["entry"] == pack["dates"][t + 1]        # entry = T+1 open (never same-day)
        assert per["exit"] == pack["dates"][t + 1 + hold]  # exit = T+1+hold
        # T+1: earliest possible exit index (hold=1) is t+2 > entry index t+1
        assert (t + 1 + hold) > (t + 1)


def test_entry_limit_lock_not_opened():
    # ENTRY-day limit lock -> position never opened (correct: never bought).
    pack = make_pack(T=8)
    j = 0
    t0 = 2  # entry day (signal t=1)
    pack["open"][t0, j] = pack["preclose"][t0, j] * np.float32(1.10)   # +10% -> LIMIT_LOCK on entry
    scores_t = np.full(len(pack["symbols"]), -1.0)
    scores_t[j] = 10.0
    elig_t = np.zeros(len(pack["symbols"]), dtype=bool)
    elig_t[j] = True
    per = top_k_period(pack, scores_t, elig_t, 1, hold=2, k=1, equity=100_000.0)
    assert per["names"][0]["status"] == "LIMIT_LOCK"
    assert per["names"][0]["entered"] is False
    assert per["n_entry"] == 0 and per["n_fill"] == 0


def test_entry_suspension_not_opened():
    pack = make_pack(T=8)
    j = 1
    t0 = 2
    pack["tradestatus"][t0, j] = 0                         # suspended on ENTRY day -> never opened
    scores_t = np.full(len(pack["symbols"]), -1.0)
    scores_t[j] = 10.0
    elig_t = np.zeros(len(pack["symbols"]), dtype=bool)
    elig_t[j] = True
    per = top_k_period(pack, scores_t, elig_t, 1, hold=2, k=1, equity=100_000.0)
    assert per["names"][0]["status"] == "SUSPENDED"
    assert per["names"][0]["entered"] is False
    assert per["n_entry"] == 0 and per["n_fill"] == 0


def test_top_k_selection_order():
    pack = make_pack(T=8)
    # scores: give a clear ranking; top-2 should be the two highest-score symbols
    scores_t = np.array([1.0, 5.0, 3.0, 9.0, 2.0, 7.0])
    elig_t = np.ones(6, dtype=bool)
    per = top_k_period(pack, scores_t, elig_t, 1, hold=1, k=2, equity=1_000_000.0)
    picked = [n["symbol"] for n in per["names"]]
    assert picked == [pack["symbols"][3], pack["symbols"][5]]  # scores 9 then 7


def test_pit_no_same_day_fill():
    # PIT: a signal computed at close(t) must fill at open(t+1), not open(t).
    pack = make_pack(T=8)
    scores_t = momentum_scores(pack, 3, lookback=2)
    assert scores_t is not None and np.all(np.isfinite(scores_t))
    elig_t = np.ones(6, dtype=bool)
    per = top_k_period(pack, scores_t, elig_t, 3, hold=1, k=2, equity=1_000_000.0)
    assert per["entry"] == pack["dates"][4]                # t=3 -> entry index 4


def test_exit_limit_lock_forces_carry_not_dropped():
    # §B / §D.4: entry FILL, planned exit LIMIT_LOCK, next day FILL -> position HELD & carried, NOT dropped.
    pack = make_pack(T=8)
    j = 0
    t, hold = 1, 1
    t0, t1 = t + 1, t + 1 + hold           # entry=2, planned exit=3
    pack["open"][t1, j] = pack["preclose"][t1, j] * np.float32(1.10)   # exit day one-word limit-up
    # t1+1 = 4 stays a normal FILL day by construction
    scores_t = np.full(len(pack["symbols"]), -1.0)
    scores_t[j] = 10.0
    elig_t = np.zeros(len(pack["symbols"]), dtype=bool)
    elig_t[j] = True
    per = top_k_period(pack, scores_t, elig_t, t, hold=hold, k=1, equity=100_000.0)
    nm = per["names"][0]
    assert nm["entered"] is True                 # bought (not "never traded")
    assert per["n_entry"] == 1 and per["invested"] > 0
    assert nm["status"] == "FILL_CARRY_1"
    assert nm["planned_exit"] == pack["dates"][t1]
    assert nm["actual_exit"] == pack["dates"][t1 + 1]
    assert nm["forced_hold_days"] == 1
    assert nm["exit_block_reason"] == "LIMIT_LOCK"
    assert per["n_round_trip_clean"] == 0 and per["n_exit_carry"] == 1


def test_exit_suspension_forces_carry():
    # §D.5: entry FILL, planned exit SUSPENDED, recovers next day -> carried, held.
    pack = make_pack(T=8)
    j = 2
    t, hold = 1, 1
    t0, t1 = t + 1, t + 1 + hold
    pack["tradestatus"][t1, j] = 0                # planned exit day suspended
    scores_t = np.full(len(pack["symbols"]), -1.0)
    scores_t[j] = 10.0
    elig_t = np.zeros(len(pack["symbols"]), dtype=bool)
    elig_t[j] = True
    per = top_k_period(pack, scores_t, elig_t, t, hold=hold, k=1, equity=100_000.0)
    nm = per["names"][0]
    assert nm["entered"] is True and per["n_entry"] == 1
    assert nm["status"] == "FILL_CARRY_1"
    assert nm["forced_hold_days"] == 1
    assert nm["exit_block_reason"] == "SUSPENDED"


def test_exit_never_recovers_marks_stuck_not_dropped():
    # Entry FILL, but exit blocked for the entire carry window -> STUCK, still HELD (not dropped).
    pack = make_pack(T=8)
    j = 0
    t, hold = 1, 1
    t0, t1 = t + 1, t + 1 + hold
    for tk in range(t1, len(pack["dates"])):     # suspend every day from planned exit onward
        pack["tradestatus"][tk, j] = 0
    scores_t = np.full(len(pack["symbols"]), -1.0)
    scores_t[j] = 10.0
    elig_t = np.zeros(len(pack["symbols"]), dtype=bool)
    elig_t[j] = True
    per = top_k_period(pack, scores_t, elig_t, t, hold=hold, k=1, equity=100_000.0)
    nm = per["names"][0]
    assert nm["entered"] is True and per["n_entry"] == 1
    assert nm["status"] == "STUCK" and per["n_stuck"] == 1
    assert nm["forced_hold_days"] >= 1


def test_period_cash_out_never_exceeds_equity():
    # Multi-name true-cash invariant (§A / §D.2): sum of buy cash out (incl ¥5 min fee) <= equity.
    pack = make_pack(T=8)
    scores_t = np.arange(len(pack["symbols"]), dtype=float)[::-1]
    elig_t = np.ones(len(pack["symbols"]), dtype=bool)
    # small equity so the ¥5 min fee actually bites
    per = top_k_period(pack, scores_t, elig_t, 1, hold=1, k=5, equity=30_000.0)
    assert per["cash_out_incl_fees"] <= 30_000.0 + 1e-6


def test_panel_coverage_detects_good_and_degenerate():
    # A real (synthetic) pack has prices -> not degenerate.
    good = make_pack(T=12)
    cg = panel_coverage(good)
    assert cg["degenerate"] is False
    assert cg["finite_close_rate_when_listed"] > 0.9
    assert cg["n_symbols_with_any_close"] == len(good["symbols"])
    # An all-NaN pack (what pack_panel produces from a MISSING raw panel) -> degenerate -> must be caught.
    empty = make_pack(T=12)
    for f in ("open", "high", "low", "close", "preclose", "volume", "amount", "turn"):
        empty[f] = np.full_like(empty[f], np.nan)
    ce = panel_coverage(empty)
    assert ce["degenerate"] is True
    assert ce["n_symbols_with_any_close"] == 0
    assert ce["missing_close_rate_listed"] == 1.0


def test_ew_period_and_evaluate_run():
    pack = make_pack(T=12)
    elig = simple_eligible(pack, min_hist=1)
    ew = ew_period(pack, elig[2], 2, hold=2)
    assert ew is not None and np.isfinite(ew["mean_ew"])
    sig = list(range(1, 8))
    res = evaluate(pack, lambda t: momentum_scores(pack, t, 2), elig, sig, hold=1, ks=(3, 5), equity=100_000.0, min_eligible=1)
    assert set(res.keys()) == {3, 5}
    for k in (3, 5):
        assert res[k]["n_signal"] >= 1
        assert res[k]["turnover_one_way_per_period"] == 1.0
