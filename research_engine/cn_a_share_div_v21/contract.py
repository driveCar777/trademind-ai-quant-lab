"""Write-once V21 contract. Frozen before ranking."""
from __future__ import print_function

from research_engine.cn_a_share_div_v21 import (
    CAGR_TARGET,
    DENIED,
    EVENT_WINDOW,
    FDR_Q,
    FINAL_OOS_ACCESS,
    HOLD_DAYS,
    KEEP_H11_H12,
    MAX_HYPOTHESES,
    MIN_EVENT_SET,
    NEW_PURCHASE,
    PRICE_DATASET_HASH,
    PRICE_DATASET_ID,
    REOPEN_H11_H12,
    REOPEN_V16,
    REOPEN_V20,
    RESEARCH,
    SAME_CLUSTER_CORR,
    SEED,
    V21_ID,
    VALIDATION,
)
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash


HYPOTHESES = (
    {
        "id": "D1_CASH_ANN_20",
        "family": "DIVIDEND_CASH_EVENT",
        "signal": "CASH_ANN_20",
        "min_n": MIN_EVENT_SET,
        "mechanism": "Long names with a cash-dividend plan announced in the last 20 sessions. Event window, not yield level.",
        "not": "HIGH_YIELD_QUINTILE_OR_V16_ROE",
    },
    {
        "id": "D2_STOCK_ANN_20",
        "family": "DIVIDEND_STOCK_EVENT",
        "signal": "STOCK_ANN_20",
        "min_n": MIN_EVENT_SET,
        "mechanism": "Long names with a stock/reserve dividend plan announced in the last 20 sessions. Bonus-share event, not cash yield.",
        "not": "CASH_YIELD_OR_PRICE_MOMENTUM",
    },
)


def build_contract():
    if len(HYPOTHESES) != MAX_HYPOTHESES:
        raise RuntimeError("V21_LOCKS_EXACTLY_TWO")
    payload = {
        "id": V21_ID,
        "dataset_id": PRICE_DATASET_ID,
        "dataset_hash": PRICE_DATASET_HASH,
        "dividend_pit": "tm-ashare-DIVIDEND-PIT-20260902-000001",
        "live_api": False,
        "new_purchase": NEW_PURCHASE,
        "reopen_h11_h12": REOPEN_H11_H12,
        "keep_h11_h12": KEEP_H11_H12,
        "reopen_v16": REOPEN_V16,
        "reopen_v20": REOPEN_V20,
        "not": ["DIVIDEND_YIELD_QUINTILE", "V16_ANNUAL_RATIO", "INDEX_MEMBERSHIP", "OPERATE_DATE_AS_KNOWLEDGE"],
        "pit_rule": "announce_date_lt_signal",
        "signal_price": "RAW_CLOSE_T",
        "execution_price": "RAW_OPEN_T1",
        "hold_days": HOLD_DAYS,
        "event_window_sessions": EVENT_WINDOW,
        "portfolio": "MEMBERSHIP_SET",
        "quantile": None,
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
