"""Write-once V38-L4 contract. One hypothesis. Written before the first run; no feature/param search after."""
from __future__ import print_function

from research_engine.cn_a_share_insider_v38 import (
    DENIED, EXEC_LAG_SESSIONS, FDR_Q, HOLD_DAYS, INSIDER_DATASET_ID, MAX_HYPOTHESES, NOTICE_CUTOFF, PRICE_DATASET_HASH,
    PRICE_DATASET_ID, QUANTILE, RESEARCH, SAME_CLUSTER_CORR, SEED, V38L4_ID, VALIDATION, WINDOW_SESSIONS,
)
from research_engine.cn_a_share_insider_v38.features import INS_FEATURES
from research_engine.cn_a_share_ml_v25 import EMBARGO, FIRST_PRED, LGBM_PARAMS, NO_REFIT_AFTER_RESEARCH, REFIT_EVERY, ROLLING_BLOCKS, ROLLING_MIN_POSITIVE, TRAIN_STRIDE
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash

HYPOTHESES = (
    {
        "id": "ML5I_LGBM_INSIDER_ONLY",
        "family": "INSIDER_HOLDER_TRADES_MODEL",
        "signal": "ML5I_LGBM",
        "features": [f[0] for f in INS_FEATURES],
        "mechanism": "Disclosed trades by major holders (>=5 pct, 董监高 via 股东增减持) and executives (高管持股变动) over a trailing %d-session "
                     "window, scaled by the stock's own liquidity. US literature: insider net buying predicts returns. A-share literature "
                     "recorded BEFORE the run: executives show little timing ability on sales; controllers' sales bump then reverse; "
                     "purchases may carry information. One fitted model on this layer alone; LO20 gate; independence vs ML1 by excess series."
                     % WINDOW_SESSIONS,
        "not": "FEATURE_SEARCH; WINDOW_SEARCH; HYPERPARAMETER_SEARCH; REFIT_AFTER_RESEARCH; SELECTING_ON_VALIDATION; SWITCHING_BOOK; "
               "SPLITTING_BUY_ONLY_AFTER_SEEING_RESULTS",
    },
)


def build_contract(insider_hash):
    if len(HYPOTHESES) != MAX_HYPOTHESES:
        raise RuntimeError("V38L4_LOCKS_EXACTLY_ONE")
    payload = {
        "id": V38L4_ID, "mission": "V38_EVOLUTION_MISSION S1 layer L4",
        "amendment": "RESEARCH_RULES_AMENDMENT_V1 (A1 LO20 gate, A2 rolling, A3 one model per layer, A4 excess-series cluster test)",
        "dataset_id": PRICE_DATASET_ID, "dataset_hash": PRICE_DATASET_HASH,
        "insider_dataset_id": INSIDER_DATASET_ID, "insider_content_hash": insider_hash,
        "insider_source": "Eastmoney datacenter RPT_SHARE_HOLDER_INCREASE (股东增减持, NOTICE_DATE) + RPT_EXECUTIVE_HOLD_DETAILS (高管持股变动, CHANGE_DATE); free",
        "insider_pit": "HOLDER visible first session strictly after NOTICE_DATE; EXEC visible CHANGE_DATE + %d sessions (disclosure due within 2 trading days); "
                       "rows visible after %s dropped" % (EXEC_LAG_SESSIONS, NOTICE_CUTOFF),
        "window_sessions": WINDOW_SESSIONS, "amount_scale": "20-session mean daily traded amount at t",
        "upstream_pit_layers": ["V38-L4 insider/holder trades (7)"],
        "live_api": False, "new_purchase": False, "cost_usd": 0.0, "modify_ml1": False,
        "features": [{"name": f[0], "layer": f[1], "ml0_sign": f[2]} for f in INS_FEATURES],
        "feature_transform": "cross-sectional rank in [0,1] per session over eligible names; names without an event in the window are NaN",
        "universe": "all eligible names in the frozen panel; NOT restricted to event names (declared before run)",
        "label": "cross-sectional rank of open(t+1)->open(t+1+%d) return minus 0.5" % HOLD_DAYS,
        "model": {"type": "lightgbm.LGBMRegressor", "params": LGBM_PARAMS, "note": "identical to V25/V27/V38-L1; not tuned"},
        "walk_forward": {"first_pred": FIRST_PRED, "refit_every_sessions": REFIT_EVERY, "embargo_sessions": EMBARGO,
                         "train_stride_sessions": TRAIN_STRIDE, "expanding": True, "frozen_after_research": NO_REFIT_AFTER_RESEARCH},
        "no_search": "features, window, transform, label, params and schedule fixed here; one run",
        "signal_price": "RAW_CLOSE_T", "execution_price": "RAW_OPEN_T1", "hold_days": HOLD_DAYS, "quantile": QUANTILE,
        "books": {"gate": "LO20 legacy long-only (A1)", "secondary": "HN20 hedged (reported only)", "predictive": "overlapping MEAN_FORWARD_RETURN excess vs eligible EW"},
        "cost_model_stock": {"commission": COMMISSION, "transfer": TRANSFER, "slippage": SLIPPAGE, "stamp_old": STAMP_OLD, "stamp_new": STAMP_NEW},
        "research": RESEARCH, "validation": VALIDATION, "denied": DENIED,
        "rolling_blocks": [list(b) for b in ROLLING_BLOCKS],
        "level1_gate": "fixed-split gates (pred net>0 both, excess/IC evidence>=2 both, FDR q=%.2f, LO20 capital>0 both) AND excess>0 in >= %d of %d rolling blocks"
                       % (FDR_Q, ROLLING_MIN_POSITIVE, len(ROLLING_BLOCKS)),
        "independence_test": "A4: corr of excess-vs-EW series vs ML1 (V25 SCORES_ML1_LGBM); > %.2f = SAME_CLUSTER" % SAME_CLUSTER_CORR,
        "fdr_q": FDR_Q, "fdr_m_layer": MAX_HYPOTHESES, "same_cluster_corr": SAME_CLUSTER_CORR, "seed": SEED, "final_oos": "DENIED",
        "verdict_labels": {"pass": "A_SHARE_INSIDER_TRADES_V38L4_INDEPENDENT_CANDIDATE", "same_cluster": "A_SHARE_INSIDER_TRADES_V38L4_SAME_CLUSTER",
                           "fail": "A_SHARE_INSIDER_TRADES_V38L4_NO_CANDIDATE"},
        "hypotheses": [dict(h) for h in HYPOTHESES],
    }
    payload["contract_hash"] = canonical_hash(payload)
    return payload
