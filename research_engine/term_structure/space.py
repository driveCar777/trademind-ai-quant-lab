"""Locked TERM_STRUCTURE space. Hash is sealed_contract(); parents stay unassigned in the hash."""
from __future__ import print_function

from research_engine.holdout import final_oos_access
from research_engine.term_structure import (
    ALLOWED_HYPOTHESIS_IDS,
    HOLD_BARS,
    LOCKED_HASH,
    TS_HOLD,
)
from research_engine.v6_external.contract import sealed_contract


HYPOTHESIS_SPECS = {
    "HYP-TSFUT-0001": {
        "hypothesis_id": "HYP-TSFUT-0001",
        "name": "BACKWARDATION_TIGHTNESS",
        "event": "BACKWARDATION",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-TSFUT-0002": {
        "hypothesis_id": "HYP-TSFUT-0002",
        "name": "STEEPENING_SHOCK",
        "event": "STEEPENING",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
    "HYP-TSFUT-0003": {
        "hypothesis_id": "HYP-TSFUT-0003",
        "name": "POSITIVE_ROLL_YIELD",
        "event": "POSITIVE_ROLL",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "target_asset": "FRONT",
    },
}


def deny_oos():
    try:
        final_oos_access(reason="term_structure_v1_contract")
    except Exception as exc:
        if type(exc).__name__ != "FinalOosAccessDenied":
            raise
        return True
    raise RuntimeError("FINAL_OOS_WAS_NOT_DENIED")


def build_search_space():
    deny_oos()
    space = sealed_contract()
    if space.get("search_space_hash") != LOCKED_HASH:
        raise RuntimeError("CONTRACT_MISMATCH:%s" % space.get("search_space_hash"))
    space["hold_bars"] = TS_HOLD
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
