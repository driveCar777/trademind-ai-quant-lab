"""Write-once V27 contract. Two hypotheses (m=2). Written before the first run; no feature/param search after."""
from __future__ import print_function

from research_engine.cn_a_share_findeep_v27 import (
    DENIED, FDR_Q, FINDEEP_DATASET_ID, HOLD_DAYS, MAX_HYPOTHESES, NOTICE_CUTOFF, PRICE_DATASET_HASH, PRICE_DATASET_ID,
    QUANTILE, RESEARCH, SAME_CLUSTER_CORR, SEED, V27_ID, VALIDATION,
)
from research_engine.cn_a_share_findeep_v27.features import FEATURES_ML2, FEATURES_ML2F
from research_engine.cn_a_share_ml_v25 import EMBARGO, FIRST_PRED, LGBM_PARAMS, NO_REFIT_AFTER_RESEARCH, REFIT_EVERY, ROLLING_BLOCKS, ROLLING_MIN_POSITIVE, TRAIN_STRIDE
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash

HYPOTHESES = (
    {
        "id": "ML2F_LGBM_FINDEEP_ONLY",
        "family": "FINANCIAL_DEEP_MODEL",
        "signal": "ML2F_LGBM",
        "features": [f[0] for f in FEATURES_ML2F],
        "mechanism": "Quarterly filings carry information the annual ratios of V16/V25 did not: earnings surprise (PEAD), revenue "
                     "growth, accrual quality, cash generation, margin trend, asset growth, leverage change, and price-scaled "
                     "value (EP/BP). One fitted cross-sectional model on this layer alone. If Level-1 and its excess-vs-EW series "
                     "is uncorrelated (<= %.2f) with ML1 and H11, it is a SECOND independent sleeve." % SAME_CLUSTER_CORR,
        "not": "FEATURE_SEARCH; HYPERPARAMETER_SEARCH; REFIT_AFTER_RESEARCH; SELECTING_FEATURES_ON_VALIDATION",
    },
    {
        "id": "ML2_LGBM_FULL_STACK",
        "family": "FINANCIAL_DEEP_MODEL",
        "signal": "ML2_LGBM",
        "features": [f[0] for f in FEATURES_ML2],
        "mechanism": "ML1's 14 features plus the 10 deep-financial features in one model. Answers whether the quarterly layer adds "
                     "to the frozen ML1 stack. Pre-declared reading: ML2 contains ML1's inputs, so it is expected to sit in ML1's "
                     "cluster; a SAME_CLUSTER result does NOT replace ML1 (the strategy stays ML1; switching would be selection "
                     "on validation). Only a Level-1 with excess corr <= %.2f vs ML1 counts as new." % SAME_CLUSTER_CORR,
        "not": "REPLACING_ML1_ON_VALIDATION_NUMBERS; FEATURE_SEARCH; REFIT_AFTER_RESEARCH",
    },
)


def build_contract(findeep_hash):
    if len(HYPOTHESES) != MAX_HYPOTHESES:
        raise RuntimeError("V27_LOCKS_EXACTLY_TWO")
    payload = {
        "id": V27_ID,
        "amendment": "RESEARCH_RULES_AMENDMENT_V1 (A1 LO20 book pre-registered as gate book, A2 rolling validation, A3 one model per layer = deep financials, A4 excess-series cluster test)",
        "dataset_id": PRICE_DATASET_ID,
        "dataset_hash": PRICE_DATASET_HASH,
        "findeep_dataset_id": FINDEEP_DATASET_ID,
        "findeep_content_hash": findeep_hash,
        "findeep_source": "Eastmoney datacenter RPT_LICO_FN_CPD (performance table) + RPT_DMSK_FN_BALANCE; free; mirrors exchange filings",
        "findeep_pit": "visible from first session strictly after NOTICE_DATE; filings with NOTICE_DATE > %s dropped; late stale report dates ignored" % NOTICE_CUTOFF,
        "findeep_tables_rejected": {"RPT_DMSK_FN_INCOME": "NOTICE_DATE = next-year comparative filing (~12 months late)", "RPT_DMSK_FN_CASHFLOW": "same"},
        "restatement_caveat": "values may be the latest restated figures with the original NOTICE_DATE (same caveat as V16/V25 BaoStock)",
        "upstream_pit_layers": ["V25 feature stack (14, frozen)", "V27 deep financial (10)"],
        "live_api": False,
        "new_purchase": False,
        "cost_usd": 0.0,
        "reopen_h11_h12": False,
        "modify_ml1": False,
        "features_ML2F": [{"name": f[0], "layer": f[1], "ml0_sign": f[2]} for f in FEATURES_ML2F],
        "features_ML2": [{"name": f[0], "layer": f[1], "ml0_sign": f[2]} for f in FEATURES_ML2],
        "feature_transform": "cross-sectional rank in [0,1] per session over eligible names (HS300_MEMBER raw 0/1)",
        "label": "cross-sectional rank of open(t+1)->open(t+1+%d) return minus 0.5" % HOLD_DAYS,
        "model": {"type": "lightgbm.LGBMRegressor", "params": LGBM_PARAMS, "note": "identical to V25; not tuned"},
        "walk_forward": {"first_pred": FIRST_PRED, "refit_every_sessions": REFIT_EVERY, "embargo_sessions": EMBARGO,
                         "train_stride_sessions": TRAIN_STRIDE, "expanding": True, "frozen_after_research": NO_REFIT_AFTER_RESEARCH},
        "no_search": "features, transform, label, params and schedule fixed here; one run; no second configuration",
        "universe": "eligible names in the frozen panel (listed, trading, non-ST, >= 40 sessions history)",
        "signal_price": "RAW_CLOSE_T",
        "execution_price": "RAW_OPEN_T1",
        "hold_days": HOLD_DAYS,
        "quantile": QUANTILE,
        "books": {"gate": "LO20 legacy long-only (A1 pre-registered; V26 found LO20 is the strategy book, HN20 a size-spread carrier)",
                  "secondary": "HN20 hedged (reported only)",
                  "predictive": "overlapping MEAN_FORWARD_RETURN excess vs eligible EW"},
        "cost_model_stock": {"commission": COMMISSION, "transfer": TRANSFER, "slippage": SLIPPAGE, "stamp_old": STAMP_OLD, "stamp_new": STAMP_NEW},
        "research": RESEARCH, "validation": VALIDATION, "denied": DENIED,
        "rolling_blocks": [list(b) for b in ROLLING_BLOCKS],
        "level1_gate": "fixed-split gates (pred net>0 both, excess/IC evidence>=2 both, FDR q=%.2f, LO20 capital>0 research and validation) "
                       "AND positive excess-vs-EW in >= %d of %d rolling blocks" % (FDR_Q, ROLLING_MIN_POSITIVE, len(ROLLING_BLOCKS)),
        "independence_test": "A4: corr of excess-vs-EW MEAN_FORWARD series vs ML1 (V25 SCORES_ML1_LGBM) and vs H11 NEG_VOL_60; > %.2f = SAME_CLUSTER" % SAME_CLUSTER_CORR,
        "fdr_q": FDR_Q, "fdr_m": MAX_HYPOTHESES, "same_cluster_corr": SAME_CLUSTER_CORR,
        "seed": SEED, "final_oos": "DENIED",
        "hypotheses": [dict(h) for h in HYPOTHESES],
    }
    payload["contract_hash"] = canonical_hash(payload)
    return payload
