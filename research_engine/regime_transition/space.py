"""Locked V0.9 space. Hash must match the markdown contract. Worker cannot add IDs."""
from __future__ import print_function

from research_engine.regime_transition import (
    ALLOWED_HYPOTHESIS_IDS,
    FAMILY_ID,
    HOLD_BARS,
    LOCKED_HASH,
    PARENTS,
    RT_BLOCK,
    RT_BOOT,
    RT_FDR_M,
    RT_FDR_Q,
    RT_ID,
    RT_PERM,
    RT_SEED,
)
from research_protocol.hashing import canonical_hash


# Exact payload from REGIME_TRANSITION_V0.9_CONTRACT.md section 11.
CANONICAL_PAYLOAD = {
    "adx_period": 14,
    "close_fill": "FORBIDDEN",
    "cost": {
        "commission_bp_per_side": 5.0,
        "slippage_bp_per_side": 10.0,
        "spread": "BROKER_POINTS_RULE",
    },
    "discovery_id": RT_ID,
    "family_id": FAMILY_ID,
    "fill": "NEXT_BAR_OPEN",
    "hold_bars": HOLD_BARS,
    "horizon": "SIGNAL_PLUS_HOLD_ALIGNED_ROWS",
    "hypothesis_count": 3,
    "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
    "parent_datasets": list(PARENTS),
    "risk": {"leverage_cap": 1.0, "risk_frac": 0.005, "stop_atr_mult": 1.5},
    "seed": RT_SEED,
    "sma_fast": 20,
    "sma_slow": 50,
    "state_source": "MARKET_STATE_V0.5",
    "stats": {
        "block_length": RT_BLOCK,
        "bootstrap": RT_BOOT,
        "fdr_q": RT_FDR_Q,
        "m": RT_FDR_M,
        "permutation": RT_PERM,
    },
    "timeframe": "D1",
    "vol_percentiles": [33, 67],
    "windows": {
        "FINAL_OOS_ACCESS": "DENIED",
        "split": "70/15/15_on_target_sorted_d1_dates",
    },
}

HYPOTHESIS_SPECS = {
    "HYP-RT-0001": {
        "hypothesis_id": "HYP-RT-0001",
        "title": "Vol enters HIGH -> next 5D OIL down",
        "feature": "VOL_SHOCK",
        "target": "OIL",
        "target_asset": "OIL",
        "predicted_sign": -1,
        "side": -1,
        "hold_bars": HOLD_BARS,
    },
    "HYP-RT-0002": {
        "hypothesis_id": "HYP-RT-0002",
        "title": "Trend strength ignites UP -> next 5D GOLD up",
        "feature": "ENTER_STRONG_UP",
        "target": "GOLD",
        "target_asset": "GOLD",
        "predicted_sign": 1,
        "side": 1,
        "hold_bars": HOLD_BARS,
    },
    "HYP-RT-0003": {
        "hypothesis_id": "HYP-RT-0003",
        "title": "Trend strength dies -> next 5D GOLD down",
        "feature": "EXIT_STRONG",
        "target": "GOLD",
        "target_asset": "GOLD",
        "predicted_sign": -1,
        "side": -1,
        "hold_bars": HOLD_BARS,
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
    space["note"] = "Worker executes listed IDs only. Delta-state. Not HYP-0001. Not V0.6. Not V0.8."
    return space


def hypothesis_map(space=None):
    if space is None:
        return dict((hid, dict(HYPOTHESIS_SPECS[hid])) for hid in ALLOWED_HYPOTHESIS_IDS)
    return dict((row["hypothesis_id"], row) for row in (space.get("hypotheses") or []))
