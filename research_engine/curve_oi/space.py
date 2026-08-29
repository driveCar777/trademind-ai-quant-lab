"""Locked CURVE_OI_JOINT space. Hash is search-space only."""
from __future__ import print_function

import hashlib
import json

from research_engine.curve_oi import (
    ALLOWED_HYPOTHESIS_IDS,
    FAMILY_ID,
    HOLD_BARS,
    LOCKED_HASH,
    CUROI_ID,
    CUROI_SEED,
)
from research_engine.holdout import final_oos_access
from research_engine.v6_external.novelty import assert_new_mechanism


HYPOTHESIS_SPECS = {
    "HYP-CUROI-0001": {
        "hypothesis_id": "HYP-CUROI-0001",
        "name": "STEEPEN_OI_EXPAND",
        "event": "STEEPEN_OI_EXPAND",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-CUROI-0002": {
        "hypothesis_id": "HYP-CUROI-0002",
        "name": "FLATTEN_OI_EXPAND",
        "event": "FLATTEN_OI_EXPAND",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-CUROI-0003": {
        "hypothesis_id": "HYP-CUROI-0003",
        "name": "STEEPEN_OI_CONTRACT",
        "event": "STEEPEN_OI_CONTRACT",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
}


def hypotheses():
    return [
        {
            "hypothesis_id": "HYP-CUROI-0001",
            "name": "STEEPEN_OI_EXPAND",
            "hypothesis": "When the official curve steepens and official front open interest expands, tightness is easing with new participation. After OI knowledge T+1 21:00Z, next-session front return is negative.",
            "economic_mechanism": "Curve steepening plus an official contract open interest expansion is an oi shock into a richer storage curve, not OI-rising-implies-buy and not slope-as-level. Not price momentum.",
            "dataset": "Frozen GLBX GC/CL curve. No new Databento bytes.",
            "feature": "lagged steepening > 0 and lagged front_oi_change > 0",
            "target": "next-session front open-to-open after OI knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps research cost; no leverage",
            "validation": "pre-registered; leakage; knowledge-time; determinism; lineage; FDR q=0.05; four Xavier",
            "failure_gate": "If FALSIFIED, do not retune steepening or OI sign. Next = daily OI versus weekly positioning change.",
        },
        {
            "hypothesis_id": "HYP-CUROI-0002",
            "name": "FLATTEN_OI_EXPAND",
            "hypothesis": "When the official curve flattens and official front open interest expands, tightness is rising with new participation. After OI knowledge, next-session front return is positive.",
            "economic_mechanism": "Curve steepening reversed (flattening) plus contract open interest expansion is an oi shock into a tighter curve. Joint curve move plus oi shock, not a curve level. Not price momentum.",
            "dataset": "same frozen official curve",
            "feature": "lagged steepening < 0 and lagged front_oi_change > 0",
            "target": "next-session front open-to-open after knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates; not a z score search",
            "failure_gate": "No hold search. Do not drop the curve leg as a rescue.",
        },
        {
            "hypothesis_id": "HYP-CUROI-0003",
            "name": "STEEPEN_OI_CONTRACT",
            "hypothesis": "When the official curve steepens while official front open interest contracts, participation is leaving as tightness eases. After OI knowledge, next-session front return is positive.",
            "economic_mechanism": "Curve steepening with official open interest flow down is an oi shock of covering or liquidation as the curve eases, not slope-as-level. Not price momentum.",
            "dataset": "same frozen official curve",
            "feature": "lagged steepening > 0 and lagged front_oi_change < 0",
            "target": "next-session front open-to-open after knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates",
            "failure_gate": "If failed, do not replace official OI with weekly positioning as a rescue of this family.",
        },
    ]


def search_space():
    for row in hypotheses():
        assert_new_mechanism(row["economic_mechanism"], family_id=None)
    return {
        "family_id": CUROI_ID,
        "family_code": FAMILY_ID,
        "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
        "hold_bars": HOLD_BARS,
        "seed": CUROI_SEED,
        "fdr_q": 0.05,
        "bootstrap_iterations": 2000,
        "permutation_iterations": 2000,
        "FINAL_OOS_ACCESS": "DENIED",
        "parents": "tm-fut-GLBX-CURVE-D1-20260829-000001",
        "do_not": [
            "Ava CFD as future or spot",
            "OI-rising-implies-buy",
            "slope as a level / backwardation cut",
            "retune steepening or OI sign or hold",
            "spend remaining Databento credits",
        ],
        "hypotheses": hypotheses(),
    }


def search_space_hash(space=None):
    payload = space or search_space()
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sealed_contract():
    space = search_space()
    digest = search_space_hash(space)
    space["search_space_hash"] = digest
    return space


def deny_oos():
    try:
        final_oos_access(reason="curve_oi_joint_v1_contract")
    except Exception as exc:
        if type(exc).__name__ != "FinalOosAccessDenied":
            raise
        return True
    raise RuntimeError("FINAL_OOS_WAS_NOT_DENIED")


def build_search_space():
    deny_oos()
    space = sealed_contract()
    if LOCKED_HASH and space.get("search_space_hash") != LOCKED_HASH:
        raise RuntimeError("CONTRACT_MISMATCH:%s" % space.get("search_space_hash"))
    space["hold_bars"] = HOLD_BARS
    space["close_fill"] = "FORBIDDEN"
    space["fill"] = "NEXT_BAR_OPEN"
    space["executed"] = False
    return space


def hypothesis_map(space=None):
    out = {}
    for hid in ALLOWED_HYPOTHESIS_IDS:
        row = dict(HYPOTHESIS_SPECS[hid])
        row["side"] = int(row.get("predicted_sign") or 1)
        row["hold_bars"] = HOLD_BARS
        out[hid] = row
    if space is None:
        return out
    for row in space.get("hypotheses") or []:
        hid = row.get("hypothesis_id")
        if hid in out:
            merged = dict(out[hid])
            merged.update(row)
            merged["event"] = HYPOTHESIS_SPECS[hid]["event"]
            merged["predicted_sign"] = HYPOTHESIS_SPECS[hid]["predicted_sign"]
            merged["hold_bars"] = HOLD_BARS
            out[hid] = merged
    return out
