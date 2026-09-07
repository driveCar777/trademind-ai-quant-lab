"""Write-once V23 contract. Signs fixed from literature before any run: leveraged retail inflow predicts lower returns."""
from __future__ import print_function

from research_engine.cn_a_share_margin_v23 import (
    DENIED, FDR_Q, HOLD_DAYS, MARGIN_DATASET_ID, MAX_HYPOTHESES, PIT_LAG_SESSIONS, PRICE_DATASET_HASH,
    PRICE_DATASET_ID, QUANTILE, RESEARCH, SAME_CLUSTER_CORR, SEED, V23_ID, VALIDATION,
)
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash

HYPOTHESES = (
    {
        "id": "M1_LOW_NET_MARGIN_INFLOW_20",
        "family": "MARGIN_FLOW",
        "mechanism": "Leveraged retail net margin buying over the last 20 sessions, scaled by float market cap, predicts lower forward returns (crowded, forced-deleveraging risk). Long the quintile with the LOWEST inflow. score = -sum(RZJME,20)/SZ.",
        "signal": "NEG_NET_INFLOW_20_OVER_CAP",
        "state": None,
        "not": "PRICE_REVERSAL_OR_TURNOVER_CLONE",
    },
    {
        "id": "M2_LOW_MARGIN_BALANCE_RATIO",
        "family": "MARGIN_LEVEL",
        "mechanism": "Margin balance as a fraction of float market cap = leverage overhang. Long the quintile with the LOWEST ratio. score = -RZYE/SZ.",
        "signal": "NEG_BALANCE_OVER_CAP",
        "state": None,
        "not": "SIZE_CLONE_OR_LOW_VOL",
    },
    {
        "id": "M3_MARGIN_DELEVERAGED_60",
        "family": "MARGIN_FLOW",
        "mechanism": "Names whose margin balance fell most over 60 sessions have already shed leveraged holders. Long the quintile with the LARGEST 60-session balance decline. score = -(RZYE_t / RZYE_{t-60} - 1).",
        "signal": "NEG_BALANCE_CHG_60",
        "state": None,
        "not": "PRICE_MOMENTUM_CLONE",
    },
)


def build_contract():
    if len(HYPOTHESES) != MAX_HYPOTHESES:
        raise RuntimeError("V23_LOCKS_EXACTLY_THREE")
    payload = {
        "id": V23_ID,
        "dataset_id": PRICE_DATASET_ID,
        "dataset_hash": PRICE_DATASET_HASH,
        "margin_dataset_id": MARGIN_DATASET_ID,
        "margin_source": "Eastmoney datacenter RPTA_WEB_RZRQ_GGMX (mirror of SSE/SZSE daily margin detail); official exchange pages probed reachable for cross-check",
        "margin_fields_used": ["RZYE", "RZJME", "SZ"],
        "live_api": False,
        "new_purchase": False,
        "cost_usd": 0.0,
        "reopen_h11_h12": False,
        "keep_h11_h12": True,
        "reopen_v13_v21": False,
        "not": ["PRICE_ONLY_FARM", "ANNOUNCEMENT_WINDOW", "RATIO", "MEMBERSHIP", "SIGN_FLIP"],
        "pit_rule": "margin detail for session D is exchange-published D+1 pre-open; score at close of t uses rows with DATE <= t-%d" % PIT_LAG_SESSIONS,
        "pit_lag_sessions": PIT_LAG_SESSIONS,
        "universe": "eligible names in the frozen panel that have a margin row on t-1 (marginable set)",
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
        "min_cross_section": 100,
        "research": list(RESEARCH),
        "validation": list(VALIDATION),
        "denied_window": list(DENIED),
        "denied_downloaded": False,
        "final_oos": "DENIED",
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
        "cagr_target_not_a_gate": 0.10,
        "do_not_flip_sign": True,
        "hypotheses": [dict(h) for h in HYPOTHESES],
    }
    payload["contract_hash"] = canonical_hash(payload)
    return payload
