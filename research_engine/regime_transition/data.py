"""Load GOLD/OIL D1 independently. Not the V0.8 1993 join. Hash mismatch stops."""
from __future__ import print_function

import os

from research_engine.errors import ContractMismatch
from research_engine.regime_transition import EXPECTED_SHA, LOGICAL, PARENTS
from research_protocol.bars import load_dataset


def date_key(timestamp_utc):
    if not timestamp_utc:
        return None
    return timestamp_utc[:10]


def slim_bar(bar, date=None):
    ts = bar.get("timestamp_utc")
    key = date or date_key(ts)
    return {
        "timestamp_utc": ts,
        "date": key,
        "open": bar.get("open"),
        "high": bar.get("high"),
        "low": bar.get("low"),
        "close": bar.get("close"),
        "spread": bar.get("spread"),
        "tick_volume": bar.get("tick_volume"),
    }


def load_target(market_root, dataset_id):
    if dataset_id not in PARENTS:
        raise ContractMismatch("CONTRACT_MISMATCH")
    folder = os.path.join(market_root, dataset_id)
    manifest, bars, sha = load_dataset(folder)
    if manifest.get("dataset_id") != dataset_id:
        raise ContractMismatch("DATA_MISMATCH")
    if manifest.get("timezone") != "UTC":
        raise ContractMismatch("DATA_MISMATCH")
    expected = EXPECTED_SHA.get(dataset_id)
    if expected and sha != expected:
        raise ContractMismatch("DATA_MISMATCH")
    out = []
    seen = {}
    for bar in bars:
        ts = bar.get("timestamp_utc") or ""
        if not ts.endswith("T00:00:00Z"):
            raise ContractMismatch("DATA_MISMATCH")
        key = date_key(ts)
        if key in seen:
            raise ContractMismatch("DATA_MISMATCH")
        seen[key] = True
        rec = slim_bar(bar, key)
        rec["role"] = None
        out.append(rec)
    return {
        "dataset_id": dataset_id,
        "logical": LOGICAL[dataset_id],
        "manifest": manifest,
        "sha256": sha,
        "bars": out,
        "n": len(out),
    }


def load_parents(market_root, dataset_ids=None):
    wanted = list(dataset_ids or PARENTS)
    packed = {}
    for dataset_id in wanted:
        row = load_target(market_root, dataset_id)
        packed[row["logical"]] = row
    return packed
