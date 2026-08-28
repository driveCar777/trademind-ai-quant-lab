"""Load GOLD + SILVER + DXY D1. Hash mismatch stops. Not V0.8 pair return."""
from __future__ import print_function

import os

from research_engine.errors import ContractMismatch
from research_engine.usd_metal import EXPECTED_SHA, LOGICAL, PARENTS, TARGETS
from research_engine.usd_metal.features import dxy_events, tag_bars
from research_protocol.bars import load_dataset


def load_one(market_root, dataset_id):
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
    return {
        "dataset_id": dataset_id,
        "logical": LOGICAL[dataset_id],
        "manifest": manifest,
        "sha256": sha,
        "bars": out,
        "n": len(out),
    }


def load_parents(market_root, dataset_ids=None):
    packed = {}
    for dataset_id in list(dataset_ids or PARENTS):
        row = load_one(market_root, dataset_id)
        packed[row["logical"]] = row
    if "DXY" not in packed:
        raise ContractMismatch("DATA_MISMATCH")
    series = dxy_events(packed["DXY"]["bars"])
    for name in TARGETS:
        if name not in packed:
            raise ContractMismatch("DATA_MISMATCH")
        tag_bars(packed[name]["bars"], series)
    packed["_dxy_events"] = len(series)
    return packed
