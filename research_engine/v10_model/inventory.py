"""Locked feature universe. Observed/derived only. No inferred LLM features."""
from __future__ import print_function

import json
import os

from research_engine.v10_model.paths import DOCS, IMMUTABLE, MARKET, OUT, ROOT, ensure_dir


FEATURES = [
    {"feature_id": "ret1", "group": "G_PRICE", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-{ASSET}-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "1-bar close return"},
    {"feature_id": "ret5", "group": "G_PRICE", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-{ASSET}-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "5-bar close return"},
    {"feature_id": "ret20", "group": "G_PRICE", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-{ASSET}-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "20-bar close return"},
    {"feature_id": "ret60", "group": "G_PRICE", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-{ASSET}-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "60-bar close return"},
    {"feature_id": "ret120", "group": "G_PRICE", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-{ASSET}-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "120-bar close return"},
    {"feature_id": "range20", "group": "G_PRICE", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-{ASSET}-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "close location in 20-bar high-low"},
    {"feature_id": "month_end", "group": "G_PRICE", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-{ASSET}-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "calendar month-end dummy"},
    {"feature_id": "rv20", "group": "G_VOL", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-{ASSET}-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "20-bar return stdev"},
    {"feature_id": "rv60", "group": "G_VOL", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-{ASSET}-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "60-bar return stdev"},
    {"feature_id": "atr14_pct", "group": "G_VOL", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-{ASSET}-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "ATR14 / close"},
    {"feature_id": "spread_pct", "group": "G_VOL", "source": "MT5", "kind": "OBSERVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-{ASSET}-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "broker spread vs close"},
    {"feature_id": "tickvol_z20", "group": "G_VOL", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-{ASSET}-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "tick_volume z vs 20"},
    {"feature_id": "curve_slope", "group": "G_FUT", "source": "PACK_E", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 1, "dataset": "tm-fut-GLBX-CURVE-D1-20260829-000001", "timeframe": "D1", "economic_meaning": "front-second settlement slope after knowledge_time"},
    {"feature_id": "roll_yield", "group": "G_FUT", "source": "PACK_E", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 1, "dataset": "tm-fut-GLBX-CURVE-D1-20260829-000001", "timeframe": "D1", "economic_meaning": "official roll yield"},
    {"feature_id": "steepening", "group": "G_FUT", "source": "PACK_E", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 1, "dataset": "tm-fut-GLBX-CURVE-D1-20260829-000001", "timeframe": "D1", "economic_meaning": "1-day slope change"},
    {"feature_id": "backwardation", "group": "G_FUT", "source": "PACK_E", "kind": "OBSERVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 1, "dataset": "tm-fut-GLBX-CURVE-D1-20260829-000001", "timeframe": "D1", "economic_meaning": "backwardation flag"},
    {"feature_id": "dte", "group": "G_FUT", "source": "PACK_E", "kind": "OBSERVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 1, "dataset": "tm-fut-GLBX-OIFLOW-D1-20260830-000001", "timeframe": "D1", "economic_meaning": "days to front expiry"},
    {"feature_id": "oi_change", "group": "G_OI", "source": "PACK_E", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 2, "dataset": "tm-fut-GLBX-OIFLOW-D1-20260830-000001", "timeframe": "D1", "economic_meaning": "front OI change after OI knowledge_time"},
    {"feature_id": "new_longs", "group": "G_OI", "source": "PACK_E", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 2, "dataset": "tm-fut-GLBX-OIFLOW-D1-20260830-000001", "timeframe": "D1", "economic_meaning": "OI-flow new longs flag"},
    {"feature_id": "new_shorts", "group": "G_OI", "source": "PACK_E", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 2, "dataset": "tm-fut-GLBX-OIFLOW-D1-20260830-000001", "timeframe": "D1", "economic_meaning": "OI-flow new shorts flag"},
    {"feature_id": "other_ret20", "group": "G_XASSET", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-GOLD-D1-20260828-000001|tm-market-OIL-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "other of GOLD/OIL 20-bar return"},
    {"feature_id": "eurusd_ret20", "group": "G_XASSET", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-EURUSD-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "EURUSD 20-bar return"},
    {"feature_id": "usdjpy_ret20", "group": "G_XASSET", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-USDJPY-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "USDJPY 20-bar return as dollar proxy"},
    {"feature_id": "go_ratio_z60", "group": "G_XASSET", "source": "MT5", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 0, "dataset": "tm-market-GOLD-D1-20260828-000001|tm-market-OIL-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "log GOLD/OIL residual z60"},
    {"feature_id": "cot_z", "group": "G_PUBLIC", "source": "CFTC", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 5, "dataset": "tm-alt-CFTC-{ASSET}-COT-W1-20260828-000002", "timeframe": "W1", "economic_meaning": "weekly COT close as stored series"},
    {"feature_id": "cot_wow", "group": "G_PUBLIC", "source": "CFTC", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 5, "dataset": "tm-alt-CFTC-{ASSET}-COT-W1-20260828-000002", "timeframe": "W1", "economic_meaning": "COT week change"},
    {"feature_id": "eia_wow", "group": "G_PUBLIC", "source": "EIA", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 5, "dataset": "tm-alt-EIA-USCRUDE-STXSPR-W1-20260828-000001", "timeframe": "W1", "economic_meaning": "US crude stocks wow"},
    {"feature_id": "ust10_chg5", "group": "G_PUBLIC", "source": "UST", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 1, "dataset": "tm-alt-UST-DGS10-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "5-session UST10 change"},
    {"feature_id": "iv_z", "group": "G_PUBLIC", "source": "CBOE", "kind": "DERIVED", "tested_simple": "SIMPLE_RULE_KILLED", "lag": 1, "dataset": "tm-alt-CBOE-GVZ-D1-20260828-000001|tm-alt-CBOE-OVX-D1-20260828-000001", "timeframe": "D1", "economic_meaning": "GVZ (GOLD) or OVX (OIL) z20"},
]

GROUP_FEATURES = {
    "G_PRICE": ["ret1", "ret5", "ret20", "ret60", "ret120", "range20", "month_end"],
    "G_VOL": ["rv20", "rv60", "atr14_pct", "spread_pct", "tickvol_z20"],
    "G_FUT": ["curve_slope", "roll_yield", "steepening", "backwardation", "dte"],
    "G_OI": ["oi_change", "new_longs", "new_shorts"],
    "G_XASSET": ["other_ret20", "eurusd_ret20", "usdjpy_ret20", "go_ratio_z60"],
    "G_PUBLIC": ["cot_z", "cot_wow", "eia_wow", "ust10_chg5", "iv_z"],
}

ABLATION_GROUPS = {
    "ALL": ["G_PRICE", "G_VOL", "G_FUT", "G_OI", "G_XASSET", "G_PUBLIC"],
    "ALL_MINUS_FUT": ["G_PRICE", "G_VOL", "G_OI", "G_XASSET", "G_PUBLIC"],
    "ALL_MINUS_OI": ["G_PRICE", "G_VOL", "G_FUT", "G_XASSET", "G_PUBLIC"],
    "ALL_MINUS_PUBLIC": ["G_PRICE", "G_VOL", "G_FUT", "G_OI", "G_XASSET"],
    "ALL_MINUS_XASSET": ["G_PRICE", "G_VOL", "G_FUT", "G_OI", "G_PUBLIC"],
    "MT5_ONLY": ["G_PRICE", "G_VOL", "G_XASSET"],
}


def _manifest_history(dataset_id):
    path = os.path.join(IMMUTABLE, dataset_id, "manifest.json")
    if not os.path.isfile(path):
        return {"first_available": None, "last_available": None, "row_count": None}
    handle = open(path, "r")
    try:
        man = json.load(handle)
    finally:
        handle.close()
    hist = man.get("history") or man.get("coverage") or {}
    return {
        "first_available": hist.get("start") or man.get("start") or man.get("first_timestamp_utc"),
        "last_available": hist.get("end") or man.get("end") or man.get("last_timestamp_utc"),
        "row_count": hist.get("row_count") or man.get("row_count"),
    }


def _scan_immutable():
    if not os.path.isdir(IMMUTABLE):
        return []
    out = []
    for name in sorted(os.listdir(IMMUTABLE)):
        folder = os.path.join(IMMUTABLE, name)
        if not os.path.isdir(folder) or not name.startswith("tm-"):
            continue
        hist = _manifest_history(name)
        out.append({"dataset_id": name, "path": folder, "history": hist})
    return out


def _scan_research_engine():
    re_root = os.path.join(ROOT, "research_engine")
    names = []
    if os.path.isdir(re_root):
        for name in sorted(os.listdir(re_root)):
            path = os.path.join(re_root, name)
            if os.path.isdir(path) and not name.startswith("__"):
                names.append(name)
    return names


def _scan_docs():
    names = []
    if os.path.isdir(DOCS):
        for name in sorted(os.listdir(DOCS)):
            if name.endswith(".md"):
                names.append(name)
    return names


def _v9_index():
    path = os.path.join(MARKET, "research_engine", "master_backtest", "DATA_ASSET_MASTER_INDEX_V9.json")
    if not os.path.isfile(path):
        return None
    handle = open(path, "r")
    try:
        return json.load(handle)
    finally:
        handle.close()


def enrich_feature(feat, v9):
    row = dict(feat)
    row["provenance"] = feat["kind"]
    row["already_tested_as_simple_rule"] = True
    row["simple_rule_status"] = "SIMPLE_RULE_KILLED"
    row["allowed_as_model_input"] = feat["kind"] in ("OBSERVED", "DERIVED")
    row["inferred"] = False
    ds = feat.get("dataset") or ""
    probe = ds.replace("{ASSET}", "GOLD").split("|")[0]
    hist = _manifest_history(probe)
    if (hist.get("first_available") is None) and v9:
        for item in v9.get("datasets") or []:
            if item.get("dataset_id") == probe:
                h = item.get("history") or {}
                hist = {
                    "first_available": h.get("start"),
                    "last_available": h.get("end"),
                    "row_count": h.get("row_count"),
                }
                break
    row["first_available"] = hist.get("first_available")
    row["last_available"] = hist.get("last_available")
    row["causal_lag"] = feat.get("lag")
    return row


def build_universe():
    v9 = _v9_index()
    features = [enrich_feature(f, v9) for f in FEATURES]
    inferred = [f for f in features if f.get("kind") == "INFERRED"]
    if inferred:
        raise ValueError("INFERRED_FEATURES_NOT_ALLOWED")
    return {
        "index_id": "MODEL_FEATURE_UNIVERSE_V10",
        "NEW_DATA_PURCHASE": False,
        "NEW_DATA_DOWNLOAD": False,
        "inferred_allowed": False,
        "n_model_features": len(features),
        "n_owned_immutable_datasets": len(_scan_immutable()),
        "owned_immutable_datasets": _scan_immutable(),
        "v9_owned_count": None if v9 is None else v9.get("n_datasets") or (v9.get("counts") and sum((v9.get("counts") or {}).values())),
        "research_engine_packages": _scan_research_engine(),
        "research_docs": _scan_docs(),
        "note": "SIMPLE_RULE_KILLED does not ban the feature as a model input. It bans reopening the old single-rule hypothesis. Model interaction is a new experiment_id.",
        "features": features,
        "group_features": GROUP_FEATURES,
        "ablation_groups": ABLATION_GROUPS,
    }


def write_universe():
    ensure_dir(OUT)
    payload = build_universe()
    path = os.path.join(OUT, "MODEL_FEATURE_UNIVERSE_V10.json")
    handle = open(path, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    finally:
        handle.close()
    return path, payload
