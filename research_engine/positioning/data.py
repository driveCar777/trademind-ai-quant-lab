"""Load GOLD/OIL D1 plus CFTC COT series. Hash mismatch stops."""
from __future__ import print_function

import csv
import os

from research_engine.errors import ContractMismatch
from research_engine.positioning import EXPECTED_SHA, FEATURE_PARENTS, LOGICAL, PARENTS
from research_engine.positioning.features import tag_features
from research_protocol.bars import load_dataset
from research_protocol.hashing import file_sha256


def load_cot_series(market_root, dataset_id):
    folder = os.path.join(market_root, dataset_id)
    series_path = os.path.join(folder, "series.csv")
    bars_path = os.path.join(folder, "bars.csv")
    if not os.path.isfile(series_path):
        raise ContractMismatch("DATA_MISMATCH")
    expected = EXPECTED_SHA.get(dataset_id)
    digest = file_sha256(bars_path)
    if expected and digest != expected:
        raise ContractMismatch("DATA_MISMATCH")
    rows = []
    handle = open(series_path, "r", encoding="utf-8")
    try:
        reader = csv.DictReader(handle)
        for row in reader:
            item = {
                "date": (row.get("date") or "").strip(),
                "asof_date": (row.get("asof_date") or "").strip(),
                "knowledge_time_utc": (row.get("knowledge_time_utc") or "").strip(),
                "mm_net_oi": float(row["mm_net_oi"]) if row.get("mm_net_oi") not in (None, "") else None,
                "com_net_oi": float(row["com_net_oi"]) if row.get("com_net_oi") not in (None, "") else None,
            }
            if item["knowledge_time_utc"]:
                rows.append(item)
    finally:
        handle.close()
    rows.sort(key=lambda r: r["knowledge_time_utc"])
    if len(rows) < 100:
        raise ContractMismatch("DATA_MISMATCH")
    return {"dataset_id": dataset_id, "sha256": digest, "rows": rows, "n": len(rows)}


def load_target(market_root, dataset_id, cot_pack):
    if dataset_id not in PARENTS:
        raise ContractMismatch("CONTRACT_MISMATCH")
    folder = os.path.join(market_root, dataset_id)
    manifest, bars, sha = load_dataset(folder)
    if manifest.get("dataset_id") != dataset_id:
        raise ContractMismatch("DATA_MISMATCH")
    if manifest.get("timezone") != "UTC":
        raise ContractMismatch("DATA_MISMATCH")
    if manifest.get("timeframe") != "D1":
        raise ContractMismatch("DATA_MISMATCH")
    expected = EXPECTED_SHA.get(dataset_id)
    if expected and sha != expected:
        raise ContractMismatch("DATA_MISMATCH")
    out = []
    seen = {}
    for bar in bars:
        ts = bar.get("timestamp_utc") or ""
        if "T" not in ts or not ts.endswith("Z"):
            raise ContractMismatch("DATA_MISMATCH")
        if ts in seen:
            raise ContractMismatch("DATA_MISMATCH")
        seen[ts] = True
        out.append(
            {
                "timestamp_utc": ts,
                "date": ts[:10],
                "open": bar.get("open"),
                "high": bar.get("high"),
                "low": bar.get("low"),
                "close": bar.get("close"),
                "spread": bar.get("spread"),
                "tick_volume": bar.get("tick_volume"),
                "role": None,
            }
        )
    logical = LOGICAL[dataset_id]
    series = cot_pack[logical]["rows"]
    tag_features(out, series)
    return {
        "dataset_id": dataset_id,
        "logical": logical,
        "manifest": manifest,
        "sha256": sha,
        "bars": out,
        "n": len(out),
    }


def load_parents(market_root, dataset_ids=None):
    cot_pack = {
        "GOLD": load_cot_series(market_root, FEATURE_PARENTS[0]),
        "OIL": load_cot_series(market_root, FEATURE_PARENTS[1]),
    }
    packed = {}
    for dataset_id in list(dataset_ids or PARENTS):
        row = load_target(market_root, dataset_id, cot_pack)
        packed[row["logical"]] = row
    packed["_cot"] = cot_pack
    return packed
