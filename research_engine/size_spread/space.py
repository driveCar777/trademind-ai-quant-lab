"""Locked size-spread space. Worker cannot change lookback or invent events."""
from __future__ import print_function

from research_engine.holdout import final_oos_access
from research_engine.size_spread import (
    ALLOWED_HYPOTHESIS_IDS,
    BASKET,
    FAMILY_ID,
    HOLD_BARS,
    LOOKBACK,
    PARENTS,
    SZ_ID,
    SZ_SEED,
)
from research_protocol.hashing import canonical_hash


CANONICAL_PAYLOAD = {
    "basket": list(BASKET),
    "close_fill": "FORBIDDEN",
    "cost": {
        "commission_bp_per_side": 5.0,
        "slippage_bp_per_side": 10.0,
        "spread": "BROKER_POINTS_RULE",
    },
    "discovery_id": SZ_ID,
    "family_id": FAMILY_ID,
    "fill": "NEXT_BAR_OPEN",
    "gates": {
        "insufficient_occupancy": "FAIL_NOT_WIDEN",
        "occupancy_max": 0.40,
        "program_candidate": "FDR_AND_TWO_HYPS_AFTER_COST",
        "research_n_trade_min": 8,
        "validation_n_trade_min": 4,
    },
    "hold_bars": HOLD_BARS,
    "horizon": "SIGNAL_PLUS_HOLD_OWN_DATES",
    "hypothesis_count": 3,
    "hypothesis_ids": list(ALLOWED_HYPOTHESIS_IDS),
    "knowledge_time_rule": "aligned_d1_closes_then_NEXT_BAR_OPEN",
    "not_ag_breadth": True,
    "not_buy_us500_on_lead": True,
    "not_hold_search": True,
    "not_idx_async_single": True,
    "not_pctl_search": True,
    "not_single_asset_momentum": True,
    "not_xs_rev_rank": True,
    "parent_datasets": list(PARENTS),
    "risk": {"leverage_cap": 1.0, "risk_frac": 0.005, "stop_atr_mult": 1.5},
    "seed": SZ_SEED,
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
        "split": "70/15/15_on_aligned_book_dates",
    },
    "size_params": {
        "lookback": LOOKBACK,
        "signal": "US2000_minus_US500_20d_sign_cross",
    },
}

HYPOTHESIS_SPECS = {
    "HYP-SZ-0001": {
        "hypothesis_id": "HYP-SZ-0001",
        "target_asset": "GOLD",
        "event": "SIZE_LAG",
        "side_mode": "GOLD_LONG",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Small-cap 20d return crosses below large-cap: risk-off, long GOLD.",
    },
    "HYP-SZ-0002": {
        "hypothesis_id": "HYP-SZ-0002",
        "target_asset": "GOLD",
        "event": "SIZE_LEAD",
        "side_mode": "GOLD_SHORT",
        "predicted_sign": -1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Small-cap 20d return crosses above large-cap: risk-on, short GOLD.",
    },
    "HYP-SZ-0003": {
        "hypothesis_id": "HYP-SZ-0003",
        "target_asset": "BOOK",
        "event": "SIZE_LAG",
        "side_mode": "SHORT_SMALL_LONG_LARGE",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Same lag: short US2000, long US500. Size book, not buy US500 alone.",
    },
}


def deny_oos():
    try:
        final_oos_access(reason="size_spread_v1_contract")
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
    from research_engine.size_spread import LOCKED_HASH

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
