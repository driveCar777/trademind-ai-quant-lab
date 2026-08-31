"""Frozen canonical strategy spec. Changing any locked field is NEW_EXPERIMENT."""
from __future__ import print_function

from research_engine.cn_a_share_strategy_v14 import (
    CAGR_TARGET,
    CLUSTER,
    DATASET_HASH,
    DATASET_ID,
    DENIED,
    EXCLUDE_ST,
    FINAL_OOS_ACCESS,
    HOLD_DAYS,
    INITIAL_CAPITAL,
    LEVERAGE,
    LONG_ONLY,
    MIN_CROSS_SECTION,
    MIN_HISTORY_PAD,
    NEW_PURCHASE,
    PARENT_CONTRACT_HASH,
    QUANTILE,
    RESEARCH,
    SEED,
    STRATEGIES,
    V14_ID,
    VALIDATION,
)
from research_engine.cn_a_share_strategy_v14.cost import cost_model_record
from research_protocol.hashing import canonical_hash


def build_spec():
    payload = {
        "id": V14_ID,
        "cluster": CLUSTER,
        "parent_contract_hash": PARENT_CONTRACT_HASH,
        "dataset_id": DATASET_ID,
        "dataset_hash": DATASET_HASH,
        "strategies": [dict(s) for s in STRATEGIES],
        "canonical_per_candidate": 1,
        "lookbacks_locked": [60, 120],
        "hold_days": HOLD_DAYS,
        "quantile": QUANTILE,
        "weight": "EQUAL_1_OVER_N_SELECTED",
        "unfilled": "WEIGHT_STAYS_CASH",
        "cash_buffer": "NONE_EXCEPT_UNFILLED",
        "leverage": LEVERAGE,
        "long_only": LONG_ONLY,
        "short": False,
        "signal": "RAW_CLOSE_T",
        "execution": "RAW_OPEN_T1",
        "rebalance": "NON_OVERLAPPING_EVERY_HOLD",
        "portfolio_formation": "LOW_REALIZED_VOL_TOP_QUANTILE",
        "min_history": "lookback + %s" % MIN_HISTORY_PAD,
        "min_cross_section": MIN_CROSS_SECTION,
        "exclude_st": EXCLUDE_ST,
        "unexecutable": ["LIMIT_LOCK", "SUSPENDED", "DELISTED", "ZERO_VOLUME", "MISSING_OPEN"],
        "delist_during_hold": "NO_FILL_IF_EXIT_UNEXECUTABLE",
        "delist_contract_gap": (
            "Contract has no mid-hold delist price. Canonical never invents one. "
            "A name is UNFILLED if entry or exit is unexecutable."
        ),
        "return_representation": "RAW_OPEN_TO_OPEN",
        "ranking_representation": "RAW_CLOSE_TO_CLOSE",
        "dividend": "DIVIDEND_EXCLUSION",
        "corporate_action": "RAW_CLOSE_CANONICAL. qfq is diagnostic only and not available as a frozen panel.",
        "initial_capital": INITIAL_CAPITAL,
        "initial_capital_note": "Diagnostic. Not a recommendation to invest 1e6 CNY.",
        "research": list(RESEARCH),
        "validation": list(VALIDATION),
        "denied": list(DENIED),
        "final_oos": FINAL_OOS_ACCESS,
        "new_purchase": NEW_PURCHASE,
        "seed": SEED,
        "cost": cost_model_record(),
        "cagr_target_not_a_gate": CAGR_TARGET,
        "level2_gate": [
            "candidate_survived",
            "executable",
            "cost_model_complete",
            "pit_clean",
            "no_hidden_optimization",
            "economics_disclosed",
            "stress_available",
        ],
        "statistic_to_strategy": (
            "Candidate Level 1 used DAILY_OVERLAPPING_H_DAY mean_net_h. "
            "Canonical strategy uses NON_OVERLAPPING_EVERY_HOLD capital."
        ),
        "no_h11_h12_blend": True,
        "no_vol_targeting": True,
        "no_drawdown_control": True,
    }
    payload["spec_hash"] = canonical_hash(payload)
    return payload
