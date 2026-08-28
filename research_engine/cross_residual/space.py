"""Locked V0.91 space. Reproduce the paper hash. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.cross_residual import (
    ALLOWED_HYPOTHESIS_IDS,
    FAMILY_ID,
    HOLD_BARS,
    LOCKED_HASH,
    PARENTS,
    SMA_N,
    XR_BLOCK,
    XR_BOOT,
    XR_ID,
    XR_PERM,
    XR_SEED,
)
from research_protocol.hashing import canonical_hash


CANONICAL_PAYLOAD = {
    "align_method": "INNER_JOIN_GOLD_OIL",
    "close_fill": "FORBIDDEN",
    "cost": {
        "commission_bp_per_side": 5.0,
        "slippage_bp_per_side": 10.0,
        "spread": "BROKER_POINTS_RULE",
    },
    "discovery_id": XR_ID,
    "family_id": FAMILY_ID,
    "fill": "NEXT_BAR_OPEN",
    "hold_bars": HOLD_BARS,
    "horizon": "SIGNAL_PLUS_HOLD_ALIGNED_ROWS",
    "hypothesis_count": 3,
    "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
    "parent_datasets": list(PARENTS),
    "residual": "LOG_GOLD_OVER_OIL_MINUS_SMA60",
    "risk": {"leverage_cap": 1.0, "risk_frac": 0.005, "stop_atr_mult": 1.5},
    "seed": XR_SEED,
    "stats": {
        "block_length": XR_BLOCK,
        "bootstrap": XR_BOOT,
        "fdr_q": 0.05,
        "m": 3,
        "permutation": XR_PERM,
    },
    "timeframe": "D1",
    "windows": {
        "FINAL_OOS_ACCESS": "DENIED",
        "split": "70/15/15_on_aligned_gold_oil_dates",
    },
}

HYPOTHESIS_SPECS = {
    "HYP-XR-0001": {
        "hypothesis_id": "HYP-XR-0001",
        "kind": "RICH",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "sma_n": SMA_N,
    },
    "HYP-XR-0002": {
        "hypothesis_id": "HYP-XR-0002",
        "kind": "CHEAP",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "sma_n": SMA_N,
    },
    "HYP-XR-0003": {
        "hypothesis_id": "HYP-XR-0003",
        "kind": "JOINT_RISKOFF",
        "predicted_sign": 0,
        "hold_bars": HOLD_BARS,
        "sma_n": SMA_N,
    },
}


def canonical_search_space_hash():
    return canonical_hash(CANONICAL_PAYLOAD)


def build_search_space():
    digest = canonical_search_space_hash()
    if digest != LOCKED_HASH:
        raise RuntimeError("CONTRACT_MISMATCH")
    space = dict(CANONICAL_PAYLOAD)
    space["search_space_hash"] = digest
    space["hypotheses"] = [dict(HYPOTHESIS_SPECS[hid]) for hid in ALLOWED_HYPOTHESIS_IDS]
    space["FINAL_OOS_ACCESS"] = "DENIED"
    return space
