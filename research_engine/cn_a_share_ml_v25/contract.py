"""Write-once V25 contract. Two hypotheses (m=2): the model and its no-fit baseline. No feature search after the first run."""
from __future__ import print_function

from research_engine.cn_a_share_ml_v25 import (
    BASIS_COST_ANNUAL, DENIED, EMBARGO, FDR_Q, FIRST_PRED, FUT_FEE_RT, FUT_SLIP_RT, HEDGE_INDEX, HOLD_DAYS,
    INDEX_DAILY_DATASET_ID, LGBM_PARAMS, MAX_HYPOTHESES, NO_REFIT_AFTER_RESEARCH, PRICE_DATASET_HASH, PRICE_DATASET_ID,
    QUANTILE, REFIT_EVERY, RESEARCH, ROLLING_BLOCKS, ROLLING_MIN_POSITIVE, SAME_CLUSTER_CORR, SEED, STOCK_FRACTION,
    TRAIN_STRIDE, V25_ID, VALIDATION,
)
from research_engine.cn_a_share_ml_v25.features import FEATURES
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash

HYPOTHESES = (
    {
        "id": "ML1_LGBM_STACK",
        "family": "MULTILAYER_MODEL",
        "signal": "ML1_LGBM",
        "mechanism": "Several weak, economically distinct A-share signals (low vol, short-term reversal, 12-1 momentum, low turnover, "
                     "small size, margin de-leveraging, holder concentration, ROE, profit growth, index membership) each carried "
                     "too little information alone to beat costs. A single cross-sectional model combining their ranks may.",
        "not": "FEATURE_SEARCH; HYPERPARAMETER_SEARCH; REFIT_AFTER_RESEARCH",
    },
    {
        "id": "ML0_RANK_AVERAGE",
        "family": "MULTILAYER_BASELINE",
        "signal": "ML0_RANKAVG",
        "mechanism": "Same features, equal-weight average of a-priori-signed ranks, no fitting. Tells whether any ML1 edge comes "
                     "from combination itself or from the fitted nonlinearity.",
        "not": "FITTED",
    },
)


def build_contract():
    if len(HYPOTHESES) != MAX_HYPOTHESES:
        raise RuntimeError("V25_LOCKS_EXACTLY_TWO")
    payload = {
        "id": V25_ID,
        "amendment": "RESEARCH_RULES_AMENDMENT_V1 (A1 construction menu, A2 rolling validation, A3 one model per layer)",
        "dataset_id": PRICE_DATASET_ID,
        "dataset_hash": PRICE_DATASET_HASH,
        "index_daily_dataset_id": INDEX_DAILY_DATASET_ID,
        "upstream_pit_layers": ["V13 price pack", "V16 FINANCIAL_ANNOUNCEMENT_DATE", "V20 index as-of snapshots",
                                "V23 margin PIT lag 1", "V24 holders HOLD_NOTICE_DATE"],
        "live_api": False,
        "new_purchase": False,
        "cost_usd": 0.0,
        "reopen_h11_h12": False,
        "reopen_v13_v24_as_hypotheses": False,
        "features": [{"name": f[0], "layer": f[1], "ml0_sign": f[2]} for f in FEATURES],
        "feature_transform": "cross-sectional rank in [0,1] per session over eligible names (HS300_MEMBER raw 0/1)",
        "label": "cross-sectional rank of open(t+1)->open(t+1+%d) return minus 0.5" % HOLD_DAYS,
        "model": {"type": "lightgbm.LGBMRegressor", "params": LGBM_PARAMS},
        "walk_forward": {"first_pred": FIRST_PRED, "refit_every_sessions": REFIT_EVERY, "embargo_sessions": EMBARGO,
                         "train_stride_sessions": TRAIN_STRIDE, "expanding": True, "frozen_after_research": NO_REFIT_AFTER_RESEARCH},
        "no_search": "features, transform, label, params and schedule are fixed here; one run; no second configuration",
        "universe": "eligible names in the frozen panel (listed, trading, non-ST, >= 40 sessions history)",
        "signal_price": "RAW_CLOSE_T",
        "execution_price": "RAW_OPEN_T1",
        "hold_days": HOLD_DAYS,
        "quantile": QUANTILE,
        "books": {
            "primary": "HN20 hedged-neutral: long top-quintile book (legacy LO20 fills/costs) with %.2f stock fraction, "
                       "short %s index futures 1:1 on filled notional; futures cost = basis %.1f%%/yr + fee %.6f + slip %.6f per round trip"
                       % (STOCK_FRACTION, HEDGE_INDEX, BASIS_COST_ANNUAL * 100, FUT_FEE_RT, FUT_SLIP_RT),
            "secondary": "LO20 legacy long-only (reported, not gated)",
            "predictive": "overlapping MEAN_FORWARD_RETURN excess vs eligible EW (unchanged)",
        },
        "cost_model_stock": {"commission": COMMISSION, "transfer": TRANSFER, "slippage": SLIPPAGE, "stamp_old": STAMP_OLD, "stamp_new": STAMP_NEW},
        "research": RESEARCH,
        "validation": VALIDATION,
        "denied": DENIED,
        "rolling_blocks": [list(b) for b in ROLLING_BLOCKS],
        "level1_gate": "fixed-split gates (pred net>0 both, excess/IC evidence>=2 both, FDR q=%.2f, HN20 capital>0 research and validation) "
                       "AND positive excess-vs-EW in >= %d of %d rolling blocks" % (FDR_Q, ROLLING_MIN_POSITIVE, len(ROLLING_BLOCKS)),
        "fdr_q": FDR_Q,
        "fdr_m": MAX_HYPOTHESES,
        "same_cluster_corr": SAME_CLUSTER_CORR,
        "diagnostics": "H11 (NEG_VOL_60) and V23 M1 re-read on HN20 book, labelled DIAGNOSTIC, never gated or promoted",
        "seed": SEED,
        "final_oos": "DENIED",
        "hypotheses": [dict(h) for h in HYPOTHESES],
    }
    payload["contract_hash"] = canonical_hash(payload)
    return payload
