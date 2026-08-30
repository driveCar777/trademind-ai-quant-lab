"""Scan owned frozen datasets. No download. No purchase."""
from __future__ import print_function

import json
import os

from research_engine.v9_master.paths import IMMUTABLE, MARKET, OUT, RESEARCH, ensure_dir


QUALIFIED_CORE = {
    "tm-market-GOLD-M15-20260825-000001",
    "tm-market-GOLD-H1-20260825-000001",
    "tm-market-GOLD-H4-20260825-000001",
    "tm-market-GOLD-D1-20260825-000001",
    "tm-market-EURUSD-M15-20260825-000001",
    "tm-market-EURUSD-H1-20260825-000001",
    "tm-market-EURUSD-H4-20260825-000001",
    "tm-market-EURUSD-D1-20260825-000001",
    "tm-market-USDJPY-M15-20260825-000001",
    "tm-market-USDJPY-H1-20260825-000001",
    "tm-market-USDJPY-H4-20260825-000001",
    "tm-market-USDJPY-D1-20260825-000001",
    "tm-market-OIL-M15-20260825-000001",
    "tm-market-OIL-H1-20260825-000001",
    "tm-market-OIL-H4-20260825-000001",
    "tm-market-OIL-D1-20260825-000001",
}

CORE_LOGICAL = ("GOLD", "EURUSD", "USDJPY", "OIL")


def _load(path):
    handle = open(path, "r")
    try:
        return json.load(handle)
    finally:
        handle.close()


def _cost_class(dataset_id, source):
    if dataset_id.startswith("tm-fut-"):
        return "PAID" if source == "databento" else "DERIVED"
    if dataset_id.startswith("tm-alt-"):
        return "FREE"
    if dataset_id.startswith("tm-market-"):
        return "FREE"
    if dataset_id.startswith("tm-align-"):
        return "DERIVED"
    return "DERIVED"


def _info_layer(dataset_id, source):
    if dataset_id.startswith("tm-fut-"):
        return "FUTURES"
    if dataset_id.startswith("tm-alt-"):
        return "PUBLIC"
    if dataset_id.startswith("tm-market-"):
        return "MT5"
    return "DERIVED"


def _profile_qualification(dataset_id):
    path = os.path.join(MARKET, "profiles", dataset_id, "dataset_profile.json")
    if not os.path.isfile(path):
        return None
    try:
        row = _load(path)
    except Exception:
        return None
    return row.get("qualification") or row.get("validation_status")


def scan_immutable():
    rows = []
    if not os.path.isdir(IMMUTABLE):
        return rows
    names = sorted(os.listdir(IMMUTABLE))
    for name in names:
        d = os.path.join(IMMUTABLE, name)
        man = os.path.join(d, "manifest.json")
        if not os.path.isdir(d) or not os.path.isfile(man):
            continue
        try:
            manifest = _load(man)
        except Exception:
            continue
        fields = manifest.get("columns") or manifest.get("schema") or []
        if isinstance(fields, str):
            fields = [fields]
        dataset_id = manifest.get("dataset_id") or name
        source = manifest.get("source") or manifest.get("vendor") or ""
        symbol = (
            manifest.get("logical_symbol")
            or manifest.get("mt5_symbol")
            or manifest.get("cftc_code")
            or ",".join(manifest.get("parents") or [])
            or None
        )
        row = {
            "dataset_id": dataset_id,
            "source": source,
            "cost_class": _cost_class(dataset_id, source),
            "information_layer": _info_layer(dataset_id, source),
            "symbol": symbol,
            "mt5_symbol": manifest.get("mt5_symbol"),
            "timeframe": manifest.get("timeframe"),
            "history": {
                "start": manifest.get("actual_start_utc") or manifest.get("data_start_utc") or manifest.get("ALIGNED_START"),
                "end": manifest.get("actual_end_utc") or manifest.get("data_end_utc") or manifest.get("ALIGNED_END"),
                "row_count": manifest.get("row_count") or manifest.get("actual_count"),
            },
            "fields": list(fields),
            "hash": manifest.get("sha256") or manifest.get("series_sha256"),
            "qualification": _profile_qualification(dataset_id)
            or manifest.get("validation_status")
            or manifest.get("qualification"),
            "in_qualified_core": dataset_id in QUALIFIED_CORE,
            "v9_execution_universe": (
                dataset_id in QUALIFIED_CORE
                or (
                    str(manifest.get("logical_symbol") or "") in CORE_LOGICAL
                    and str(manifest.get("timeframe") or "") in ("M15", "H1", "H4", "D1")
                )
            ),
            "path": d.replace("\\", "/"),
        }
        rows.append(row)
    return rows


def build_index():
    datasets = scan_immutable()
    counts = {"FREE": 0, "PAID": 0, "DERIVED": 0, "MT5": 0, "PUBLIC": 0, "FUTURES": 0}
    for row in datasets:
        counts[row["cost_class"]] = counts.get(row["cost_class"], 0) + 1
        counts[row["information_layer"]] = counts.get(row["information_layer"], 0) + 1
    payload = {
        "index_id": "DATA_ASSET_MASTER_INDEX_V9",
        "NEW_DATA_PURCHASE": False,
        "DATACOST": 0.0,
        "n_datasets": len(datasets),
        "counts": counts,
        "qualified_core_n": len(QUALIFIED_CORE),
        "execution_universe_logical": list(CORE_LOGICAL),
        "execution_universe_mt5": {
            "GOLD": "GOLD",
            "EURUSD": "EURUSD",
            "USDJPY": "USDJPY",
            "OIL": "CrudeOIL",
        },
        "notes": [
            "Canonical research core is the 16 tm-market-*-20260825-000001 datasets.",
            "Ava GOLD/OIL are CFDs. Not GC/CL futures.",
            "Pack E slim curve/OI/volume are DERIVED from already-paid Databento history.",
            "Options bytes = 0. Options are not in this index as a tradable dataset.",
            "Final OOS is DENIED and is not read.",
        ],
        "datasets": datasets,
    }
    return payload


def write_index():
    ensure_dir(OUT)
    payload = build_index()
    path = os.path.join(OUT, "DATA_ASSET_MASTER_INDEX_V9.json")
    handle = open(path, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    finally:
        handle.close()
    return path, payload
