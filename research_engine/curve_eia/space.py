"""Locked CURVE_EIA_REPRICE space. Hash is search-space only."""
from __future__ import print_function

import hashlib
import json

from research_engine.curve_eia import (
    ALLOWED_HYPOTHESIS_IDS,
    CUEIA_ID,
    CUEIA_SEED,
    FAMILY_ID,
    HOLD_BARS,
    LOCKED_HASH,
)
from research_engine.holdout import final_oos_access
from research_engine.v6_external.novelty import assert_new_mechanism


HYPOTHESIS_SPECS = {
    "HYP-CUEIA-0001": {
        "hypothesis_id": "HYP-CUEIA-0001",
        "name": "INV_BUILD_STEEPEN",
        "event": "INV_BUILD_STEEPEN",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-CUEIA-0002": {
        "hypothesis_id": "HYP-CUEIA-0002",
        "name": "INV_DRAW_FLATTEN",
        "event": "INV_DRAW_FLATTEN",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-CUEIA-0003": {
        "hypothesis_id": "HYP-CUEIA-0003",
        "name": "INV_DRAW_STEEPEN",
        "event": "INV_DRAW_STEEPEN",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
}


def hypotheses():
    return [
        {
            "hypothesis_id": "HYP-CUEIA-0001",
            "name": "INV_BUILD_STEEPEN",
            "hypothesis": "When US crude stocks rise week-over-week and the official CL curve steepens, storage is richer. After Wednesday 16:00Z knowledge, next-session CL front return is negative.",
            "economic_mechanism": "EIA inventory change curve repricing: stocks wow up plus CL curve steepening means the physical build is already in the deferred premium. Not inventory z-score. Not price momentum.",
            "dataset": "Frozen GLBX CL curve plus EIA WCESTUS1. No new Databento bytes.",
            "feature": "EIA stocks wow > 0 and last known CL steepening > 0, after Wednesday 16:00Z",
            "target": "next-session CL front open-to-open after Wednesday knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps research cost; no leverage",
            "validation": "pre-registered; leakage; knowledge-time; determinism; lineage; FDR q=0.05; four Xavier",
            "failure_gate": "If FALSIFIED, do not retune wow or steepening. Next = UST10 change x GC curve.",
        },
        {
            "hypothesis_id": "HYP-CUEIA-0002",
            "name": "INV_DRAW_FLATTEN",
            "hypothesis": "When US crude stocks fall week-over-week and the official CL curve flattens, tightness is rising with a physical draw. After Wednesday knowledge, next-session CL front return is positive.",
            "economic_mechanism": "Inventory change curve: stocks wow down plus curve steepening reversed (flattening) is a tightness repricing, not an inventory z-score. Not price momentum.",
            "dataset": "same frozen CL curve plus EIA stocks",
            "feature": "EIA stocks wow < 0 and last known CL steepening < 0",
            "target": "next-session CL front open-to-open after Wednesday knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates; not a z score search",
            "failure_gate": "No hold search. Do not reopen INVENTORY_V1 z-cross as a rescue.",
        },
        {
            "hypothesis_id": "HYP-CUEIA-0003",
            "name": "INV_DRAW_STEEPEN",
            "hypothesis": "When US crude stocks fall while the official CL curve steepens, the physical draw and the curve disagree. After Wednesday knowledge, next-session CL front return is positive.",
            "economic_mechanism": "Inventory change curve disagreement: stocks wow down with CL curve steepening is a delayed tightness signal, not inventory z-score. Not price momentum.",
            "dataset": "same frozen CL curve plus EIA stocks",
            "feature": "EIA stocks wow < 0 and last known CL steepening > 0",
            "target": "next-session CL front open-to-open after Wednesday knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates",
            "failure_gate": "If failed, do not replace wow sign with a standardized inventory threshold.",
        },
    ]


def search_space():
    for row in hypotheses():
        assert_new_mechanism(row["economic_mechanism"], family_id=None)
    return {
        "family_id": CUEIA_ID,
        "family_code": FAMILY_ID,
        "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
        "hold_bars": HOLD_BARS,
        "seed": CUEIA_SEED,
        "fdr_q": 0.05,
        "bootstrap_iterations": 2000,
        "permutation_iterations": 2000,
        "FINAL_OOS_ACCESS": "DENIED",
        "parents": "tm-fut-GLBX-CURVE-D1-20260829-000001 + EIA WCESTUS1",
        "do_not": [
            "inventory z-score / wow z-cross",
            "Ava CFD as future or spot",
            "retune wow or steepening or hold",
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
        final_oos_access(reason="curve_eia_reprice_v1_contract")
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
