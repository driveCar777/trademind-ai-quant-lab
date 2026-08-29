"""Locked FUT_CFD_LEAD space."""
from __future__ import print_function

import hashlib
import json

from research_engine.fut_cfd import (
    ABSORB_CFD,
    ABSORB_FUT,
    ALLOWED_HYPOTHESIS_IDS,
    FAMILY_ID,
    FUTCFD_ID,
    FUTCFD_SEED,
    GAP,
    GOLD_ID,
    HOLD_BARS,
    LOCKED_HASH,
    OIL_ID,
    CURVE_ID,
)
from research_engine.holdout import final_oos_access
from research_engine.v6_external.novelty import assert_new_mechanism


HYPOTHESIS_SPECS = {
    "HYP-FUTCFD-0001": {
        "hypothesis_id": "HYP-FUTCFD-0001",
        "name": "FUT_LEAD",
        "event": "FUT_LEAD",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "CFD",
    },
    "HYP-FUTCFD-0002": {
        "hypothesis_id": "HYP-FUTCFD-0002",
        "name": "CFD_OVERSHOOT",
        "event": "CFD_OVERSHOOT",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "target_asset": "CFD",
    },
    "HYP-FUTCFD-0003": {
        "hypothesis_id": "HYP-FUTCFD-0003",
        "name": "ABSORB",
        "event": "ABSORB",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "CFD",
    },
}


def hypotheses():
    return [
        {
            "hypothesis_id": "HYP-FUTCFD-0001",
            "name": "FUT_LEAD",
            "hypothesis": "When official front settlement return exceeds the broker CFD return by more than 20 bp, the CFD lagged the venue. After settlement knowledge, next CFD open-to-open is positive.",
            "economic_mechanism": "Official exchange settlement versus a parallel broker CFD quote is futures leadership / exchange basis, not price momentum and not treating broker GOLD as exchange spot.",
            "dataset": "%s + %s + %s" % (CURVE_ID, GOLD_ID, OIL_ID),
            "feature": "fut_ret - cfd_ret > %s" % GAP,
            "target": "next-session broker CFD open-to-open after settlement knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "quoted CFD spread floored at 2 bp one-way; no leverage",
            "validation": "pre-registered; leakage; knowledge-time; determinism; lineage; FDR q=0.05; four Xavier",
            "failure_gate": "If FALSIFIED, do not search the gap. Next = curve+OI joint.",
        },
        {
            "hypothesis_id": "HYP-FUTCFD-0002",
            "name": "CFD_OVERSHOOT",
            "hypothesis": "When the broker CFD return exceeds official settlement by more than 20 bp, the CFD ran ahead of the venue. Fade the CFD after knowledge.",
            "economic_mechanism": "CFD overshoot versus official settlement is quote disagreement and futures leadership in reverse, not a pair-to-metal lead and not price momentum.",
            "dataset": "same three frozen parents",
            "feature": "fut_ret - cfd_ret < -%s" % GAP,
            "target": "next-session broker CFD open-to-open after knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "quoted CFD spread floored at 2 bp one-way",
            "validation": "same gates",
            "failure_gate": "No hold search. Do not flip overshoot to continuation.",
        },
        {
            "hypothesis_id": "HYP-FUTCFD-0003",
            "name": "ABSORB",
            "hypothesis": "When official settlement rises more than 20 bp and the CFD barely moves, the CFD absorbed the venue move. After knowledge, CFD catches up.",
            "economic_mechanism": "Quote absorption: venue settlement moved, the broker quote stayed quiet. Exchange basis, not curve slope and not USDJPY to GOLD.",
            "dataset": "same three frozen parents",
            "feature": "fut_ret > %s and abs(cfd_ret) < %s" % (ABSORB_FUT, ABSORB_CFD),
            "target": "next-session broker CFD open-to-open after knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "quoted CFD spread floored at 2 bp one-way",
            "validation": "same gates",
            "failure_gate": "If failed, do not call GOLD spot. Next family is curve+OI joint.",
        },
    ]


def search_space():
    for row in hypotheses():
        assert_new_mechanism(row["economic_mechanism"], family_id=None)
    return {
        "family_id": FUTCFD_ID,
        "family_code": FAMILY_ID,
        "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
        "hold_bars": HOLD_BARS,
        "seed": FUTCFD_SEED,
        "fdr_q": 0.05,
        "bootstrap_iterations": 2000,
        "permutation_iterations": 2000,
        "FINAL_OOS_ACCESS": "DENIED",
        "parents": list((CURVE_ID, GOLD_ID, OIL_ID)),
        "gap": GAP,
        "do_not": [
            "call broker GOLD exchange spot",
            "USDJPY to GOLD",
            "search the 20 bp gap",
            "retune hold",
            "spend Databento credits",
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
        final_oos_access(reason="fut_cfd_lead_v1_contract")
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
