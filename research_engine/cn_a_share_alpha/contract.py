"""Locked V13 contract. Frozen before any ranking result."""
from __future__ import print_function

from research_engine.cn_a_share_alpha import (
    DATASET_HASH,
    DATASET_ID,
    DENIED_END,
    DENIED_START,
    EXCLUDE_ST,
    FDR_Q,
    FINAL_OOS_ACCESS,
    HOLD_DAYS,
    LOOKBACKS,
    MAX_HYPOTHESES,
    MIN_CROSS_SECTION,
    MIN_HISTORY_PAD,
    QUANTILE,
    RESEARCH_END,
    RESEARCH_START,
    SEED,
    V13_ID,
    VALID_END,
    VALID_START,
)
from research_engine.cn_a_share_alpha.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash


HYPOTHESES = (
    {"id": "H01_MOM_20", "family": "CROSS_SECTIONAL_MOMENTUM", "lookback": 20, "sign": "HIGH_PAST_RETURN"},
    {"id": "H02_MOM_60", "family": "CROSS_SECTIONAL_MOMENTUM", "lookback": 60, "sign": "HIGH_PAST_RETURN"},
    {"id": "H03_MOM_120", "family": "CROSS_SECTIONAL_MOMENTUM", "lookback": 120, "sign": "HIGH_PAST_RETURN"},
    {"id": "H04_REV_20", "family": "CROSS_SECTIONAL_REVERSAL", "lookback": 20, "sign": "LOW_PAST_RETURN"},
    {"id": "H05_REV_60", "family": "CROSS_SECTIONAL_REVERSAL", "lookback": 60, "sign": "LOW_PAST_RETURN"},
    {"id": "H06_REV_120", "family": "CROSS_SECTIONAL_REVERSAL", "lookback": 120, "sign": "LOW_PAST_RETURN"},
    {"id": "H07_ACT_20", "family": "CROSS_SECTIONAL_ACTIVITY", "lookback": 20, "sign": "LOW_TURNOVER"},
    {"id": "H08_ACT_60", "family": "CROSS_SECTIONAL_ACTIVITY", "lookback": 60, "sign": "LOW_TURNOVER"},
    {"id": "H09_ACT_120", "family": "CROSS_SECTIONAL_ACTIVITY", "lookback": 120, "sign": "LOW_TURNOVER"},
    {"id": "H10_VOL_20", "family": "CROSS_SECTIONAL_VOLATILITY", "lookback": 20, "sign": "LOW_REALIZED_VOL"},
    {"id": "H11_VOL_60", "family": "CROSS_SECTIONAL_VOLATILITY", "lookback": 60, "sign": "LOW_REALIZED_VOL"},
    {"id": "H12_VOL_120", "family": "CROSS_SECTIONAL_VOLATILITY", "lookback": 120, "sign": "LOW_REALIZED_VOL"},
)


def build_contract():
    if len(HYPOTHESES) > MAX_HYPOTHESES:
        raise RuntimeError("TOO_MANY_HYPOTHESES")
    payload = {
        "id": V13_ID,
        "dataset_id": DATASET_ID,
        "dataset_hash": DATASET_HASH,
        "live_api": False,
        "new_purchase": False,
        "financial": "BLOCKED",
        "industry": "BLOCKED",
        "event": "BLOCKED",
        "signal_price": "RAW_CLOSE_T",
        "execution_price": "RAW_OPEN_T1",
        "return_representation": "RAW_CLOSE_TO_CLOSE",
        "return_limitation": "Full qfq panel was not frozen. Ranking uses raw close returns. CA days can jump.",
        "lookbacks": list(LOOKBACKS),
        "hold_days": HOLD_DAYS,
        "quantile": QUANTILE,
        "portfolio": "QUINTILE_TOP_BOTTOM",
        "rebalance": "NON_OVERLAPPING_EVERY_HOLD",
        "stats_formation": "DAILY_OVERLAPPING_H_DAY",
        "long_only": "CAPITAL_DEFAULT",
        "long_short": "RESEARCH_BOOK_NO_LOCATE",
        "t_plus_1": True,
        "exclude_st": EXCLUDE_ST,
        "min_history": "lookback + %s" % MIN_HISTORY_PAD,
        "min_cross_section": MIN_CROSS_SECTION,
        "unexecutable": ["LIMIT_LOCK", "SUSPENDED", "DELISTED", "ZERO_VOLUME", "MISSING_OPEN"],
        "no_forward_fill": True,
        "research": [RESEARCH_START, RESEARCH_END],
        "validation": [VALID_START, VALID_END],
        "denied_window": [DENIED_START, DENIED_END],
        "final_oos": FINAL_OOS_ACCESS,
        "split": "70/15/15_TIME",
        "fdr_q": FDR_Q,
        "seed": SEED,
        "bootstrap": {"iid": 1000, "block": 1000, "block_len": HOLD_DAYS, "seed": SEED},
        "permutation": {"n": 100, "seed": SEED},
        "cost_model": {
            "id": "A_SHARE_TRANSACTION_COST_MODEL_V1",
            "commission": COMMISSION,
            "transfer": TRANSFER,
            "slippage": SLIPPAGE,
            "stamp_before_20230828": STAMP_OLD,
            "stamp_from_20230828": STAMP_NEW,
            "stamp_side": "SELL_ONLY",
            "not": "MT5_5BP_10BP",
        },
        "benchmarks": ["B0_EW_MARKET", "B1_RANDOM_QUINTILE", "B2_NAIVE_1D_RETURN"],
        "regime": "EW_MARKET_60D_SIGN_AND_20PCT_DRAWDOWN",
        "sector_neutral": False,
        "market_neutral": False,
        "factor_combination": False,
        "ml": False,
        "hypotheses": [dict(h) for h in HYPOTHESES],
        "level1": [
            "research_cost_adj_lo_excess_vs_b0 > 0",
            "validation_cost_adj_lo_excess_vs_b0 > 0",
            "BH_FDR_q_0.05",
            ">=2 evidence (excess and rank_ic) on research AND validation",
        ],
        "do_not_flip_sign": True,
    }
    payload["contract_hash"] = canonical_hash(payload)
    return payload
