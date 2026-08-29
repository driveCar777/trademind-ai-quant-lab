"""Locked GOLD/US500 correlation-regime space. Worker cannot change lookbacks."""
from __future__ import print_function

from research_engine.corr_shock import (
    ALLOWED_HYPOTHESIS_IDS,
    BASKET,
    BREAK_PCTL,
    CORR_LOOKBACK,
    FAMILY_ID,
    HOLD_BARS,
    PARENTS,
    PCT_LOOKBACK,
    SPIKE_PCTL,
    CS_ID,
    CS_SEED,
)
from research_engine.holdout import final_oos_access
from research_protocol.hashing import canonical_hash


CANONICAL_PAYLOAD = {
    "basket": list(BASKET),
    "close_fill": "FORBIDDEN",
    "corr_params": {
        "break_pctl": BREAK_PCTL,
        "corr_lookback": CORR_LOOKBACK,
        "pct_lookback": PCT_LOOKBACK,
        "spike_pctl": SPIKE_PCTL,
    },
    "cost": {
        "commission_bp_per_side": 5.0,
        "slippage_bp_per_side": 10.0,
        "spread": "BROKER_POINTS_RULE",
    },
    "discovery_id": CS_ID,
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
    "not_cross_metal_ratio": True,
    "not_dxy_z": True,
    "not_hold_search": True,
    "not_pctl_search": True,
    "not_v08_fx_return": True,
    "parent_datasets": list(PARENTS),
    "risk": {"leverage_cap": 1.0, "risk_frac": 0.005, "stop_atr_mult": 1.5},
    "seed": CS_SEED,
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
}

HYPOTHESIS_SPECS = {
    "HYP-CS-0001": {
        "hypothesis_id": "HYP-CS-0001",
        "target_asset": "BOOK",
        "event": "CORR_BREAK_CROSS",
        "side_mode": "REV_RISKOFF",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "60d GOLD/US500 corr crosses below its 252d 20th pctile: long GOLD short US500.",
    },
    "HYP-CS-0002": {
        "hypothesis_id": "HYP-CS-0002",
        "target_asset": "BOOK",
        "event": "CORR_BREAK_CROSS",
        "side_mode": "GOLD_LONG",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Same break: long GOLD only. Quality bid without the equity short.",
    },
    "HYP-CS-0003": {
        "hypothesis_id": "HYP-CS-0003",
        "target_asset": "BOOK",
        "event": "CORR_SPIKE_CROSS",
        "side_mode": "REV_RISKON",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Corr crosses above 252d 80th pctile: short GOLD long US500 (risk-on coupling).",
    },
}


def deny_oos():
    try:
        final_oos_access(reason="corr_shock_v1_contract")
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
    from research_engine.corr_shock import LOCKED_HASH

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
