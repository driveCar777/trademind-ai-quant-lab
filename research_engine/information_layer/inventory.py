"""Scan frozen manifests and Pack E state. Never open raw zst here."""
from __future__ import print_function

import json
import os

from research_engine.data_expansion.paths import repo_root
from research_engine.information_layer import BILLED_PACK_E_USD, CREDIT_REMAINING_USD


def _load(path):
    handle = open(path, encoding="utf-8")
    try:
        return json.load(handle)
    finally:
        handle.close()


def _walk_manifests(root):
    folder = os.path.join(root, "data", "market", "immutable")
    rows = []
    if not os.path.isdir(folder):
        return rows
    for name in sorted(os.listdir(folder)):
        man = os.path.join(folder, name, "manifest.json")
        if not os.path.isfile(man):
            continue
        item = _load(man)
        source = str(item.get("source") or "")
        if source == "databento" or str(item.get("dataset_id") or "").startswith("tm-fut-"):
            status = "PAID" if "CURVE" in name else "DERIVED"
            cost = "pack_e_shared"
            license_ = "databento_historical_internal_research"
        elif str(item.get("dataset_id") or "").startswith("tm-alt-"):
            status = "FREE"
            cost = 0
            license_ = "public_vendor_terms"
        else:
            status = "FREE"
            cost = 0
            license_ = "broker_terminal_internal"
        rows.append(
            {
                "dataset": item.get("dataset_id") or name,
                "source": source or item.get("vendor"),
                "schema": item.get("schema") or item.get("bars_format") or item.get("timeframe"),
                "history": {
                    "start": item.get("data_start_utc") or item.get("actual_start_utc") or item.get("first"),
                    "end": item.get("data_end_utc") or item.get("actual_end_utc") or item.get("last"),
                    "n": item.get("row_count") or item.get("n") or item.get("actual_count"),
                },
                "symbol": item.get("logical_symbol") or item.get("parents") or item.get("mt5_symbol"),
                "timestamp": item.get("retrieved_at_utc") or item.get("checked_at_utc"),
                "cost": cost,
                "license": license_,
                "hash": item.get("sha256"),
                "status": "FROZEN",
                "class": status,
            }
        )
    return rows


def _pack_e(root):
    path = os.path.join(
        root, "data", "market", "research_engine", "external", "V61_ACQUIRE_STATE.json"
    )
    if not os.path.isfile(path):
        return {"complete": False, "jobs": {}}
    state = _load(path)
    jobs = {}
    for schema, job in (state.get("jobs") or {}).items():
        jobs[schema] = {
            "id": job.get("id"),
            "state": job.get("state"),
            "cost_usd": job.get("cost_usd"),
            "progress": job.get("progress"),
        }
    files = state.get("files") or []
    return {
        "complete": all(str(j.get("state")) == "done" for j in jobs.values()) and len(files) >= 60,
        "n_files": len(files),
        "jobs": jobs,
        "billed_usd": BILLED_PACK_E_USD,
        "raw_gitignored": True,
        "re_download_forbidden": True,
    }


def build_inventory():
    root = repo_root()
    datasets = _walk_manifests(root)
    failed = _load(
        os.path.join(root, "data", "market", "research_engine", "FAILED_ALPHA_DATABASE_V2.json")
    )
    n_free = sum(1 for r in datasets if r.get("class") == "FREE")
    n_paid = sum(1 for r in datasets if r.get("class") == "PAID")
    n_derived = sum(1 for r in datasets if r.get("class") == "DERIVED")
    return {
        "mission": "V7_INFORMATION_FUSION",
        "NO_NEW_PURCHASE": True,
        "credits_remaining_usd_estimate": CREDIT_REMAINING_USD,
        "n_datasets": len(datasets),
        "n_free": n_free,
        "n_paid": n_paid,
        "n_derived": n_derived,
        "n_failed_families": failed.get("n"),
        "pack_e": _pack_e(root),
        "datasets": datasets,
        "FINAL_OOS_TOUCHED": False,
    }
