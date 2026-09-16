"""CLI: run the A-Short D1 baseline over T+1/T+2/T+3/T+5 x Top-K, IF the frozen price pack is present.

Empirical alpha requires the upstream frozen price pack (tm-ashare-EQUITY-D1-...). When it is not
materialized in this environment the run is DATA_BLOCKED and this prints exactly what to do; it never
fabricates results. Cost/account/feasibility tables do NOT need the pack -> see report_tables.py.

Usage:
  python -m research_engine.cn_a_short.run_baseline                 # research window, momentum baseline
  python -m research_engine.cn_a_short.run_baseline --scores PATH   # external [T,N] score .npy
Windows/OOS are LOCKED (single unlock) per contract; this CLI refuses OOS unless --unlock-oos given.
"""
from __future__ import print_function

import argparse
import datetime
import hashlib
import json
import os
import subprocess

import numpy as np

from research_engine.cn_a_short import (CONTRACT_ID, DERIVED_DATASET_ID, HORIZONS, MIN_ELIGIBLE,
                                        OOS_WINDOW, RESEARCH_WINDOW, SEED, TOP_KS, UPSTREAM_DATASET_HASH,
                                        UPSTREAM_DATASET_ID, VALIDATION_WINDOW)
from research_engine.cn_a_short.baseline import (evaluate, momentum_scores, panel_coverage,
                                                 simple_eligible, top_k_period)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_short")
CONTRACT_DOC = os.path.join(ROOT, "docs", "a_short", "A_SHORT_D1_RESEARCH_CONTRACT.md")


def _git_head():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    except Exception:
        return None


def _contract_hash():
    try:
        return hashlib.sha256(open(CONTRACT_DOC, "rb").read()).hexdigest()
    except Exception:
        return None


def _meta(extra=None):
    m = {
        "contract_id": CONTRACT_ID,
        "contract_hash": _contract_hash(),
        "upstream_dataset_id": UPSTREAM_DATASET_ID,
        "upstream_hash": UPSTREAM_DATASET_HASH,
        "derived_dataset_id": DERIVED_DATASET_ID,
        "derived_dataset_hash": None,
        "code_commit": _git_head(),
        "generated_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "seed": SEED,
        "research_window": RESEARCH_WINDOW,
        "validation_window": VALIDATION_WINDOW,
        "oos_window": OOS_WINDOW,
    }
    if extra:
        m.update(extra)
    return m


def _pack_available():
    try:
        from research_engine.cn_a_share_alpha.pack import pack_exists
        return pack_exists()
    except Exception:
        return False


def _write_artifact(name, payload):
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    path = os.path.join(OUT, name)
    json.dump(payload, open(path, "w"), indent=2, default=float)
    return path


def _blocked_message(reason, detail=None):
    from research_engine.cn_a_share_alpha.paths import CACHE
    msg = _meta({
        "status": "DATA_BLOCKED",
        "reason": reason,
        "detail": detail,
        "expected_pack_cache": CACHE,
        "how_to_materialize": [
            "On the :9000 master host (has the frozen raw daily panel; BaoStock login is restricted to :9000):",
            "python -c \"from research_engine.cn_a_share_alpha.pack import pack_panel; pack_panel()\"",
            "then re-run: python -m research_engine.cn_a_short.run_baseline",
        ],
        "note": "Do NOT rebuild via BaoStock off :9000 — that yields a different, unverifiable dataset that fails the registered upstream_hash. Cost/account tables do NOT need the pack; use report_tables.py.",
    })
    return msg


def _emit_feasibility_artifacts():
    """Pack-INDEPENDENT arithmetic (cost sensitivity + account executability). These carry NO alpha; they
    exist so Step 22 artifacts are present even when the empirical run is blocked."""
    from research_engine.cn_a_short import ACCOUNT_SIZES, SLIPPAGE_SIDE_GRID, TURNOVER_SCENARIOS
    from research_engine.cn_a_short.account import feasible_portfolio
    from research_engine.cn_a_short.feasibility import cost_envelope
    cost_rows = [cost_envelope(h, tn, P, slip) for h in HORIZONS
                 for tn in sorted(set(TURNOVER_SCENARIOS.values())) for P in (2_000, 20_000, 100_000)
                 for slip in SLIPPAGE_SIDE_GRID]
    _write_artifact("PHASE2A2_COST_SENSITIVITY.json",
                    _meta({"kind": "COST_SENSITIVITY", "note": "arithmetic cost envelope; pack-independent; NO alpha",
                           "slippage_side_grid": list(SLIPPAGE_SIDE_GRID), "rows": cost_rows}))
    acct_rows = []
    for e in ACCOUNT_SIZES:
        for pr in (5, 10, 20, 50, 100):
            for k in (3, 5, 10, 20):
                fp = feasible_portfolio(e, pr, k, exposure=1.0, slip_side=0.001)
                acct_rows.append({"equity": e, "price": pr, "k": k, "feasible": fp["feasible"],
                                  "n_names": fp["n_names"], "cash_idle_frac": fp["cash_idle_frac"],
                                  "per_name_notional": fp["per_name_notional"],
                                  "rt_cost_pct_total": fp.get("rt_cost_pct_total")})
    _write_artifact("PHASE2A2_ACCOUNT_GRID.json",
                    _meta({"kind": "ACCOUNT_GRID", "note": "executability arithmetic; pack-independent; NO alpha",
                           "rows": acct_rows}))


