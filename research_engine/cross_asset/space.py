"""Locked V0.8 space. Hypotheses come from this file, not from the worker."""
from __future__ import print_function

from research_engine.cross_asset import (
    ALIGNED_END,
    ALIGNED_N,
    ALIGNED_START,
    ALLOWED_HYPOTHESIS_IDS,
    CROSS_BLOCK,
    CROSS_BOOT,
    CROSS_FDR_M,
    CROSS_FDR_Q,
    CROSS_ID,
    CROSS_PERM,
    CROSS_SEED,
    FAMILY_ID,
    LOCKED_HASH,
    PARENTS,
)
from research_protocol.hashing import canonical_hash


# Exact payload from CROSS_ASSET_ALPHA_V0.8_CONTRACT.md section 11.
CANONICAL_PAYLOAD = {
    "align_key": "UTC_DATE",
    "align_method": "INNER_JOIN_ALL_FOUR",
    "aligned_end": ALIGNED_END,
    "aligned_n_dates": ALIGNED_N,
    "aligned_start": ALIGNED_START,
    "close_fill": "FORBIDDEN",
    "cost": {
        "commission_bp_per_side": 5.0,
        "slippage_bp_per_side": 10.0,
        "spread": "BROKER_POINTS_RULE",
    },
    "discovery_id": CROSS_ID,
    "family_id": FAMILY_ID,
    "fill": "NEXT_BAR_OPEN",
    "horizon": "NEXT_ALIGNED_ROW",
    "hypothesis_count": 3,
    "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
    "parent_datasets": list(PARENTS),
    "risk": {"leverage_cap": 1.0, "risk_frac": 0.005, "stop_atr_mult": 1.5},
    "same_window_pair": True,
    "seed": CROSS_SEED,
    "stats": {
        "block_length": CROSS_BLOCK,
        "bootstrap": CROSS_BOOT,
        "fdr_q": CROSS_FDR_Q,
        "m": CROSS_FDR_M,
        "permutation": CROSS_PERM,
    },
    "timeframe": "D1",
    "windows": {
        "FINAL_OOS_ACCESS": "DENIED",
        "final_oos": ["2025-09-11", "2026-08-25"],
        "research": ["2020-04-01", "2024-09-26"],
        "split": "70/15/15_on_sorted_aligned_dates",
        "validation": ["2024-09-27", "2025-09-10"],
    },
}

# Evaluation specs. Worker may only use IDs listed in CANONICAL_PAYLOAD.
HYPOTHESIS_SPECS = {
    "HYP-XA-0001": {
        "hypothesis_id": "HYP-XA-0001",
        "input_assets": ["USDJPY"],
        "target_asset": "GOLD",
        "kind": "Q3",
        "predicted_sign": -1,
        "side": -1,
    },
    "HYP-XA-0002": {
        "hypothesis_id": "HYP-XA-0002",
        "input_assets": ["EURUSD"],
        "target_asset": "GOLD",
        "kind": "Q3",
        "predicted_sign": 1,
        "side": 1,
    },
    "HYP-XA-0003": {
        "hypothesis_id": "HYP-XA-0003",
        "input_assets": ["USDJPY", "EURUSD"],
        "target_asset": "OIL",
        "kind": "DOLLAR_UP",
        "predicted_sign": -1,
        "side": -1,
    },
}


def canonical_search_space_hash():
    return canonical_hash(CANONICAL_PAYLOAD)


def build_search_space():
    digest = canonical_search_space_hash()
    if digest != LOCKED_HASH:
        raise RuntimeError("CONTRACT_MISMATCH")
    hyps = []
    for hid in ALLOWED_HYPOTHESIS_IDS:
        hyps.append(dict(HYPOTHESIS_SPECS[hid]))
    space = dict(CANONICAL_PAYLOAD)
    space["search_space_hash"] = digest
    space["hypotheses"] = hyps
    space["FINAL_OOS_ACCESS"] = "DENIED"
    space["close_fill"] = "FORBIDDEN"
    space["note"] = "Worker executes listed IDs only. Not HYP-0001. Not V0.6."
    return space


def hypothesis_map(space):
    return dict((row["hypothesis_id"], row) for row in (space.get("hypotheses") or []))
