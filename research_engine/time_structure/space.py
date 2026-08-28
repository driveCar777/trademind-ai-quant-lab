"""Locked session-open space. Worker cannot add IDs or invent sessions."""
from __future__ import print_function

from research_engine.holdout import final_oos_access
from research_engine.time_structure import (
    ALLOWED_HYPOTHESIS_IDS,
    FAMILY_ID,
    HOLD_BARS,
    PARENTS,
    TS_ID,
    TS_SEED,
)
from research_protocol.hashing import canonical_hash


CANONICAL_PAYLOAD = {
    "close_fill": "FORBIDDEN",
    "cost": {
        "commission_bp_per_side": 5.0,
        "slippage_bp_per_side": 10.0,
        "spread": "BROKER_POINTS_RULE",
    },
    "discovery_id": TS_ID,
    "family_id": FAMILY_ID,
    "fill": "NEXT_BAR_OPEN",
    "gates": {
        "insufficient_occupancy": "FAIL_NOT_WIDEN",
        "occupancy_max": 0.40,
        "program_candidate": "FDR_AND_BOTH_TARGETS_AFTER_COST",
        "research_n_trade_min": 8,
        "validation_n_trade_min": 4,
    },
    "hold_bars": HOLD_BARS,
    "horizon": "SIGNAL_PLUS_HOLD_OWN_DATES",
    "hypothesis_count": 3,
    "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
    "not_institutional_time": True,
    "not_weekday": True,
    "parent_datasets": list(PARENTS),
    "risk": {"leverage_cap": 1.0, "risk_frac": 0.005, "stop_atr_mult": 1.5},
    "seed": TS_SEED,
    "sessions": {
        "LONDON_OPEN_H1": {
            "dst": "EU_LAST_SUNDAY_MARCH_OCTOBER",
            "local_hour": 8,
            "tz": "Europe/London",
        },
        "NY_FX_OPEN_H1": {
            "dst": "US_SECOND_SUNDAY_MARCH_FIRST_SUNDAY_NOVEMBER",
            "local_hour": 8,
            "tz": "America/New_York",
        },
    },
    "stats": {
        "block_length": 5,
        "bootstrap": 2000,
        "fdr_q": 0.05,
        "m": 3,
        "permutation": 2000,
    },
    "timeframe": "H1",
    "windows": {
        "FINAL_OOS_ACCESS": "DENIED",
        "split": "70/15/15_on_each_target_own_h1_dates",
    },
}

HYPOTHESIS_SPECS = {
    "HYP-TS-0001": {
        "hypothesis_id": "HYP-TS-0001",
        "kind": "LONDON_OPEN",
        "target_asset": "GOLD",
        "event": "LONDON_OPEN_H1",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "London cash open inventory reprice into gold.",
    },
    "HYP-TS-0002": {
        "hypothesis_id": "HYP-TS-0002",
        "kind": "LONDON_OPEN",
        "target_asset": "OIL",
        "event": "LONDON_OPEN_H1",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "London cash open inventory reprice into oil.",
    },
    "HYP-TS-0003": {
        "hypothesis_id": "HYP-TS-0003",
        "kind": "NY_FX_OPEN",
        "target_asset": "GOLD",
        "event": "NY_FX_OPEN_H1",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "New York FX cash open inventory reprice into gold.",
    },
}


def deny_oos():
    try:
        final_oos_access(reason="time_structure_v1_contract")
    except Exception as exc:
        if type(exc).__name__ != "FinalOosAccessDenied":
            raise
        return True
    raise RuntimeError("FINAL_OOS_WAS_NOT_DENIED")


def canonical_search_space_hash():
    return canonical_hash(CANONICAL_PAYLOAD)


def _with_side(spec):
    row = dict(spec)
    row["side"] = int(row.get("predicted_sign") or 1)
    row["target"] = row.get("target_asset")
    row["hold_bars"] = HOLD_BARS
    return row


def build_search_space():
    deny_oos()
    from research_engine.time_structure import LOCKED_HASH

    digest = canonical_search_space_hash()
    if LOCKED_HASH and digest != LOCKED_HASH:
        raise RuntimeError("CONTRACT_MISMATCH:%s" % digest)
    space = dict(CANONICAL_PAYLOAD)
    space["search_space_hash"] = digest
    space["hypotheses"] = [_with_side(HYPOTHESIS_SPECS[hid]) for hid in ALLOWED_HYPOTHESIS_IDS]
    space["FINAL_OOS_ACCESS"] = "DENIED"
    space["executed"] = False
    return space


def hypothesis_map(space=None):
    if space is None:
        return dict((hid, _with_side(HYPOTHESIS_SPECS[hid])) for hid in ALLOWED_HYPOTHESIS_IDS)
    out = {}
    for row in space.get("hypotheses") or []:
        hid = row.get("hypothesis_id")
        if hid in HYPOTHESIS_SPECS:
            merged = dict(HYPOTHESIS_SPECS[hid])
            merged.update(row)
            out[hid] = _with_side(merged)
        else:
            out[hid] = _with_side(row)
    return out
