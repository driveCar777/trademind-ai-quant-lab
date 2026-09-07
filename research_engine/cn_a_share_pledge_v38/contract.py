"""Write-once V38-L7 contract. One hypothesis. Written before the first run; no feature/param search after."""
from __future__ import print_function

from research_engine.cn_a_share_pledge_v38 import (
    DENIED, FDR_Q, FIRST_PRED_SESSIONS_AFTER_LIVE, HOLD_DAYS, LIVE_MIN_FRAC, MAX_HYPOTHESES, PLEDGE_DATASET_ID, PRICE_DATASET_HASH, PRICE_DATASET_ID, QUANTILE,
    RESEARCH, SAME_CLUSTER_CORR, SEED, SNAP_LAG_SESSIONS, SNAPSHOT_CUTOFF, STALE_SESSIONS, V38L7_ID, VALIDATION,
)
from research_engine.cn_a_share_pledge_v38.features import PL_FEATURES
from research_engine.cn_a_share_ml_v25 import EMBARGO, FIRST_PRED, LGBM_PARAMS, NO_REFIT_AFTER_RESEARCH, REFIT_EVERY, ROLLING_BLOCKS, ROLLING_MIN_POSITIVE, TRAIN_STRIDE
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash

HYPOTHESES = (
    {
        "id": "ML6P_LGBM_PLEDGE_ONLY",
        "family": "EQUITY_PLEDGE_MODEL",
        "signal": "ML6P_LGBM",
        "features": [f[0] for f in PL_FEATURES],
        "mechanism": "Controller equity-pledge level, 20/60-session change, deal count, pledged cap vs liquidity and a price-stress "
                     "interaction from weekly CSDC snapshots. Literature recorded BEFORE the run: high / rising pledge ratios predict "
                     "crash risk and underperformance (2018 forced-liquidation wave); low or falling pledge = healthier controller. "
                     "Long side = low-pledge names. One fitted model on this layer alone; LO20 gate; independence vs ML1 by excess series.",
        "not": "FEATURE_SEARCH; WINDOW_SEARCH; HYPERPARAMETER_SEARCH; REFIT_AFTER_RESEARCH; SELECTING_ON_VALIDATION; SWITCHING_BOOK; "
               "USING_AS_ML1_FILTER_AFTER_SEEING_RESULTS",
    },
)


def build_contract(pledge_hash, first_live, first_pred):
    if len(HYPOTHESES) != MAX_HYPOTHESES:
        raise RuntimeError("V38L7_LOCKS_EXACTLY_ONE")
    payload = {
        "id": V38L7_ID, "mission": "V38_EVOLUTION_MISSION S1 layer L7",
        "amendment": "RESEARCH_RULES_AMENDMENT_V1 (A1 LO20 gate, A2 rolling, A3 one model per layer, A4 excess-series cluster test)",
        "dataset_id": PRICE_DATASET_ID, "dataset_hash": PRICE_DATASET_HASH,
        "pledge_dataset_id": PLEDGE_DATASET_ID, "pledge_content_hash": pledge_hash,
        "pledge_source": "Eastmoney datacenter RPT_CSDC_LIST (中登 weekly 股权质押, TRADE_DATE = Friday); free; 2014-03 ->",
        "pledge_pit": "snapshot visible first session after TRADE_DATE + %d sessions; carried forward <= %d sessions; absent name = zero pledge; "
                      "snapshots after %s dropped" % (SNAP_LAG_SESSIONS - 1, STALE_SESSIONS, SNAPSHOT_CUTOFF),
        "effective_start": "layer live from %s; sessions with < %.0f%% of eligible names live are excluded from training and scoring "
                           "(research period effectively 2014-03 -> 2021-08; declared before run)" % (first_live, LIVE_MIN_FRAC * 100),
        "upstream_pit_layers": ["V38-L7 equity pledge (6)"],
        "live_api": False, "new_purchase": False, "cost_usd": 0.0, "modify_ml1": False,
        "features": [{"name": f[0], "layer": f[1], "ml0_sign": f[2]} for f in PL_FEATURES],
        "feature_transform": "cross-sectional rank in [0,1] per session over eligible live names",
        "universe": "all eligible names in the frozen panel on live sessions",
        "label": "cross-sectional rank of open(t+1)->open(t+1+%d) return minus 0.5" % HOLD_DAYS,
        "model": {"type": "lightgbm.LGBMRegressor", "params": LGBM_PARAMS, "note": "identical to V25/V27/V38-L1/L4; not tuned"},
        "walk_forward": {"first_pred": first_pred, "first_pred_rule": "layer live start + %d sessions (V25 rule of >= 2 years of labels; V25 global %s not applicable to a 2014 layer)"
                         % (FIRST_PRED_SESSIONS_AFTER_LIVE, FIRST_PRED), "refit_every_sessions": REFIT_EVERY, "embargo_sessions": EMBARGO,
                         "train_stride_sessions": TRAIN_STRIDE, "expanding": True, "frozen_after_research": NO_REFIT_AFTER_RESEARCH},
        "no_search": "features, lag, transform, label, params and schedule fixed here; one run",
        "signal_price": "RAW_CLOSE_T", "execution_price": "RAW_OPEN_T1", "hold_days": HOLD_DAYS, "quantile": QUANTILE,
        "books": {"gate": "LO20 legacy long-only (A1)", "secondary": "HN20 hedged (reported only)", "predictive": "overlapping MEAN_FORWARD_RETURN excess vs eligible EW"},
        "cost_model_stock": {"commission": COMMISSION, "transfer": TRANSFER, "slippage": SLIPPAGE, "stamp_old": STAMP_OLD, "stamp_new": STAMP_NEW},
        "research": RESEARCH, "validation": VALIDATION, "denied": DENIED,
        "rolling_blocks": [list(b) for b in ROLLING_BLOCKS],
        "level1_gate": "fixed-split gates (pred net>0 both, excess/IC evidence>=2 both, FDR q=%.2f, LO20 capital>0 both) AND excess>0 in >= %d of %d rolling blocks"
                       % (FDR_Q, ROLLING_MIN_POSITIVE, len(ROLLING_BLOCKS)),
        "independence_test": "A4: corr of excess-vs-EW series vs ML1 (V25 SCORES_ML1_LGBM); > %.2f = SAME_CLUSTER" % SAME_CLUSTER_CORR,
        "fdr_q": FDR_Q, "fdr_m_layer": MAX_HYPOTHESES, "same_cluster_corr": SAME_CLUSTER_CORR, "seed": SEED, "final_oos": "DENIED",
        "verdict_labels": {"pass": "A_SHARE_EQUITY_PLEDGE_V38L7_INDEPENDENT_CANDIDATE", "same_cluster": "A_SHARE_EQUITY_PLEDGE_V38L7_SAME_CLUSTER",
                           "fail": "A_SHARE_EQUITY_PLEDGE_V38L7_NO_CANDIDATE"},
        "hypotheses": [dict(h) for h in HYPOTHESES],
    }
    payload["contract_hash"] = canonical_hash(payload)
    return payload
