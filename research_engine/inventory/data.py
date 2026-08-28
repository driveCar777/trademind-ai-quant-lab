"""Load GOLD/OIL D1 plus EIA weekly stocks. Hash mismatch stops."""
from __future__ import print_function

import csv
import os

from research_engine.errors import ContractMismatch
from research_engine.inventory import EXPECTED_SHA, FEATURE_PARENTS, LOGICAL, PARENTS
from research_engine.inventory.features import tag_features
from research_protocol.bars import load_dataset
from research_protocol.hashing import file_sha256


def load_inv_series(market_root, dataset_id):
    folder = os.path.join(market_root, dataset_id)
    series_path = os.path.join(folder, "series.csv")
    bars_path = os.path.join(folder, "bars.csv")
    if not os.path.isfile(series_path):
        raise ContractMismatch("DATA_MISMATCH")
    expected = EXPECTED_SHA.get(dataset_id)
    digest = file_sha256(bars_path)
    if expected and digest != expected:
        raise ContractMismatch("DATA_MISMATCH")
    raw = []
    handle = open(series_path, "r", encoding="utf-8")
    try:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row.get("knowledge_time_utc") or row.get("value") in (None, ""):
                continue
            raw.append(
                {
                    "week_ending": row.get("week_ending"),
                    "knowledge_time_utc": row["knowledge_time_utc"].strip(),
                    "value": float(row["value"]),
                }
            )
    finally:
        handle.close()
    raw.sort(key=lambda r: r["knowledge_time_utc"])
    prev = None
    rows = []
    for item in raw:
        wow = None if prev is None else item["value"] - prev
        item = dict(item)
        item["wow"] = wow
        rows.append(item)
        prev = item["value"]
    if len(rows) < 200:
        raise ContractMismatch("DATA_MISMATCH")
    return {"dataset_id": dataset_id, "sha256": digest, "rows": rows, "n": len(rows)}


def load_target(market_root, dataset_id, inv_pack):
    if dataset_id not in PARENTS:
        raise ContractMismatch("CONTRACT_MISMATCH")
    folder = os.path.join(market_root, dataset_id)
    manifest, bars, sha = load_dataset(folder)
    if manifest.get("dataset_id") != dataset_id or manifest.get("timeframe") != "D1":
        raise ContractMismatch("DATA_MISMATCH")
    expected = EXPECTED_SHA.get(dataset_id)
    if expected and sha != expected:
        raise ContractMismatch("DATA_MISMATCH")
    out = []
    seen = {}
    for bar in bars:
        ts = bar.get("timestamp_utc") or ""
        if ts in seen or "T" not in ts:
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
    tag_features(out, inv_pack["rows"])
    return {
        "dataset_id": dataset_id,
        "logical": LOGICAL[dataset_id],
        "manifest": manifest,
        "sha256": sha,
        "bars": out,
        "n": len(out),
    }


def load_parents(market_root, dataset_ids=None):
    inv_pack = load_inv_series(market_root, FEATURE_PARENTS[0])
    packed = {}
    for dataset_id in list(dataset_ids or PARENTS):
        row = load_target(market_root, dataset_id, inv_pack)
        packed[row["logical"]] = row
    packed["_inv"] = inv_pack
    return packed
