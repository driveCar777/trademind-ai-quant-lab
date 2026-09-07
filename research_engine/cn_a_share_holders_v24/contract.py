"""Write-once V24 contract. Sign fixed a priori: ownership concentration (falling holder count) -> long."""
from __future__ import print_function

from research_engine.cn_a_share_holders_v24 import (
    DENIED, FDR_Q, HOLD_DAYS, HOLDERS_DATASET_ID, MAX_HYPOTHESES, NOTICE_CUTOFF, PRICE_DATASET_HASH,
    PRICE_DATASET_ID, QUANTILE, RESEARCH, SAME_CLUSTER_CORR, SEED, V24_ID, VALIDATION,
)
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash

HYPOTHESES = (
    {
        "id": "HC1_CONCENTRATION_QOQ",
        "family": "HOLDER_CONCENTRATION",
        "mechanism": "Falling shareholder count between consecutive reports = chips concentrating into fewer hands (informed accumulation, retail exit). Long the quintile with the largest QoQ decline. score = -(HOLDER_NUM / PRE_HOLDER_NUM - 1) from the latest announced report.",
        "signal": "NEG_QOQ_CHANGE",
        "state": None,
        "not": "PRICE_MOMENTUM_OR_TURNOVER_CLONE",
    },
    {
        "id": "HC2_CONCENTRATION_2Q",
        "family": "HOLDER_CONCENTRATION",
        "mechanism": "Persistent concentration over two reports. Long the quintile with the largest decline vs the report two periods back. score = -(HOLDER_NUM_t / HOLDER_NUM_{t-2} - 1).",
        "signal": "NEG_2Q_CHANGE",
        "state": None,
        "not": "HC1_CLONE_BY_CONSTRUCTION_IS_ACCEPTED_AS_HORIZON_VARIANT",
    },
    {
        "id": "HC3_LOW_HOLDERS_PER_SHARE",
        "family": "HOLDER_LEVEL",
        "mechanism": "Fewer holders per A-share outstanding = concentrated ownership level. Long the quintile with the lowest holders/share. score = -(HOLDER_NUM / TOTAL_A_SHARES).",
        "signal": "NEG_HOLDERS_PER_SHARE",
        "state": None,
        "not": "PURE_SIZE_CLONE",
    },
)


def build_contract():
    if len(HYPOTHESES) != MAX_HYPOTHESES:
        raise RuntimeError("V24_LOCKS_EXACTLY_THREE")
    payload = {
        "id": V24_ID,
        "dataset_id": PRICE_DATASET_ID,
        "dataset_hash": PRICE_DATASET_HASH,
        "holders_dataset_id": HOLDERS_DATASET_ID,
        "holders_source": "Eastmoney datacenter RPT_HOLDERNUM_DET per stock; fields HOLDER_NUM, PRE_HOLDER_NUM, TOTAL_A_SHARES, END_DATE, HOLD_NOTICE_DATE",
        "live_api": False,
        "new_purchase": False,
        "cost_usd": 0.0,
        "reopen_h11_h12": False,
        "keep_h11_h12": True,
        "reopen_v13_v23": False,
        "not": ["PRICE_ONLY_FARM", "ANNOUNCEMENT_WINDOW_LONG", "RATIO", "MEMBERSHIP", "SIGN_FLIP"],
        "pit_rule": "value from report R visible from the first session strictly after HOLD_NOTICE_DATE(R); rows with HOLD_NOTICE_DATE > %s dropped at compile" % NOTICE_CUTOFF,
        "universe": "eligible names in the frozen panel with at least one announced holder-count report",
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
        "final_oos": "DENIED",
        "fdr_q": FDR_Q,
        "seed": SEED,
        "cost_model": {"id": "A_SHARE_STRATEGY_COST_MODEL_V1", "commission": COMMISSION, "transfer": TRANSFER, "slippage": SLIPPAGE,
                       "stamp_before_20230828": STAMP_OLD, "stamp_from_20230828": STAMP_NEW, "optimize": False},
        "same_cluster_corr": SAME_CLUSTER_CORR,
        "cagr_target_not_a_gate": 0.10,
        "do_not_flip_sign": True,
        "hypotheses": [dict(h) for h in HYPOTHESES],
    }
    payload["contract_hash"] = canonical_hash(payload)
    return payload
