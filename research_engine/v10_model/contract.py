"""Locked V10 model contract. Frozen before any fit."""
from __future__ import print_function

from research_engine.v10_model import (
    DATABENTO_HISTORICAL_SPEND,
    FDR_Q,
    FINAL_OOS_ACCESS,
    HOLD_BARS,
    LOOKBACKS,
    MAX_FEATURE_GROUPS,
    MAX_INTERACTIONS,
    MAX_MODELS,
    MAX_STATES,
    MAX_TARGETS,
    NEW_DATA_DOWNLOAD,
    NEW_DATA_PURCHASE,
    PRIMARY_THRESHOLD,
    RISK_FRACS,
    THRESHOLDS,
    V10_ID,
    V10_SEED,
    V10_VERSION,
)
from research_protocol.hashing import canonical_hash


TARGETS = (
    {
        "target_id": "T1_DIR1",
        "name": "next_open_direction_h1",
        "kind": "direction",
        "horizon_bars": 1,
        "definition": "sign(open[t+2] / open[t+1] - 1). NEXT_BAR_OPEN 1-bar hold.",
        "label": "1 if open[t+2] > open[t+1] else 0",
    },
    {
        "target_id": "T2_DIR5",
        "name": "next_open_direction_h5",
        "kind": "direction",
        "horizon_bars": 5,
        "definition": "sign(open[t+6] / open[t+1] - 1). NEXT_BAR_OPEN 5-bar hold.",
        "label": "1 if open[t+6] > open[t+1] else 0",
    },
)

MODELS = (
    {"model_id": "M0", "family": "NAIVE", "spec": "train_majority_and_base_rate"},
    {"model_id": "M1", "family": "LOGISTIC", "spec": "LogisticRegression C=1.0 max_iter=200"},
    {"model_id": "M2", "family": "TREE", "spec": "DecisionTreeClassifier max_depth=3 min_samples_leaf=20"},
    {"model_id": "M3", "family": "FOREST", "spec": "RandomForestClassifier n_estimators=20 max_depth=3 min_samples_leaf=20"},
)

REPRESENTATIONS = (
    {"rep_id": "REP_RAW", "name": "raw features"},
    {"rep_id": "REP_Z60", "name": "causal z-score lookback 60"},
    {"rep_id": "REP_INTERACT", "name": "10 pre-registered interactions on z60"},
    {"rep_id": "REP_STATE", "name": "5 locked state dummies plus z60"},
)

FEATURE_GROUPS = (
    {"group_id": "G_PRICE", "name": "Price / return"},
    {"group_id": "G_VOL", "name": "Volatility / friction"},
    {"group_id": "G_FUT", "name": "Futures structure"},
    {"group_id": "G_OI", "name": "Open interest flow"},
    {"group_id": "G_XASSET", "name": "Cross asset"},
    {"group_id": "G_PUBLIC", "name": "Public macro / positioning / IV index"},
)

INTERACTIONS = (
    {"id": "I01", "a": "ret20", "b": "rv20", "why": "momentum conditioned on realized vol"},
    {"id": "I02", "a": "ret20", "b": "other_ret20", "why": "GOLD/OIL joint risk"},
    {"id": "I03", "a": "ret20", "b": "usdjpy_ret20", "why": "dollar proxy times metal/oil"},
    {"id": "I04", "a": "curve_slope", "b": "oi_change", "why": "curve x OI interaction, not a reopened OI rule"},
    {"id": "I05", "a": "curve_slope", "b": "eia_wow", "why": "inventory surprise times curve"},
    {"id": "I06", "a": "oi_change", "b": "cot_z", "why": "daily OI times weekly positioning"},
    {"id": "I07", "a": "rv20", "b": "iv_z", "why": "RV vs public IV index"},
    {"id": "I08", "a": "month_end", "b": "ret20", "why": "calendar times momentum"},
    {"id": "I09", "a": "curve_slope", "b": "ret20", "why": "structure times price"},
    {"id": "I10", "a": "ust10_chg5", "b": "ret20", "why": "rates change times target return"},
)

STATES = (
    "TREND_LOWVOL",
    "TREND_HIGHVOL",
    "RANGE_LOWVOL",
    "RANGE_HIGHVOL",
    "WIDE_FRICTION",
)

ASSETS = ("GOLD", "OIL")

