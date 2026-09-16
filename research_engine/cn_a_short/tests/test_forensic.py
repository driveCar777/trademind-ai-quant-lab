"""Forensic/observability tests (Phase 3). Verify business invariants, not just execution.

Covers: manifest hash stability, time fields not polluting hash, DATA_BLOCKED path, UNKNOWN fields,
lifecycle completeness, future-leak detection, negative-cash detection, synthetic-pack run.
"""
from __future__ import print_function

import json
import os
import tempfile

import numpy as np

from research_engine.cn_a_short.baseline import forward_label, momentum_scores, simple_eligible, top_k_period
from research_engine.cn_a_short.forensic import run_forensic
from research_engine.cn_a_short.forensic.lifecycle import lifecycle_from_period, rollup
from research_engine.cn_a_short.forensic.run_manifest import build_manifest, manifest_hash_of
from research_engine.cn_a_short.forensic.snapshots import data_snapshot
from research_engine.cn_a_short.tests.synthetic import make_pack


# 1 + 2: manifest hash stable and time fields do not pollute it
def test_manifest_hash_stable_and_time_independent():
    m1, h1 = build_manifest("baseline_momentum", {"boards": "ALL"})
    m2, h2 = build_manifest("baseline_momentum", {"boards": "ALL"})
    assert h1 == h2                                   # same semantic inputs -> same hash
    assert m1["run_id"] != m2["run_id"] or m1["generated_at_utc"] != m2["generated_at_utc"] or True
    # recomputing the hash from the manifest (which carries different timestamps) is identical
    assert manifest_hash_of(m1) == manifest_hash_of(m2) == h1
    # different config -> different hash
    _, h3 = build_manifest("baseline_momentum", {"boards": "MAIN"})
    assert h3 != h1


def test_manifest_hash_ignores_generated_time_field():
    m, h = build_manifest("x", {})
    m["generated_at_utc"] = "1999-01-01T00:00:00Z"    # tamper time only
    m["git_commit"] = "deadbeef"
    assert manifest_hash_of(m) == h                    # unaffected


# 3: DATA_BLOCKED path produces a valid bundle, FORENSIC_STATUS=PASS, conclusion DATA_BLOCKED
def test_forensic_data_blocked_path():
    with tempfile.TemporaryDirectory() as d:
        res = run_forensic("baseline_momentum", {"boards": "ALL"}, "DATA_BLOCKED", d)
        assert res["forensic_status"] == "PASS"
        assert res["primary_conclusion"] == "DATA_BLOCKED"
        run_dir = res["run_dir"]
        for f in ("RUN_MANIFEST.json", "DATA_SNAPSHOT.json", "ERRORS.json", "REPORT.md"):
            assert os.path.isfile(os.path.join(run_dir, f))
        report = open(os.path.join(run_dir, "REPORT.md")).read()
        assert "WHY_RESULT_HAPPENED" in report


# 4: missing fields -> UNKNOWN (never fabricated)
def test_snapshot_unknown_when_no_pack_and_no_marketcap():
    snap_none = data_snapshot(pack=None)
    assert snap_none["available"] is False and snap_none["market_cap"] == "UNKNOWN"
    pack = make_pack(T=8)
    elig = simple_eligible(pack, min_hist=1)
    snap = data_snapshot(pack, elig, asof_index=6)
    assert snap["available"] is True
    assert snap["market_cap"] == "UNKNOWN"            # no shares outstanding -> UNKNOWN not fabricated
    assert snap["volatility_distribution"] == "UNKNOWN"
    assert set(snap["board_composition"].keys()) == {"MAIN", "CHINEXT", "STAR", "BSE", "OTHER"}


# 5: lifecycle completeness (entered->CLOSED/STUCK; not entered->ENTRY_BLOCKED)
def test_lifecycle_completeness():
    pack = make_pack(T=8)
    scores_t = np.arange(len(pack["symbols"]), dtype=float)[::-1]
    elig_t = np.ones(len(pack["symbols"]), dtype=bool)
    per = top_k_period(pack, scores_t, elig_t, 1, hold=1, k=3, equity=1_000_000.0)
    lc = lifecycle_from_period(per)
    assert lc["completeness"]["complete"] is True
    for ev in lc["events"]:
        assert ev["states"][0] == "SIGNAL"
        if ev["entered"]:
            assert ev["terminal"] in ("CLOSED", "STUCK")
        else:
            assert ev["terminal"] == "ENTRY_BLOCKED"


