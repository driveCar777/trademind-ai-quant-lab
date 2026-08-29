"""Locked DTE_ROLL_WINDOW space. Hash is search-space only."""
from __future__ import print_function

import hashlib
import json

from research_engine.futures_dte import (
    ALLOWED_HYPOTHESIS_IDS,
    DTE_ID,
    DTE_SEED,
    FAMILY_ID,
    HOLD_BARS,
    LOCKED_HASH,
)
from research_engine.holdout import final_oos_access
from research_engine.v6_external.novelty import assert_new_mechanism


HYPOTHESIS_SPECS = {
    "HYP-FUTDTE-0001": {
        "hypothesis_id": "HYP-FUTDTE-0001",
        "name": "NEAR_EXPIRY",
        "event": "NEAR_EXPIRY",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-FUTDTE-0002": {
        "hypothesis_id": "HYP-FUTDTE-0002",
        "name": "FRONT_ROLL",
        "event": "FRONT_ROLL",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-FUTDTE-0003": {
        "hypothesis_id": "HYP-FUTDTE-0003",
        "name": "POST_ROLL",
        "event": "POST_ROLL",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
}


def hypotheses():
    return [
        {
            "hypothesis_id": "HYP-FUTDTE-0001",
            "name": "NEAR_EXPIRY",
            "hypothesis": "When days to expiry of the official front is 5 or fewer, roll congestion pressures the front. After settlement knowledge, next-session front return is negative.",
            "economic_mechanism": "Days to expiry near the official contract expiry is a calendar-structure roll window, not price momentum and not curve slope.",
            "dataset": "Derived OI-flow panel days_to_expiry / front symbol. $0. No new Databento bytes.",
            "feature": "days_to_expiry <= 5 on the official front",
            "target": "next-session front open-to-open after settlement knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps research cost; no leverage",
            "validation": "pre-registered; leakage; knowledge-time; determinism; lineage; FDR q=0.05; four Xavier",
            "failure_gate": "If FALSIFIED, do not search dte cut. Next is fusion or EXTERNAL_DATA_GATE.",
        },
        {
            "hypothesis_id": "HYP-FUTDTE-0002",
            "name": "FRONT_ROLL",
            "hypothesis": "When the official front contract identity changes, the new front is the roll. After settlement knowledge, next-session new-front return is positive.",
            "economic_mechanism": "A days to expiry reset via official front identity change is the exchange roll, not a slope cut and not price momentum.",
            "dataset": "same derived panel front symbol",
            "feature": "front raw_symbol changes versus previous session",
            "target": "next-session front open-to-open after knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates; not a z_cut search",
            "failure_gate": "No hold search. Do not flip roll to fade as a rescue.",
        },
        {
            "hypothesis_id": "HYP-FUTDTE-0003",
            "name": "POST_ROLL",
            "hypothesis": "The session after an official front roll, residual roll flow continues. After settlement knowledge, next-session front return is positive.",
            "economic_mechanism": "Post-roll flow is the day after the days to expiry identity change, not open-interest covering and not curve inversion. Not price momentum.",
            "dataset": "same derived panel",
            "feature": "previous session was a front identity change",
            "target": "next-session front open-to-open after knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates",
            "failure_gate": "If failed, do not replace DTE with slope. Next is unused fusion or purchase case.",
        },
    ]


def search_space():
    for row in hypotheses():
        assert_new_mechanism(row["economic_mechanism"], family_id=None)
    return {
        "family_id": DTE_ID,
        "family_code": FAMILY_ID,
        "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
        "hold_bars": HOLD_BARS,
        "seed": DTE_SEED,
        "fdr_q": 0.05,
        "bootstrap_iterations": 2000,
        "permutation_iterations": 2000,
        "FINAL_OOS_ACCESS": "DENIED",
        "parents": "tm-fut-GLBX-OIFLOW-D1-20260830-000001",
        "do_not": [
            "Ava CFD as future or spot",
            "price momentum on front only",
            "retune dte cut/hold",
            "reuse TERM_STRUCTURE slope",
            "reuse OI or volume events",
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
        final_oos_access(reason="futures_dte_v1_contract")
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