ABLATIONS = (
    "ALL",
    "ALL_MINUS_FUT",
    "ALL_MINUS_OI",
    "ALL_MINUS_PUBLIC",
    "ALL_MINUS_XASSET",
    "MT5_ONLY",
)


def build_contract():
    body = {
        "contract_id": "MODEL_CONTRACT_V10",
        "discovery_id": V10_ID,
        "version": V10_VERSION,
        "seed": V10_SEED,
        "FINAL_OOS_ACCESS": FINAL_OOS_ACCESS,
        "NEW_DATA_PURCHASE": NEW_DATA_PURCHASE,
        "NEW_DATA_DOWNLOAD": NEW_DATA_DOWNLOAD,
        "databento_historical_spend_usd": DATABENTO_HISTORICAL_SPEND,
        "unused_research_reserve_note": "remaining Databento credits are UNUSED_RESEARCH_RESERVE",
        "hypothesis": "Existing information may contain nonlinear/interaction structure not captured by simple rules. MODEL is not assumed to be alpha.",
        "split": {
            "method": "TIME_ORDER_70_15_15",
            "train": "research",
            "test": "validation",
            "unused_tail": "not used for fit, selection, or threshold choice",
            "random_split": False,
            "purge_bars": 5,
            "embargo_bars": 1,
        },
        "targets": list(TARGETS),
        "target_count": len(TARGETS),
        "models": list(MODELS),
        "model_count": len(MODELS),
        "representations": list(REPRESENTATIONS),
        "feature_groups": list(FEATURE_GROUPS),
        "lookbacks": list(LOOKBACKS),
        "lookback_search": False,
        "lookback_note": "20/60/120 are computed together as features, not three search axes.",
        "interactions": list(INTERACTIONS),
        "states": list(STATES),
        "assets": list(ASSETS),
        "ablations": list(ABLATIONS),
        "ablation_slice": {
            "model_id": "M1",
            "rep_id": "REP_Z60",
            "target_id": "T1_DIR1",
            "note": "Pre-registered diagnostic slice. Not chosen after PnL.",
        },
        "thresholds": list(THRESHOLDS),
        "primary_threshold": PRIMARY_THRESHOLD,
        "risk_frac": list(RISK_FRACS),
        "hold_bars": dict(HOLD_BARS),
        "execution": {
            "fill": "NEXT_BAR_OPEN",
            "close_fill": "FORBIDDEN",
            "venue": "MT5",
            "cost": "MASTER_BACKTEST_CONTRACT_V9",
        },
        "gates": {
            "predictive": "validation logloss/Brier better than M0 and AUC>0.5",
            "economic": "costed validation net>0 and not one-symbol",
            "candidate": "research+validation costed positive, FDR q=0.05, >=2 assets, no Final OOS",
            "fdr_q": FDR_Q,
        },
        "forbidden": {
            "automl": True,
            "hyperparameter_search": True,
            "target_farm": True,
            "live_internet_feature": True,
            "llm_news": True,
            "a_share": True,
            "options": True,
            "new_purchase": True,
        },
        "limits": {
            "max_models": MAX_MODELS,
            "max_feature_groups": MAX_FEATURE_GROUPS,
            "max_targets": MAX_TARGETS,
            "max_interactions": MAX_INTERACTIONS,
            "max_states": MAX_STATES,
        },
        "xavier": "NOT_REQUIRED_IF_LOCAL_RUNTIME_SMALL",
        "note": "Do not retune depth/threshold/lookback/hold after seeing results.",
    }
    hashed = dict(body)
    hashed.pop("contract_hash", None)
    body["contract_hash"] = canonical_hash(hashed)
    return body


def assert_contract(contract):
    if not contract or contract.get("contract_id") != "MODEL_CONTRACT_V10":
        raise ValueError("V10_CONTRACT_ID")
    if contract.get("FINAL_OOS_ACCESS") != FINAL_OOS_ACCESS:
        raise ValueError("V10_OOS")
    if contract.get("NEW_DATA_PURCHASE") is not False:
        raise ValueError("V10_PURCHASE")
    if contract.get("target_count") != 2:
        raise ValueError("V10_TARGETS")
    if contract.get("model_count") != 4:
        raise ValueError("V10_MODELS")
    if len(contract.get("interactions") or []) > MAX_INTERACTIONS:
        raise ValueError("V10_INTERACTIONS")
    expect = build_contract()
    if contract.get("contract_hash") != expect.get("contract_hash"):
        raise ValueError("V10_CONTRACT_HASH")
    return True
