"""Write-once V16 alpha contract. Formulas locked before ranking. No price-only hyps."""
from __future__ import print_function

from research_engine.cn_a_share_information_v16 import (
    CAGR_TARGET,
    DENIED,
    FDR_Q,
    FINAL_OOS_ACCESS,
    HOLD_DAYS,
    MAX_FIN_HYP,
    MAX_IND_HYP,
    NEW_H13,
    NEW_PURCHASE,
    PRICE_DATASET_HASH,
    PRICE_DATASET_ID,
    QUANTILE,
    REOPEN_H11_H12,
    RESEARCH,
    SEED,
    V16_ID,
    VALIDATION,
)
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash


FIN_HYPOTHESES = (
    {
        "id": "F1_YOY_NP_ANN",
        "family": "EARNINGS_GROWTH",
        "mechanism": "Latest visible annual net_profit vs prior visible annual. Long high YoY.",
        "signal": "YOY_NET_PROFIT_ANNUAL",
        "lookback": "latest_visible_annual",
        "hold_days": HOLD_DAYS,
    },
    {
        "id": "F1_YOY_REV_ANN",
        "family": "EARNINGS_GROWTH",
        "mechanism": "Latest visible annual revenue vs prior visible annual. Long high YoY.",
        "signal": "YOY_REVENUE_ANNUAL",
        "lookback": "latest_visible_annual",
        "hold_days": HOLD_DAYS,
    },
    {
        "id": "F2_ROE_ANN",
        "family": "PROFITABILITY",
        "mechanism": "Latest visible annual ROE. Long high ROE.",
        "signal": "ROE_ANNUAL",
        "lookback": "latest_visible_annual",
        "hold_days": HOLD_DAYS,
    },
    {
        "id": "F2_GPM_ANN",
        "family": "PROFITABILITY",
        "mechanism": "Latest visible annual gross margin. Long high GPM.",
        "signal": "GPM_ANNUAL",
        "lookback": "latest_visible_annual",
        "hold_days": HOLD_DAYS,
    },
    {
        "id": "F3_NPM_ANN",
        "family": "QUALITY",
        "mechanism": "Latest visible annual net profit margin. Long high quality.",
        "signal": "NPM_ANNUAL",
        "lookback": "latest_visible_annual",
        "hold_days": HOLD_DAYS,
    },
    {
        "id": "F4_ROE_DELTA_ANN",
        "family": "FINANCIAL_CHANGE",
        "mechanism": "Change in annual ROE vs prior visible annual. Long improving ROE.",
        "signal": "ROE_DELTA_ANNUAL",
        "lookback": "latest_visible_annual",
        "hold_days": HOLD_DAYS,
    },
)

IND_HYPOTHESES = ()


def build_financial_contract():
    if len(FIN_HYPOTHESES) > MAX_FIN_HYP:
        raise RuntimeError("TOO_MANY_FIN_HYP")
    if len(FIN_HYPOTHESES) != 6:
        raise RuntimeError("V16_LOCKS_SIX_FIN")
    if any("VOL" in h["id"] or "MOM" in h["id"] or "REV_PX" in h["id"] for h in FIN_HYPOTHESES):
        raise RuntimeError("PRICE_ONLY_FORBIDDEN")
    payload = {
        "id": V16_ID + "_FINANCIAL_ALPHA",
        "price_dataset_id": PRICE_DATASET_ID,
        "price_dataset_hash": PRICE_DATASET_HASH,
        "new_purchase": NEW_PURCHASE,
        "reopen_h11_h12": REOPEN_H11_H12,
        "new_h13": NEW_H13,
        "price_only": False,
        "knowledge_time": "announcement_date <= signal_date",
        "report_period_is_not_knowledge_time": True,
        "quantile": QUANTILE,
        "hold_days": HOLD_DAYS,
        "long_only": True,
        "predictive_metric_name": "MEAN_FORWARD_RETURN",
        "predictive_is_not_cagr": True,
        "cagr_only_from": "CANONICAL_CAPITAL_ACCOUNT",
        "research": list(RESEARCH),
        "validation": list(VALIDATION),
        "denied": list(DENIED),
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
        },
        "restatement_risk": True,
        "cagr_target_not_a_gate": CAGR_TARGET,
        "hypotheses": [dict(h) for h in FIN_HYPOTHESES],
    }
    payload["contract_hash"] = canonical_hash(payload)
    return payload


def build_industry_contract(blocked=True):
    payload = {
        "id": V16_ID + "_INDUSTRY_ALPHA",
        "blocked": blocked,
        "reason": "INDUSTRY_PIT_BLOCKED_CURRENT_ONLY",
        "max_hypotheses": MAX_IND_HYP,
        "hypotheses": [dict(h) for h in IND_HYPOTHESES],
        "new_purchase": NEW_PURCHASE,
        "final_oos": FINAL_OOS_ACCESS,
    }
    payload["contract_hash"] = canonical_hash(payload)
    return payload
