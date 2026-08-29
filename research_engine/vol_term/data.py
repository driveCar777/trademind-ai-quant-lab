"""Load GOLD D1 + GOLD H1 + US500 D1. Hash mismatch stops."""
from __future__ import print_function

import os

from research_engine.errors import ContractMismatch
from research_engine.vol_term import BASKET, EXPECTED_SHA, H1_ID, LOGICAL, PARENTS
from research_engine.vol_term.features import daily_h1_rv, tag_book
from research_protocol.bars import load_dataset


def load_one(market_root, dataset_id, want_tf):
    if dataset_id not in PARENTS:
        raise ContractMismatch("CONTRACT_MISMATCH")
    folder = os.path.join(market_root, dataset_id)
    manifest, bars, sha = load_dataset(folder)
    if manifest.get("dataset_id") != dataset_id or manifest.get("timeframe") != want_tf:
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


def align(packed, names):
    sets = []
    i = 0
    while i < len(names):
        sets.append(set(b.get("date") for b in packed[names[i]]["bars"]))
        i += 1
    common = sorted(set.intersection(*sets))
    if len(common) < 400:
        raise ContractMismatch("DATA_MISMATCH")
    aligned = {}
    for name in names:
        by_date = {}
        for bar in packed[name]["bars"]:
            by_date[bar["date"]] = bar
        aligned[name] = [by_date[d] for d in common]
    return common, aligned


def load_parents(market_root, dataset_ids=None):
    packed = {}
    for dataset_id in list(dataset_ids or PARENTS):
        want = "H1" if dataset_id == H1_ID else "D1"
        row = load_one(market_root, dataset_id, want)
        packed[row["logical"]] = row
    for name in BASKET:
        if name not in packed:
            raise ContractMismatch("DATA_MISMATCH")
    if "GOLD_H1" not in packed:
        raise ContractMismatch("DATA_MISMATCH")
    common, aligned = align(packed, BASKET)
    h1_rv = daily_h1_rv(packed["GOLD_H1"]["bars"])
    packed["_aligned"] = aligned
    packed["_book"] = tag_book(aligned, h1_rv)
    packed["_n_common"] = len(common)
    packed["_n_h1_rv_days"] = len(h1_rv)
    return packed
