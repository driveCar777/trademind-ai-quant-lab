"""INSTITUTIONAL_TIME_V1.0 paper contract. No runner. Do not execute."""
from __future__ import print_function

from research_engine.holdout import final_oos_access
from research_protocol.hashing import canonical_hash


IT_ID = "INSTITUTIONAL_TIME_V1.0"
FAMILY_ID = "FAM-IT-CALENDAR-0001"
IT_SEED = 20260825
HOLD_BARS = 5
ALLOWED_HYPOTHESIS_IDS = ("HYP-IT-0001", "HYP-IT-0002", "HYP-IT-0003")
PARENTS = (
    "tm-market-GOLD-D1-20260825-000001",
    "tm-market-OIL-D1-20260825-000001",
)
# Locked after first canonical_hash of CANONICAL_PAYLOAD.
LOCKED_HASH = "1d3c4a1fb628465fed18b4af978d767c2ffbe3f8d6ea23233da01aed3d524457"


CANONICAL_PAYLOAD = {
    "calendar": {
        "kind": "INSTITUTIONAL_MONTH_TURN",
        "not_weekday": True,
        "window": "SINGLE_BAR_EVENT",
        "widen_after_pnl": "FORBIDDEN",
    },
    "close_fill": "FORBIDDEN",
    "cost": {
        "commission_bp_per_side": 5.0,
        "slippage_bp_per_side": 10.0,
        "spread": "BROKER_POINTS_RULE",
    },
    "discovery_id": IT_ID,
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
    "parent_datasets": list(PARENTS),
    "risk": {"leverage_cap": 1.0, "risk_frac": 0.005, "stop_atr_mult": 1.5},
    "seed": IT_SEED,
    "stats": {
        "block_length": 5,
        "bootstrap": 2000,
        "fdr_q": 0.05,
        "m": 3,
        "permutation": 2000,
    },
    "timeframe": "D1",
    "windows": {
        "FINAL_OOS_ACCESS": "DENIED",
        "split": "70/15/15_on_each_target_own_d1_dates",
    },
}

HYPOTHESIS_SPECS = {
    "HYP-IT-0001": {
        "hypothesis_id": "HYP-IT-0001",
        "kind": "MONTH_END",
        "target_asset": "GOLD",
        "event": "LAST_D1_BAR_OF_CALENDAR_MONTH",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Month-end benchmark/commodity-book rebalance into gold.",
    },
    "HYP-IT-0002": {
        "hypothesis_id": "HYP-IT-0002",
        "kind": "MONTH_END",
        "target_asset": "OIL",
        "event": "LAST_D1_BAR_OF_CALENDAR_MONTH",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Same month-end commodity-book rebalance into oil.",
    },
    "HYP-IT-0003": {
        "hypothesis_id": "HYP-IT-0003",
        "kind": "MONTH_START",
        "target_asset": "GOLD",
        "event": "FIRST_D1_BAR_OF_CALENDAR_MONTH",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Turn-of-month new-month allocation into gold.",
    },
}


def deny_oos():
    try:
        final_oos_access(reason="institutional_time_v10_contract")
    except Exception as exc:
        if type(exc).__name__ != "FinalOosAccessDenied":
            raise
        return True
    raise RuntimeError("FINAL_OOS_WAS_NOT_DENIED")


def canonical_search_space_hash():
    return canonical_hash(CANONICAL_PAYLOAD)


def build_search_space():
    deny_oos()
    digest = canonical_search_space_hash()
    if digest != LOCKED_HASH:
        raise RuntimeError("CONTRACT_MISMATCH:%s" % digest)
    space = dict(CANONICAL_PAYLOAD)
    space["search_space_hash"] = digest
    space["hypotheses"] = [dict(HYPOTHESIS_SPECS[hid]) for hid in ALLOWED_HYPOTHESIS_IDS]
    space["FINAL_OOS_ACCESS"] = "DENIED"
    space["executed"] = False
    space["runner"] = "NONE"
    return space
