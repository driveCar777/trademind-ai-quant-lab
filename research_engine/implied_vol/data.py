"""Load GOLD/OIL D1 plus CBOE IV series. Hash mismatch stops."""
from __future__ import print_function

import csv
import os

from research_engine.errors import ContractMismatch
from research_engine.implied_vol import EXPECTED_SHA, FEATURE_PARENTS, LOGICAL, PARENTS
from research_engine.implied_vol.features import tag_features
from research_protocol.bars import load_dataset


def load_iv_series(market_root, dataset_id):
    folder = os.path.join(market_root, dataset_id)
    series_path = os.path.join(folder, "series.csv")
    bars_path = os.path.join(folder, "bars.csv")
    if not os.path.isfile(series_path):
        raise ContractMismatch("DATA_MISMATCH")
    expected = EXPECTED_SHA.get(dataset_id)
    from research_protocol.hashing import file_sha256

    digest = file_sha256(bars_path)
    if expected and digest != expected:
        raise ContractMismatch("DATA_MISMATCH")
    by_date = {}
    handle = open(series_path, "r", encoding="utf-8")
    try:
        reader = csv.DictReader(handle)
        for row in reader:
            day = (row.get("date") or "").strip()
            raw = row.get("value")
            if not day or raw in (None, ""):
                continue
            by_date[day] = float(raw)
    finally:
        handle.close()
    if len(by_date) < 1000:
        raise ContractMismatch("DATA_MISMATCH")
    return {"dataset_id": dataset_id, "sha256": digest, "by_date": by_date, "n": len(by_date)}


def load_target(market_root, dataset_id, iv_pack):
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
    if logical == "GOLD":
        tag_features(out, iv_pack["GVZ"]["by_date"])
        i = 0
        while i < len(out):
            out[i]["is_gvz_z_cross"] = bool(out[i].get("is_iv_z_cross"))
            out[i]["is_gvz_vrp_rich_cross"] = bool(out[i].get("is_vrp_rich_cross"))
            out[i]["is_ovx_z_cross"] = False
            i += 1
    else:
        tag_features(out, iv_pack["OVX"]["by_date"])
        i = 0
        while i < len(out):
            out[i]["is_ovx_z_cross"] = bool(out[i].get("is_iv_z_cross"))
            out[i]["is_gvz_z_cross"] = False
            out[i]["is_gvz_vrp_rich_cross"] = False
            i += 1
    return {
        "dataset_id": dataset_id,
        "logical": logical,
        "manifest": manifest,
        "sha256": sha,
        "bars": out,
        "n": len(out),
    }


def load_parents(market_root, dataset_ids=None):
    iv_pack = {
        "GVZ": load_iv_series(market_root, FEATURE_PARENTS[0]),
        "OVX": load_iv_series(market_root, FEATURE_PARENTS[1]),
    }
    packed = {}
    for dataset_id in list(dataset_ids or PARENTS):
        row = load_target(market_root, dataset_id, iv_pack)
        packed[row["logical"]] = row
    packed["_iv"] = iv_pack
    return packed
