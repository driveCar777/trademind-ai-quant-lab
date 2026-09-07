"""Write-once V20 contract. Frozen before ranking."""
from __future__ import print_function

from research_engine.cn_a_share_index_v20 import (
    ADD_LOOKBACK,
    CAGR_TARGET,
    DENIED,
    FDR_Q,
    FINAL_OOS_ACCESS,
    HOLD_DAYS,
    KEEP_H11_H12,
    MAX_HYPOTHESES,
    MIN_EVENT_SET,
    MIN_SET,
    NEW_PURCHASE,
    PRICE_DATASET_HASH,
    PRICE_DATASET_ID,
    REOPEN_H11_H12,
    REOPEN_V16,
    REOPEN_V17,
    REOPEN_V18,
    REOPEN_V19,
    RESEARCH,
    SAME_CLUSTER_CORR,
    SEED,
    V20_ID,
    VALIDATION,
)
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash


HYPOTHESES = (
    {
        "id": "X1_HS300_SET",
        "family": "INDEX_MEMBERSHIP",
        "index": "HS300",
        "signal": "HS300_MEMBER",
        "min_n": MIN_SET,
        "mechanism": "Long eligible current CSI 300 members. Institutional ownership / membership premium.",
        "not": "H11_LOW_VOL_OR_PRICE_SIZE_SORT",
    },
    {
        "id": "X2_ZZ500_SET",
        "family": "INDEX_MEMBERSHIP",
        "index": "ZZ500",
        "signal": "ZZ500_MEMBER",
        "min_n": MIN_SET,
        "mechanism": "Long eligible current CSI 500 members. Mid-cap index membership, not mega-cap.",
        "not": "HS300_CLONE_OR_H11",
    },
    {
        "id": "X3_HS300_IN_252",
        "family": "INDEX_RECONSTITUTION",
        "index": "HS300",
        "signal": "HS300_ADD_252",
        "min_n": MIN_EVENT_SET,
        "mechanism": "Long names that entered CSI 300 in the last 252 pack sessions and are still members. Reconstitution inflow.",
        "not": "STATIC_MEMBERSHIP_OR_MOMENTUM",
    },
    {
        "id": "X4_HS300_OUT_252",
        "family": "INDEX_RECONSTITUTION",
        "index": "HS300",
        "signal": "HS300_DROP_252",
        "min_n": MIN_EVENT_SET,
        "mechanism": "Long names that left CSI 300 in the last 252 pack sessions and are still listed. Post-deletion leftover after forced selling.",
        "not": "SHORT_DELETES_OR_H11",
    },
)


def build_contract():
    if len(HYPOTHESES) != MAX_HYPOTHESES:
        raise RuntimeError("V20_LOCKS_EXACTLY_FOUR")
    payload = {
        "id": V20_ID,
        "dataset_id": PRICE_DATASET_ID,
        "dataset_hash": PRICE_DATASET_HASH,
        "index_pit": "tm-ashare-INDEX-PIT-20260902-000001",
        "live_api": False,
        "new_purchase": NEW_PURCHASE,
        "reopen_h11_h12": REOPEN_H11_H12,
        "keep_h11_h12": KEEP_H11_H12,
        "reopen_v16": REOPEN_V16,
        "reopen_v17": REOPEN_V17,
        "reopen_v18": REOPEN_V18,
        "reopen_v19": REOPEN_V19,
        "not": ["PRICE_ONLY_FARM", "V16_ANNUAL_RATIO", "V17_MACRO_BETA", "QUINTILE_OF_BINARY"],
        "pit_rule": "index_effective_date_le_signal",
        "signal_price": "RAW_CLOSE_T",
        "execution_price": "RAW_OPEN_T1",
        "hold_days": HOLD_DAYS,
        "portfolio": "MEMBERSHIP_SET",
        "quantile": None,
        "add_lookback_sessions": ADD_LOOKBACK,
        "min_set": MIN_SET,
        "min_event_set": MIN_EVENT_SET,
        "long_only": True,
        "rebalance": "NON_OVERLAPPING_EVERY_HOLD",
        "predictive_metric_name": "MEAN_FORWARD_RETURN",
        "predictive_is_not_cagr": True,
        "cagr_only_from": "CANONICAL_CAPITAL_ACCOUNT",
        "research": list(RESEARCH),
        "validation": list(VALIDATION),
        "denied_window": list(DENIED),
        "final_oos": FINAL_OOS_ACCESS,
        "fdr_q": FDR_Q,
        "seed": SEED,
        "cost_model": {
            "id": "A_SHARE_STRATEGY_COST_MODEL_V1",
            "commission": COMMISSION,
            "transfer": TRANSFER,
            "slippage": SLIPPAGE,
            "stamp_before_20230828": STAMP_OLD,
            "stamp_from_20230828": STAMP_NEW,
            "optimize": False,
        },
        "same_cluster_corr": SAME_CLUSTER_CORR,
        "cagr_target_not_a_gate": CAGR_TARGET,
        "do_not_flip_sign": True,
        "hypotheses": [dict(h) for h in HYPOTHESES],
    }
    payload["contract_hash"] = canonical_hash(payload)
    return payload
