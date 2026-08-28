"""Locked COT space. Worker cannot change z_cut or invent IDs."""
from __future__ import print_function

from research_engine.holdout import final_oos_access
from research_engine.positioning import (
    ALLOWED_HYPOTHESIS_IDS,
    FAMILY_ID,
    FEATURE_PARENTS,
    HOLD_BARS,
    PARENTS,
    POS_ID,
    POS_SEED,
    Z_CUT,
    Z_LOOKBACK,
)
from research_protocol.hashing import canonical_hash


CANONICAL_PAYLOAD = {
    "close_fill": "FORBIDDEN",
    "cost": {
        "commission_bp_per_side": 5.0,
        "slippage_bp_per_side": 10.0,
        "spread": "BROKER_POINTS_RULE",
    },
    "cot_params": {
        "z_cut": Z_CUT,
        "z_lookback": Z_LOOKBACK,
    },
    "discovery_id": POS_ID,
    "family_id": FAMILY_ID,
    "feature_datasets": list(FEATURE_PARENTS),
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
    "knowledge_time_rule": "CFTC_Tuesday_asof_plus_Friday_21:00Z_then_NEXT_BAR_OPEN",
    "not_v08_price_proxy": True,
    "not_zcut_search": True,
    "parent_datasets": list(PARENTS),
    "risk": {"leverage_cap": 1.0, "risk_frac": 0.005, "stop_atr_mult": 1.5},
    "seed": POS_SEED,
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
    "HYP-POS-0001": {
        "hypothesis_id": "HYP-POS-0001",
        "target_asset": "GOLD",
        "event": "MM_WASH_CROSS",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Gold managed-money net/OI z-cross below -2: speculator washout then bounce.",
    },
    "HYP-POS-0002": {
        "hypothesis_id": "HYP-POS-0002",
        "target_asset": "OIL",
        "event": "MM_WASH_CROSS",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Oil managed-money net/OI z-cross below -2: speculator washout then bounce.",
    },
    "HYP-POS-0003": {
        "hypothesis_id": "HYP-POS-0003",
        "target_asset": "GOLD",
        "event": "COM_LONG_CROSS",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Gold commercial net/OI z-cross above +2: commercials unusually long, subsequent gold bid.",
    },
}


def deny_oos():
    try:
        final_oos_access(reason="positioning_v1_contract")
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
    from research_engine.positioning import LOCKED_HASH

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
