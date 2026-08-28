"""Locked surprise space. Worker cannot change z_cut or lookback."""
from __future__ import print_function

from research_engine.holdout import final_oos_access
from research_engine.microstructure_surprise import (
    ALLOWED_HYPOTHESIS_IDS,
    FAMILY_ID,
    HOLD_BARS,
    LOOKBACK,
    MS_ID,
    MS_SEED,
    PARENTS,
    Z_CUT,
)
from research_protocol.hashing import canonical_hash


CANONICAL_PAYLOAD = {
    "close_fill": "FORBIDDEN",
    "cost": {
        "commission_bp_per_side": 5.0,
        "slippage_bp_per_side": 10.0,
        "spread": "BROKER_POINTS_RULE",
    },
    "discovery_id": MS_ID,
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
    "lookback_same_hour": LOOKBACK,
    "not_fd_tickvol_level": True,
    "not_weekday": True,
    "parent_datasets": list(PARENTS),
    "risk": {"leverage_cap": 1.0, "risk_frac": 0.005, "stop_atr_mult": 1.5},
    "seed": MS_SEED,
    "stats": {
        "block_length": 5,
        "bootstrap": 2000,
        "fdr_q": 0.05,
        "m": 3,
        "permutation": 2000,
    },
    "surprise": {
        "baseline": "SAME_UTC_HOUR_TRAILING",
        "kind": "TICK_VOLUME_Z",
        "quiet_price_mult": 0.5,
        "z_cut": Z_CUT,
    },
    "timeframe": "H1",
    "windows": {
        "FINAL_OOS_ACCESS": "DENIED",
        "split": "70/15/15_on_each_target_own_h1_dates",
    },
}

HYPOTHESIS_SPECS = {
    "HYP-MS-0001": {
        "hypothesis_id": "HYP-MS-0001",
        "kind": "VOL_SURPRISE",
        "target_asset": "GOLD",
        "event": "TICKVOL_SAME_HOUR_SURPRISE",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Unexpected same-hour activity into gold, not a volume level.",
    },
    "HYP-MS-0002": {
        "hypothesis_id": "HYP-MS-0002",
        "kind": "VOL_SURPRISE",
        "target_asset": "OIL",
        "event": "TICKVOL_SAME_HOUR_SURPRISE",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Unexpected same-hour activity into oil, not a volume level.",
    },
    "HYP-MS-0003": {
        "hypothesis_id": "HYP-MS-0003",
        "kind": "VOL_DIVERGENCE",
        "target_asset": "GOLD",
        "event": "TICKVOL_SURPRISE_QUIET_PRICE",
        "predicted_sign": 1,
        "hold_bars": HOLD_BARS,
        "mechanism": "Activity surprise with quiet price; inventory then catch-up.",
    },
}


def deny_oos():
    try:
        final_oos_access(reason="microstructure_surprise_v1")
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
    from research_engine.microstructure_surprise import LOCKED_HASH

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
