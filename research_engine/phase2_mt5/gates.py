"""Candidate Gate V2 C0–C13. Auto-trade only if ALL pass. Otherwise DO NOT TRADE."""
from __future__ import annotations

from typing import Any, Dict, List

GATES = (
    ("C0", "Pre-registered write-once contract exists"),
    ("C1", "Data is PIT; no future-close fills"),
    ("C2", "Economic labels (net, cost, MFE/MAE)"),
    ("C3", "Non-overlap book; overlap disclosed + purge/embargo"),
    ("C4", "Unified costs; assumptions labeled"),
    ("C5", "Baselines run; model has incremental OOS value vs baseline"),
    ("C6", "Research and validation same sign; no val-set search"),
    ("C7", "FINAL OOS locked and unused for selection"),
    ("C8", "Multiple-testing counted"),
    ("C9", "Time stop AND risk stop"),
    ("C10", "Three-state LONG/SHORT/FLAT; not always-in"),
    ("C11", "Execution uses SignalContractV2 (same as backtest)"),
    ("C12", "Paper ledger maps signal_id to MT5 deal"),
    ("C13", "20%/month is not an optimizer target; leverage is not alpha"),
)


def evaluate(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Honest gate. Missing evidence = fail. Never invent a Candidate."""
    results = []

    def add(code: str, ok: bool, why: str):
        results.append({"id": code, "pass": bool(ok), "why": why})

    add("C0", bool(ctx.get("contract_exists")), ctx.get("c0_why") or "contract missing")
    add("C1", bool(ctx.get("pit")), ctx.get("c1_why") or "PIT not demonstrated")
    add("C2", bool(ctx.get("economic_labels")), ctx.get("c2_why") or "labels not economic")
    add("C3", bool(ctx.get("nonoverlap_book")), ctx.get("c3_why") or "overlap not handled")
    add("C4", bool(ctx.get("costs_labeled")), ctx.get("c4_why") or "costs not labeled")
    add("C5", bool(ctx.get("incremental_oos")), ctx.get("c5_why") or "no incremental OOS vs baseline")
    add("C6", bool(ctx.get("same_sign_windows")), ctx.get("c6_why") or "windows disagree or searched")
    add("C7", bool(ctx.get("final_oos_locked")), ctx.get("c7_why") or "FINAL OOS not locked")
    add("C8", bool(ctx.get("multiple_testing")), ctx.get("c8_why") or "degrees of freedom not counted")
    add("C9", bool(ctx.get("time_stop") and ctx.get("risk_stop")), ctx.get("c9_why") or "need time stop + risk stop")
    add("C10", bool(ctx.get("three_state")), ctx.get("c10_why") or "always-in or no FLAT")
    add("C11", bool(ctx.get("same_schema")), ctx.get("c11_why") or "backtest/paper schema split")
    add("C12", bool(ctx.get("deal_mapped")), ctx.get("c12_why") or "no signal_id→deal map")
    add("C13", bool(ctx.get("no_20pct_optimize")), ctx.get("c13_why") or "20% used as fit target")

    passed = [r for r in results if r["pass"]]
    failed = [r for r in results if not r["pass"]]
    all_ok = len(failed) == 0
    return {
        "candidate": False if not all_ok else bool(ctx.get("force_candidate")),
        "do_not_trade": not all_ok,
        "n_pass": len(passed),
        "n_fail": len(failed),
        "gates": results,
        "failed_ids": [r["id"] for r in failed],
        "note": "candidate remains false unless every gate passes. Grok/RSI/V4 follow cannot pass.",
    }


def default_phase2_context() -> Dict[str, Any]:
    return {
        "contract_exists": True,
        "c0_why": "EXP-001/002/003 contracts written",
        "pit": True,
        "c1_why": "signal at close[t], fill next open",
        "economic_labels": True,
        "nonoverlap_book": True,
        "costs_labeled": True,
        "incremental_oos": False,
        "c5_why": "no model beat baselines on RESEARCH OOS",
        "same_sign_windows": False,
        "c6_why": "Phase 1 V4 research −10% / val +84% already disagrees",
        "final_oos_locked": True,
        "c7_why": "FINAL_OOS from 2025-09-12 locked, not scored for selection",
        "multiple_testing": True,
        "time_stop": True,
        "risk_stop": False,
        "c9_why": "baselines have time stop only; no pre-registered risk stop on a Candidate",
        "three_state": True,
        "same_schema": True,
        "deal_mapped": False,
        "c12_why": "no live Phase 2 fills yet; MT5_JOURNAL was already missing in Phase 1",
        "no_20pct_optimize": True,
        "force_candidate": False,
    }
