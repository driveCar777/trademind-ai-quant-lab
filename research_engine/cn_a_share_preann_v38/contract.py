"""Write-once V38-L1 contract. One hypothesis (m=1 within the layer; V38 mission FDR counts it). Written before the first run."""
from __future__ import print_function

from research_engine.cn_a_share_ml_v25 import EMBARGO, FIRST_PRED, LGBM_PARAMS, NO_REFIT_AFTER_RESEARCH, REFIT_EVERY, ROLLING_BLOCKS, ROLLING_MIN_POSITIVE, TRAIN_STRIDE
from research_engine.cn_a_share_preann_v38 import (
    DENIED, EVENT_HORIZON_SESSIONS, FDR_Q, HOLD_DAYS, MAX_HYPOTHESES, MAX_NOTICE_LAG_DAYS, NOTICE_CUTOFF, PREANN_DATASET_ID,
    PRICE_DATASET_HASH, PRICE_DATASET_ID, QUANTILE, RESEARCH, SAME_CLUSTER_CORR, SEED, V38L1_ID, VALIDATION,
)
from research_engine.cn_a_share_preann_v38.features import PA_FEATURES
from research_engine.cn_a_share_strategy_v14.cost import COMMISSION, SLIPPAGE, STAMP_NEW, STAMP_OLD, TRANSFER
from research_protocol.hashing import canonical_hash

HYPOTHESES = (
    {
        "id": "ML4P_LGBM_PREANN_ONLY",
        "family": "PREANNOUNCEMENT_EVENT_MODEL",
        "signal": "ML4P_LGBM",
        "features": [f[0] for f in PA_FEATURES],
        "mechanism": "Earnings pre-announcements (业绩预告/快报) arrive weeks before the formal filing used by V27 and carry the "
                     "company's own surprise statement (yoy range, type, revenue), its timing (early voluntary disclosure), and "
                     "the market's first reaction (announcement gap, 3-session drift, abnormal volume). Post-earnings-announcement "
                     "drift in A-shares is documented to persist for months with slow decay (东方证券 2018 SUE; 天风 2020 净利润断层: "
                     "预告 > 正式财报 > 快报). One fitted cross-sectional model on this layer alone. If Level-1 and its excess-vs-EW "
                     "series is uncorrelated (<= %.2f) with ML1, it is a SECOND independent sleeve." % SAME_CLUSTER_CORR,
        "not": "FEATURE_SEARCH; HYPERPARAMETER_SEARCH; REFIT_AFTER_RESEARCH; SELECTING_FEATURES_ON_VALIDATION; "
               "SWITCHING_BOOK_AFTER_SEEING_HN20; RESTRICTING_UNIVERSE_AFTER_SEEING_RESULTS",
    },
)


