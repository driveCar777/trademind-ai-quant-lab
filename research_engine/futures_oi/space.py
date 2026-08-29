"""Locked FUTURES_OI_FLOW space. Hash is search-space only."""
from __future__ import print_function

import hashlib
import json

from research_engine.futures_oi import (
    ALLOWED_HYPOTHESIS_IDS,
    FAMILY_ID,
    HOLD_BARS,
    LOCKED_HASH,
    OI_ID,
    OI_SEED,
)
from research_engine.holdout import final_oos_access
from research_engine.v6_external.novelty import assert_new_mechanism


HYPOTHESIS_SPECS = {
    "HYP-FUTOI-0001": {
        "hypothesis_id": "HYP-FUTOI-0001",
        "name": "NEW_LONGS",
        "event": "NEW_LONGS",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-FUTOI-0002": {
        "hypothesis_id": "HYP-FUTOI-0002",
        "name": "SHORT_COVER",
        "event": "SHORT_COVER",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-FUTOI-0003": {
        "hypothesis_id": "HYP-FUTOI-0003",
        "name": "NEW_SHORTS",
        "event": "NEW_SHORTS",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
}


def hypotheses():
    return [
        {
            "hypothesis_id": "HYP-FUTOI-0001",
            "name": "NEW_LONGS",
            "hypothesis": "When official front contract open interest rises with the same-session settlement, new longs are being added. After OI knowledge T+1 21:00Z, next-session front return is positive.",
            "economic_mechanism": "Official contract open interest flow confirms a price rise as new longs, an oi shock of fresh demand, not short covering and not curve slope. Not price momentum.",
            "dataset": "Derived OI-flow panel from frozen GLBX GC/CL curve. No new Databento bytes.",
            "feature": "front_oi_change > 0 and settlement change > 0, lagged to OI knowledge",
            "target": "next-session front open-to-open after OI knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps research cost; no leverage",
            "validation": "pre-registered; leakage; knowledge-time; determinism; lineage; FDR q=0.05; four Xavier",
            "failure_gate": "If FALSIFIED, do not retune OI sign or hold. Next = volume x price rescan at $0.",
        },
        {
            "hypothesis_id": "HYP-FUTOI-0002",
            "name": "SHORT_COVER",
            "hypothesis": "When settlement rises while official front open interest falls, the rise is short covering. After OI knowledge, fade the covering bounce.",
            "economic_mechanism": "Contract open interest decline with a higher settlement is short covering, an oi shock that is not new demand. Fade after knowledge time. Not price momentum.",
            "dataset": "same derived OI-flow panel",
            "feature": "front_oi_change < 0 and settlement change > 0, lagged to OI knowledge",
            "target": "next-session front open-to-open after knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates; not a z_cut search",
            "failure_gate": "No hold search. Do not flip covering to continuation as a rescue.",
        },
        {
            "hypothesis_id": "HYP-FUTOI-0003",
            "name": "NEW_SHORTS",
            "hypothesis": "When settlement falls while official front open interest rises, new shorts are being added. After OI knowledge, next-session front return is negative.",
            "economic_mechanism": "Official contract open interest rising into a lower settlement is an oi shock of new shorts, not a curve inversion. Not price momentum.",
            "dataset": "same derived OI-flow panel",
            "feature": "front_oi_change > 0 and settlement change < 0, lagged to OI knowledge",
            "target": "next-session front open-to-open after knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates",
            "failure_gate": "If failed, do not replace official OI with COT. Next family is volume x price.",
        },
    ]


def search_space():
    for row in hypotheses():
        assert_new_mechanism(row["economic_mechanism"], family_id=None)
    return {
        "family_id": OI_ID,
        "family_code": FAMILY_ID,
        "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
        "hold_bars": HOLD_BARS,
        "seed": OI_SEED,
        "fdr_q": 0.05,
        "bootstrap_iterations": 2000,
        "permutation_iterations": 2000,
        "FINAL_OOS_ACCESS": "DENIED",
        "parents": "tm-fut-GLBX-OIFLOW-D1-20260830-000001",
        "do_not": [
            "Ava CFD as future or spot",
            "price momentum on front only",
            "retune OI sign/hold",
            "reuse TERM_STRUCTURE slope",
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
        final_oos_access(reason="futures_oi_flow_v1_contract")
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
