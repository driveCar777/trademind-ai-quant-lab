"""Write-once V19 contract."""
from __future__ import print_function

from research_engine.cn_a_share_indmacro_v19 import (
    CAGR_TARGET,
    DENIED,
    FDR_Q,
    FINAL_OOS_ACCESS,
    HOLD_DAYS,
    KEEP_H11_H12,
    MAX_HYPOTHESES,
    NEW_PURCHASE,
    PRICE_DATASET_HASH,
    PRICE_DATASET_ID,
    QUANTILE,
    REOPEN_H11_H12,
    REOPEN_V16,
    REOPEN_V17,
    REOPEN_V18,
    RESEARCH,
    SAME_CLUSTER_CORR,
    SEED,
    V19_ID,
    VALIDATION,
)
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash


HYPOTHESES = (
    {"id": "IM1_USD_IND_DEF_60", "family": "INDUSTRY_USD_DEFENSIVE", "macro": "USD_FROM_EURUSD", "lookback": 60, "signal": "NEG_BETA_TIMES_SHOCK", "mechanism": "After USD up, long members of low industry-USD-beta groups.", "not": "V16_IND_RS_OR_V17_STOCK_BETA"},
    {"id": "IM2_USD_IND_DEF_120", "family": "INDUSTRY_USD_DEFENSIVE", "macro": "USD_FROM_EURUSD", "lookback": 120, "signal": "NEG_BETA_TIMES_SHOCK", "mechanism": "Same industry USD defensive, 120-day industry beta.", "not": "V16_IND_RS_OR_V17_STOCK_BETA"},
    {"id": "IM3_US_IND_CONT_60", "family": "INDUSTRY_US_CONTINUATION", "macro": "US500", "lookback": 60, "signal": "BETA_TIMES_SHOCK", "mechanism": "After US500 up, long members of high industry-US500-beta groups.", "not": "V16_IND_RS_OR_V17_STOCK_BETA"},
    {"id": "IM4_US_IND_CONT_120", "family": "INDUSTRY_US_CONTINUATION", "macro": "US500", "lookback": 120, "signal": "BETA_TIMES_SHOCK", "mechanism": "Same industry US500 continuation, 120-day industry beta.", "not": "V16_IND_RS_OR_V17_STOCK_BETA"},
    {"id": "IM5_GVZ_IND_DEF_60", "family": "INDUSTRY_GVZ_DEFENSIVE", "macro": "GVZ", "lookback": 60, "signal": "NEG_BETA_TIMES_SHOCK", "mechanism": "After GVZ up, long members of low industry-GVZ-beta groups.", "not": "V16_IND_RS_OR_V17_STOCK_BETA"},
    {"id": "IM6_GVZ_IND_DEF_120", "family": "INDUSTRY_GVZ_DEFENSIVE", "macro": "GVZ", "lookback": 120, "signal": "NEG_BETA_TIMES_SHOCK", "mechanism": "Same industry GVZ defensive, 120-day industry beta.", "not": "V16_IND_RS_OR_V17_STOCK_BETA"},
)


def build_contract():
    if len(HYPOTHESES) != MAX_HYPOTHESES:
        raise RuntimeError("V19_LOCKS_EXACTLY_SIX")
    payload = {
        "id": V19_ID,
        "dataset_id": PRICE_DATASET_ID,
        "dataset_hash": PRICE_DATASET_HASH,
        "industry_pit": "tm-ashare-INDUSTRY-PIT-20260831-000001",
        "live_api": False,
        "new_purchase": NEW_PURCHASE,
        "reopen_h11_h12": REOPEN_H11_H12,
        "keep_h11_h12": KEEP_H11_H12,
        "reopen_v16": REOPEN_V16,
        "reopen_v17": REOPEN_V17,
        "reopen_v18": REOPEN_V18,
        "not": ["V16_INDUSTRY_RELATIVE_STRENGTH", "V17_STOCK_LEVEL_MACRO_BETA", "H11_H12"],
        "pit_rule": "industry_effective_date_le_signal_and_macro_date_lt_signal",
        "signal_price": "RAW_CLOSE_T",
        "execution_price": "RAW_OPEN_T1",
        "hold_days": HOLD_DAYS,
        "quantile": QUANTILE,
        "portfolio": "QUINTILE_TOP_20",
        "long_only": True,
        "rebalance": "NON_OVERLAPPING_EVERY_HOLD",
        "predictive_metric_name": "MEAN_FORWARD_RETURN",
        "predictive_is_not_cagr": True,
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