def _forensic_config(window, equity, boards, scores_path):
    return {"experiment": "baseline_momentum", "window": list(window), "equity": equity, "boards": boards,
            "model": "20D_MOMENTUM_BASELINE" if not scores_path else os.path.basename(scores_path),
            "horizons": list(HORIZONS), "top_ks": list(TOP_KS), "min_eligible": MIN_ELIGIBLE,
            "boards_default": boards, "exclude_st": False, "min_hist": 20}


def _forensic_safe(experiment, config, status, **kw):
    """Run the forensic bundle without ever breaking the baseline (PASS/DEGRADED)."""
    try:
        from research_engine.cn_a_short.forensic import run_forensic
        return run_forensic(experiment, config, status, OUT, **kw)
    except Exception as exc:
        return {"forensic_status": "DEGRADED", "error": str(exc)}


def _sample_forensic_inputs(pack, elig, signal_idx, score_fn, equity, boards, n_days=5, hold=1, k=10):
    """Read-only observability samples (SIGNALS + lifecycle) — does NOT affect the evaluate result."""
    from research_engine.cn_a_short.forensic.signals import signal_snapshot
    signals, periods = [], []
    days = signal_idx[:: max(1, len(signal_idx) // max(1, n_days))][:n_days]
    for t in days:
        scores_t = score_fn(t) if callable(score_fn) else score_fn[t]
        if scores_t is None:
            continue
        signals.append(signal_snapshot(pack, scores_t, elig[t], t, k, boards=boards))
        per = top_k_period(pack, scores_t, elig[t], t, hold, k, equity, boards=boards)
        if per is not None:
            per["equity_ref"] = equity
            periods.append(per)
    return signals, periods


def run(window=RESEARCH_WINDOW, scores_path=None, equity=100_000.0, boards="ALL", unlock_oos=False,
        forensic=True):
    _emit_feasibility_artifacts()
    config = _forensic_config(window, equity, boards, scores_path)
    if not _pack_available():
        msg = _blocked_message("FROZEN_PRICE_PACK_NOT_MATERIALIZED")
        _write_artifact("PHASE2A2_RESULTS.json", msg)
        _write_artifact("PHASE2A2_DIAGNOSTICS.json", _meta({
            "status": "DATA_BLOCKED", "reason": "FROZEN_PRICE_PACK_NOT_MATERIALIZED",
            "note": "entry/exit/carry/stuck diagnostics require the materialized frozen pack (Steps 8-10)."}))
        if forensic:
            msg["forensic"] = _forensic_safe("baseline_momentum", config, "DATA_BLOCKED")
        print(json.dumps(msg, indent=2))
        return msg
    from research_engine.cn_a_share_alpha.pack import load_pack
    pack = load_pack()
    # Guard (Phase 2A.2): a pack built from a missing raw panel is all-NaN. Running research on it would
    # fabricate empty "results". Detect degenerate coverage and DATA_BLOCK instead.
    cov = panel_coverage(pack)
    if cov["degenerate"]:
        msg = _blocked_message("DEGENERATE_PANEL_NO_PRICES", detail=cov)
        _write_artifact("PHASE2A2_RESULTS.json", msg)
        if forensic:
            msg["forensic"] = _forensic_safe("baseline_momentum", config, "DATA_BLOCKED",
                                             pack=pack, coverage=cov)
        print(json.dumps(msg, indent=2))
        return msg
    dates = pack["dates"]
    elig = simple_eligible(pack, min_hist=20)
    a, b = window
    i0 = next(i for i, d in enumerate(dates) if d >= a)
    i1 = max(i for i, d in enumerate(dates) if d <= b)
    signal_idx = list(range(i0, i1 + 1))
    if scores_path:
        scores = np.load(scores_path, mmap_mode="r")
        score_fn = scores
        model_used = os.path.basename(scores_path)
    else:
        score_fn = lambda t: momentum_scores(pack, t, lookback=20)
        model_used = "20D_MOMENTUM_BASELINE"
    result = _meta({"status": "RESEARCH_COMPLETE", "window": window, "equity": equity, "boards": boards,
                    "model_used": model_used, "coverage": cov, "horizons": {}})
    for hold in HORIZONS:
        result["horizons"][hold] = evaluate(pack, score_fn, elig, signal_idx, hold, TOP_KS, equity,
                                            boards=boards, min_eligible=MIN_ELIGIBLE)
    _write_artifact("PHASE2A2_RESULTS.json", result)
    print("WROTE", os.path.join(OUT, "PHASE2A2_RESULTS.json"), "model=", model_used)
    if forensic:
        signals, periods = _sample_forensic_inputs(pack, elig, signal_idx, score_fn, equity, boards)
        result["forensic"] = _forensic_safe("baseline_momentum", config, "RESEARCH_COMPLETE",
                                             pack=pack, elig=elig, asof_index=i1, coverage=cov,
                                             evaluate_result=result["horizons"], signals=signals,
                                             period_samples=periods)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default=None)
    ap.add_argument("--equity", type=float, default=100_000.0)
    ap.add_argument("--boards", default="ALL")
    ap.add_argument("--unlock-oos", action="store_true")
    ap.add_argument("--forensic", dest="forensic", action="store_true", default=True,
                    help="write forensic runs/<RUN_ID>/ bundle (default on)")
    ap.add_argument("--no-forensic", dest="forensic", action="store_false",
                    help="disable the forensic bundle")
    args = ap.parse_args()
    run(scores_path=args.scores, equity=args.equity, boards=args.boards, unlock_oos=args.unlock_oos,
        forensic=args.forensic)