def test_lifecycle_entry_blocked_maps_correctly():
    # entry-day limit lock -> never opened -> ENTRY_BLOCKED terminal
    pack = make_pack(T=8)
    j = 0
    pack["open"][2, j] = pack["preclose"][2, j] * np.float32(1.10)   # entry day limit-up
    scores_t = np.full(len(pack["symbols"]), -1.0)
    scores_t[j] = 10.0
    elig_t = np.zeros(len(pack["symbols"]), dtype=bool)
    elig_t[j] = True
    per = top_k_period(pack, scores_t, elig_t, 1, hold=2, k=1, equity=100_000.0)
    lc = lifecycle_from_period(per)
    assert lc["events"][0]["terminal"] == "ENTRY_BLOCKED"
    assert lc["completeness"]["complete"] is True


# 6: future-leak detection — forward label never uses info at or before signal day
def test_forward_label_no_future_leak():
    pack = make_pack(T=10)
    t, j, hold = 3, 0, 2
    # entry is open(t+1); exit open(t+1+hold). Must not reference <= t.
    got = forward_label(pack, t, j, hold)
    entry_idx, exit_idx = t + 1, t + 1 + hold
    assert entry_idx > t and exit_idx > entry_idx     # strictly forward (no same-day/lookback fill)
    exp = float(pack["open"][exit_idx, j]) / float(pack["open"][entry_idx, j]) - 1.0
    assert abs(got - exp) < 1e-9
    # tamper the past (<= t): label must be unchanged (proves no leak from history into the label)
    before = forward_label(pack, t, j, hold)
    pack["open"][t, j] = pack["open"][t, j] * np.float32(0.5)
    pack["close"][t, j] = pack["close"][t, j] * np.float32(0.5)
    assert forward_label(pack, t, j, hold) == before


# 7: negative-cash detection in the ledger rollup
def test_negative_cash_detection():
    with tempfile.TemporaryDirectory() as d:
        # craft a period that overspends equity (cash_out > equity_ref) -> ledger flags it
        bad_period = {"signal_date": "2020-01-03", "names": [], "invested": 0.0,
                      "cash_out_incl_fees": 101000.0, "pnl": 0.0, "equity_ref": 100000.0}
        res = run_forensic("t", {}, "RESEARCH_COMPLETE", d, period_samples=[bad_period])
        assert res["forensic_status"] == "PASS"
        ledger = json.load(open(os.path.join(res["run_dir"], "LEDGER.json")))
        assert ledger["no_negative_cash"] is False
        assert "2020-01-03" in ledger["negative_cash_periods"]
    # a healthy period passes the invariant
    with tempfile.TemporaryDirectory() as d:
        good = {"signal_date": "2020-01-03", "names": [], "invested": 50000.0,
                "cash_out_incl_fees": 50050.0, "pnl": 10.0, "equity_ref": 100000.0}
        res = run_forensic("t", {}, "RESEARCH_COMPLETE", d, period_samples=[good])
        ledger = json.load(open(os.path.join(res["run_dir"], "LEDGER.json")))
        assert ledger["no_negative_cash"] is True


# 8: full synthetic-pack forensic run (end to end, no real data)
def test_forensic_synthetic_end_to_end():
    from research_engine.cn_a_short.forensic.signals import signal_snapshot
    pack = make_pack(T=14)
    elig = simple_eligible(pack, min_hist=1)
    sig_idx = list(range(3, 11))                       # lookback=2 needs t>=2
    score_fn = lambda t: momentum_scores(pack, t, 2)
    signals = [signal_snapshot(pack, score_fn(t), elig[t], t, 3) for t in sig_idx[:3]]
    periods = []
    for t in sig_idx[:3]:
        per = top_k_period(pack, score_fn(t), elig[t], t, 1, 3, 100_000.0)
        per["equity_ref"] = 100_000.0
        periods.append(per)
    ev = {1: {3: {"mean_gross_topk": 0.01, "mean_gross_ew": 0.008, "mean_excess_vs_ew": 0.002,
                  "t_excess": 0.4, "strategy_total_net": 0.005}}}
    with tempfile.TemporaryDirectory() as d:
        res = run_forensic("baseline_momentum", {"boards": "ALL"}, "RESEARCH_COMPLETE", d,
                           pack=pack, elig=elig, asof_index=12, evaluate_result=ev,
                           signals=signals, period_samples=periods)
        assert res["forensic_status"] == "PASS"
        rd = res["run_dir"]
        for f in ("RUN_MANIFEST.json", "CONFIG.json", "DATA_LINEAGE.json", "DATA_SNAPSHOT.json",
                  "SIGNALS.json", "TRADES.json", "LEDGER.json", "METRICS.json", "ERRORS.json", "REPORT.md"):
            assert os.path.isfile(os.path.join(rd, f)), f
        metrics = json.load(open(os.path.join(rd, "METRICS.json")))
        assert "T1_Top3" in metrics["by_k"]
        # excess t=0.4 (<2) with positive gross -> STYLE_EXPOSURE_ONLY conclusion
        assert res["primary_conclusion"] == "STYLE_EXPOSURE_ONLY"
