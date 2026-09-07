"""Write-once V18 contract. Frozen before ranking."""
from __future__ import print_function

from research_engine.cn_a_share_altinfo_v18 import (
    CAGR_TARGET,
    DENIED,
    FDR_Q,
    FINAL_OOS_ACCESS,
    HOLD_DAYS,
    KEEP_H11_H12,
    MAX_HYPOTHESES,
    MIN_CROSS_SECTION,
    NEW_H13,
    NEW_PURCHASE,
    PRICE_DATASET_HASH,
    PRICE_DATASET_ID,
    PRICE_ONLY_REOPEN,
    QUANTILE,
    REOPEN_H11_H12,
    REOPEN_V16,
    REOPEN_V17,
    RESEARCH,
    SAME_CLUSTER_CORR,
    SEED,
    V18_ID,
    VALIDATION,
)
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash


HYPOTHESES = (
    {
        "id": "A1_SEASONED_AGE",
        "family": "LISTING_AGE",
        "mechanism": "IPO long-run underperformance. Long the most seasoned names. score = calendar age in days.",
        "signal": "AGE_DAYS",
        "state": None,
        "not": "YOUNG_IPO_MOMENTUM_OR_PRICE_ONLY",
    },
    {
        "id": "A2_RELATIVE_AGE",
        "family": "LISTING_AGE",
        "mechanism": "Long names older than that day's eligible median age. Relative seasoning, not absolute.",
        "signal": "AGE_MINUS_CS_MEDIAN",
        "state": None,
        "not": "ABSOLUTE_AGE_CLONE_OR_SIZE",
    },
    {
        "id": "A3_CLEAN_STREAK",
        "family": "ST_HISTORY",
        "mechanism": "Long names with the longest consecutive non-ST streak. Special-treatment risk fading.",
        "signal": "CLEAN_STREAK",
        "state": None,
        "not": "H11_VOL_OR_CURRENT_ST_FILTER",
    },
    {
        "id": "A4_RECENT_RESUME",
        "family": "SUSPEND_RESUME",
        "mechanism": "After suspension lifts, delayed catching-up. Long shortest consecutive tradable streak (recent resume).",
        "signal": "NEG_UP_STREAK",
        "state": None,
        "not": "PRICE_REVERSAL_OR_LIMIT_LOCK",
    },
    {
        "id": "A5_MONTH_END_SEASONED",
        "family": "CALENDAR_WINDOW",
        "mechanism": "Month-end window dressing into seasoned names. Age score only on last 2 CN trading days of the month.",
        "signal": "AGE_DAYS",
        "state": "MONTH_END_2",
        "not": "IT_GOLD_MONTH_END_OR_PRICE_REVERSAL",
    },
    {
        "id": "A6_QUARTER_END_SEASONED",
        "family": "CALENDAR_WINDOW",
        "mechanism": "Quarter-end reporting window dressing into seasoned names. Age score only on last 5 CN trading days of the quarter.",
        "signal": "AGE_DAYS",
        "state": "QUARTER_END_5",
        "not": "IT_GOLD_MONTH_END_OR_PRICE_REVERSAL",
    },
)


def build_contract():
    if len(HYPOTHESES) != MAX_HYPOTHESES:
        raise RuntimeError("V18_LOCKS_EXACTLY_SIX")
    payload = {
        "id": V18_ID,
        "dataset_id": PRICE_DATASET_ID,
        "dataset_hash": PRICE_DATASET_HASH,
        "alt_sources": ["tm-cn-a-BASIC-20260830-000001", "pack.isST", "pack.tradestatus", "tm-cn-a-CALENDAR-20260830-000001"],
        "live_api": False,
        "new_purchase": NEW_PURCHASE,
        "reopen_h11_h12": REOPEN_H11_H12,
        "keep_h11_h12": KEEP_H11_H12,
        "price_only_reopen": PRICE_ONLY_REOPEN,
        "reopen_v16": REOPEN_V16,
        "reopen_v17": REOPEN_V17,
        "new_h13": NEW_H13,
        "not": ["PRICE_ONLY_FARM", "V17_MACRO_RETUNE", "EVENT_ANNOUNCEMENT", "NEWS_TEXT"],
        "pit_rule": "listing_date_and_flags_through_signal_date_only",
        "signal_price": "RAW_CLOSE_T",
        "execution_price": "RAW_OPEN_T1",
        "hold_days": HOLD_DAYS,
        "quantile": QUANTILE,
        "portfolio": "QUINTILE_TOP_20",
        "long_only": True,
        "rebalance": "NON_OVERLAPPING_EVERY_HOLD",
        "predictive_metric_name": "MEAN_FORWARD_RETURN",
        "predictive_is_not_cagr": True,
        "cagr_only_from": "CANONICAL_CAPITAL_ACCOUNT",
        "min_cross_section": MIN_CROSS_SECTION,
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
