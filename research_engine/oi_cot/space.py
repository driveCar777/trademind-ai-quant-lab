"""Locked OI_COT_BUILD space. Hash is search-space only."""
from __future__ import print_function

import hashlib
import json

from research_engine.holdout import final_oos_access
from research_engine.oi_cot import (
    ALLOWED_HYPOTHESIS_IDS,
    FAMILY_ID,
    HOLD_BARS,
    LOCKED_HASH,
    OICOT_ID,
    OICOT_SEED,
)
from research_engine.v6_external.novelty import assert_new_mechanism


HYPOTHESIS_SPECS = {
    "HYP-OICOT-0001": {
        "hypothesis_id": "HYP-OICOT-0001",
        "name": "BUILD_ALIGN",
        "event": "BUILD_ALIGN",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-OICOT-0002": {
        "hypothesis_id": "HYP-OICOT-0002",
        "name": "SPEED_GAP",
        "event": "SPEED_GAP",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-OICOT-0003": {
        "hypothesis_id": "HYP-OICOT-0003",
        "name": "UNWIND_ALIGN",
        "event": "UNWIND_ALIGN",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
}


def hypotheses():
    return [
        {
            "hypothesis_id": "HYP-OICOT-0001",
            "name": "BUILD_ALIGN",
            "hypothesis": "When official daily open interest flow and weekly positioning both rise in the same census week, a build is confirmed after Friday knowledge. Next-session front return is negative.",
            "economic_mechanism": "Daily official open interest flow plus weekly positioning change in the same direction is a position build, a speed-aligned crowding transition, not a COT extreme. Not price momentum.",
            "dataset": "Frozen GLBX curve OI plus CFTC GOLD/OIL weekly series. No new Databento bytes.",
            "feature": "week-sum official front_oi_change > 0 and weekly mm_net change > 0, after Friday 21:00Z",
            "target": "next-session front open-to-open after Friday knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps research cost; no leverage",
            "validation": "pre-registered; leakage; knowledge-time; determinism; lineage; FDR q=0.05; four Xavier",
            "failure_gate": "If FALSIFIED, do not retune OI or weekly positioning sign. Next = EIA wow x CL curve.",
        },
        {
            "hypothesis_id": "HYP-OICOT-0002",
            "name": "SPEED_GAP",
            "hypothesis": "When official daily open interest expands while weekly positioning falls, exchange participation and the delayed census disagree. After Friday knowledge, next-session front return is positive.",
            "economic_mechanism": "Daily official open interest flow up against a weekly positioning unwind is a speed gap between the exchange clock and the census clock, not a COT extreme. Not price momentum.",
            "dataset": "same frozen official OI plus weekly positioning",
            "feature": "week-sum official front_oi_change > 0 and weekly mm_net change < 0",
            "target": "next-session front open-to-open after Friday knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates; not a z score search",
            "failure_gate": "No hold search. Do not replace weekly positioning with a COT extreme as a rescue.",
        },
        {
            "hypothesis_id": "HYP-OICOT-0003",
            "name": "UNWIND_ALIGN",
            "hypothesis": "When official daily open interest and weekly positioning both fall, an unwind is confirmed after Friday knowledge. Next-session front return is positive.",
            "economic_mechanism": "Daily official open interest flow down plus weekly positioning unwind is a confirmed position unwinding, not a COT extreme. Not price momentum.",
            "dataset": "same frozen official OI plus weekly positioning",
            "feature": "week-sum official front_oi_change < 0 and weekly mm_net change < 0",
            "target": "next-session front open-to-open after Friday knowledge_time",
            "horizon": HOLD_BARS,
            "cost": "one-way 2 bps",
            "validation": "same gates",
            "failure_gate": "If failed, do not reopen POSITIONING_V1 extremes.",
        },
    ]


def search_space():
    for row in hypotheses():
        assert_new_mechanism(row["economic_mechanism"], family_id=None)
    return {
        "family_id": OICOT_ID,
        "family_code": FAMILY_ID,
        "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
        "hold_bars": HOLD_BARS,
        "seed": OICOT_SEED,
        "fdr_q": 0.05,
        "bootstrap_iterations": 2000,
        "permutation_iterations": 2000,
        "FINAL_OOS_ACCESS": "DENIED",
        "parents": "tm-fut-GLBX-CURVE-D1-20260829-000001 + CFTC GOLD/OIL 000002",
        "do_not": [
            "COT extreme / mm_net_oi z",
            "weekly cot token reuse",
            "Ava CFD as future or spot",
            "retune OI or weekly positioning sign or hold",
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
        final_oos_access(reason="oi_cot_build_v1_contract")
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
