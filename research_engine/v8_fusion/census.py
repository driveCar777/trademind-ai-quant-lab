"""Full frozen-dataset census. Headers only. No raw zst."""
from __future__ import print_function

import csv
import json
import os

from research_engine.data_expansion.paths import repo_root
from research_engine.v8_fusion import BILLED_PACK_E_USD, CREDIT_REMAINING_USD


def _load(path):
    handle = open(path, encoding="utf-8")
    try:
        return json.load(handle)
    finally:
        handle.close()


def _csv_fields(path):
    if not os.path.isfile(path):
        return []
    handle = open(path, "r")
    try:
        reader = csv.reader(handle)
        row = next(reader, None)
        return list(row or [])
    finally:
        handle.close()


def _class_of(name, item):
    source = str(item.get("source") or "")
    did = str(item.get("dataset_id") or name)
    if source == "databento" or did.startswith("tm-fut-"):
        if "CURVE" in name:
            return "PAID", "pack_e_shared", "databento_historical_internal_research"
        return "DERIVED", 0, "derived_from_pack_e_internal"
    if did.startswith("tm-alt-"):
        return "FREE", 0, "public_vendor_terms"
    return "FREE", 0, "broker_terminal_internal"


def build_census():
    root = repo_root()
    folder = os.path.join(root, "data", "market", "immutable")
    rows = []
    for name in sorted(os.listdir(folder)):
        man = os.path.join(folder, name, "manifest.json")
        if not os.path.isfile(man):
            continue
        item = _load(man)
        klass, cost, license_ = _class_of(name, item)
        fields = []
        for fname in ("bars.csv", "curve.csv", "features.csv", "series.csv"):
            got = _csv_fields(os.path.join(folder, name, fname))
            if got:
                fields = got
                break
        derived = item.get("parent_dataset_id") or item.get("parent") or None
        rows.append(
            {
                "dataset_id": item.get("dataset_id") or name,
                "source": item.get("source") or item.get("vendor"),
                "cost": cost,
                "symbol": item.get("logical_symbol") or item.get("parents") or item.get("mt5_symbol"),
                "timeframe": item.get("timeframe") or item.get("schema"),
                "first": item.get("data_start_utc") or item.get("actual_start_utc") or item.get("first"),
                "last": item.get("data_end_utc") or item.get("actual_end_utc") or item.get("last"),
                "n": item.get("row_count") or item.get("actual_count") or item.get("n"),
                "fields": fields,
                "hash": item.get("sha256"),
                "status": "FROZEN",
                "class": klass,
                "license": license_,
                "derived_from": derived,
            }
        )
    failed = _load(os.path.join(root, "data", "market", "research_engine", "FAILED_ALPHA_DATABASE_V2.json"))
    n_free = sum(1 for r in rows if r.get("class") == "FREE")
    n_paid = sum(1 for r in rows if r.get("class") == "PAID")
    n_derived = sum(1 for r in rows if r.get("class") == "DERIVED")
    return {
        "catalog_id": "DATA_ASSET_CENSUS_V8",
        "mission": "V8_INFORMATION_FUSION",
        "NO_NEW_PURCHASE": True,
        "credits_remaining_usd_estimate": CREDIT_REMAINING_USD,
        "pack_e_billed_usd": BILLED_PACK_E_USD,
        "n_datasets": len(rows),
        "n_free": n_free,
        "n_paid": n_paid,
        "n_derived": n_derived,
        "n_failed_families": failed.get("n"),
        "datasets": rows,
        "FINAL_OOS_TOUCHED": False,
    }