def build_contract(preann_hash):
    if len(HYPOTHESES) != MAX_HYPOTHESES:
        raise RuntimeError("V38L1_LOCKS_EXACTLY_ONE")
    payload = {
        "id": V38L1_ID,
        "mission": "V38_EVOLUTION_MISSION S1 layer L1",
        "amendment": "RESEARCH_RULES_AMENDMENT_V1 (A1 LO20 gate book pre-registered, A2 rolling validation, A3 one model per layer, A4 excess-series cluster test)",
        "dataset_id": PRICE_DATASET_ID,
        "dataset_hash": PRICE_DATASET_HASH,
        "preann_dataset_id": PREANN_DATASET_ID,
        "preann_content_hash": preann_hash,
        "preann_source": "Eastmoney datacenter RPT_PUBLIC_OP_NEWPREDICT (业绩预告) + RPT_FCI_PERFORMANCEE (业绩快报); free; mirrors exchange filings",
        "preann_pit": "visible from first session strictly after NOTICE_DATE, for <= %d sessions or until a newer event; notice lag vs period end "
                      "must be within [-200, %d] days (else IPO back-fill / vendor re-dating, dropped); NOTICE_DATE > %s dropped"
                      % (EVENT_HORIZON_SESSIONS, MAX_NOTICE_LAG_DAYS, NOTICE_CUTOFF),
        "preann_caveats": {"forecast_versions": "table keeps only the latest version per (stock, period, line); a revised forecast is seen once at its revision date; conservative",
                           "express_backfill": "~60% of EXPRESS rows carry NOTICE_DATE > 1 year after period end (re-dated); dropped by the lag rule"},
        "upstream_pit_layers": ["V38-L1 pre-announcement (9)"],
        "live_api": False, "new_purchase": False, "cost_usd": 0.0, "modify_ml1": False,
        "features": [{"name": f[0], "layer": f[1], "ml0_sign": f[2]} for f in PA_FEATURES],
        "feature_transform": "cross-sectional rank in [0,1] per session over eligible names; names without a live event are NaN (LightGBM missing branch); "
                             "PA_TYPE / PA_NEG_AGE ties broken by 1e-3 * clipped surprise",
        "universe": "all eligible names in the frozen panel (listed, trading, non-ST, >= 40 sessions history); NOT restricted to event names (declared before run)",
        "label": "cross-sectional rank of open(t+1)->open(t+1+%d) return minus 0.5" % HOLD_DAYS,
        "model": {"type": "lightgbm.LGBMRegressor", "params": LGBM_PARAMS, "note": "identical to V25/V27; not tuned"},
        "walk_forward": {"first_pred": FIRST_PRED, "refit_every_sessions": REFIT_EVERY, "embargo_sessions": EMBARGO,
                         "train_stride_sessions": TRAIN_STRIDE, "expanding": True, "frozen_after_research": NO_REFIT_AFTER_RESEARCH},
        "no_search": "features, transform, label, params, horizon and schedule fixed here; one run; no second configuration",
        "signal_price": "RAW_CLOSE_T", "execution_price": "RAW_OPEN_T1", "hold_days": HOLD_DAYS, "quantile": QUANTILE,
        "books": {"gate": "LO20 legacy long-only (A1 pre-registered)", "secondary": "HN20 hedged (reported only, never the gate)",
                  "predictive": "overlapping MEAN_FORWARD_RETURN excess vs eligible EW"},
        "cost_model_stock": {"commission": COMMISSION, "transfer": TRANSFER, "slippage": SLIPPAGE, "stamp_old": STAMP_OLD, "stamp_new": STAMP_NEW},
        "research": RESEARCH, "validation": VALIDATION, "denied": DENIED,
        "rolling_blocks": [list(b) for b in ROLLING_BLOCKS],
        "level1_gate": "fixed-split gates (pred net>0 both, excess/IC evidence>=2 both, FDR q=%.2f, LO20 capital>0 research and validation) "
                       "AND positive excess-vs-EW in >= %d of %d rolling blocks" % (FDR_Q, ROLLING_MIN_POSITIVE, len(ROLLING_BLOCKS)),
        "independence_test": "A4: corr of excess-vs-EW MEAN_FORWARD series vs ML1 (V25 SCORES_ML1_LGBM) and vs V27 ML2F; > %.2f = SAME_CLUSTER" % SAME_CLUSTER_CORR,
        "fdr_q": FDR_Q, "fdr_m_layer": MAX_HYPOTHESES, "same_cluster_corr": SAME_CLUSTER_CORR,
        "seed": SEED, "final_oos": "DENIED",
        "verdict_labels": {"pass": "A_SHARE_PREANNOUNCEMENT_V38L1_INDEPENDENT_CANDIDATE", "same_cluster": "A_SHARE_PREANNOUNCEMENT_V38L1_SAME_CLUSTER",
                           "fail": "A_SHARE_PREANNOUNCEMENT_V38L1_NO_CANDIDATE"},
        "hypotheses": [dict(h) for h in HYPOTHESES],
    }
    payload["contract_hash"] = canonical_hash(payload)
    return payload
