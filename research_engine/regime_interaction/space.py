from __future__ import print_function

from research_engine.holdout import final_oos_access
from research_engine.regime_interaction import (
    ALLOWED_HYPOTHESIS_IDS,
    FAMILY_ID,
    HOLD_BARS,
    PARENTS,
    RI_ID,
    RI_SEED,
    RV_N,
    SELF_N,
)
from research_protocol.hashing import canonical_hash


CANONICAL_PAYLOAD = {
    "close_fill": "FORBIDDEN",
    "cost": {"commission_bp_per_side": 5.0, "slippage_bp_per_side": 10.0, "spread": "BROKER_POINTS_RULE"},
    "discovery_id": RI_ID,
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
    "not_v08": True,
    "not_v09": True,
    "not_v091": True,
    "not_weekday": True,
    "parent_datasets": list(PARENTS),
    "relative_vol": {"cross_level": 1.0, "rv_n": RV_N, "self_n": SELF_N},
    "risk": {"leverage_cap": 1.0, "risk_frac": 0.005, "stop_atr_mult": 1.5},
    "seed": RI_SEED,
    "stats": {"block_length": 5, "bootstrap": 2000, "fdr_q": 0.05, "m": 3, "permutation": 2000},
    "timeframe": "H1",
    "windows": {"FINAL_OOS_ACCESS": "DENIED", "split": "70/15/15_on_each_target_own_h1_dates"},
}

HYPOTHESIS_SPECS = {
    "HYP-RI-0001": {
        "hypothesis_id": "HYP-RI-0001",
        "target_asset": "GOLD",
        "event": "GOLD_RELVOL_CROSSES_CHEAP",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Gold realized vol crosses cheap vs oil; bid the quieter metal.",
    },
    "HYP-RI-0002": {
        "hypothesis_id": "HYP-RI-0002",
        "target_asset": "OIL",
        "event": "OIL_RELVOL_CROSSES_CHEAP",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Oil realized vol crosses cheap vs gold; bid the quieter commodity.",
    },
    "HYP-RI-0003": {
        "hypothesis_id": "HYP-RI-0003",
        "target_asset": "GOLD",
        "event": "JOINT_VOL_SHOCK",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Joint gold+oil vol shock; risk-on bounce into gold. Not V0.9 single-asset tercile.",
    },
}


def deny_oos():
    try:
        final_oos_access(reason="regime_interaction_v1")
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
    return row


def build_search_space():
    deny_oos()
    from research_engine.regime_interaction import LOCKED_HASH

    digest = canonical_search_space_hash()
    if LOCKED_HASH and digest != LOCKED_HASH:
        raise RuntimeError("CONTRACT_MISMATCH:%s" % digest)
    space = dict(CANONICAL_PAYLOAD)
    space["search_space_hash"] = digest
    space["hypotheses"] = [_with_side(HYPOTHESIS_SPECS[hid]) for hid in ALLOWED_HYPOTHESIS_IDS]
    space["FINAL_OOS_ACCESS"] = "DENIED"
    return space


def hypothesis_map(space=None):
    if space is None:
        return dict((hid, _with_side(HYPOTHESIS_SPECS[hid])) for hid in ALLOWED_HYPOTHESIS_IDS)
    return dict((row["hypothesis_id"], _with_side(row)) for row in (space.get("hypotheses") or []))
