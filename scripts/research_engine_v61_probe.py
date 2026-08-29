#!/usr/bin/env python3
"""V6.1 secret check + metadata.get_cost. Never prints the key."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.data_expansion.paths import repo_root
from research_engine.data_sources import ENV_DATABENTO
from research_engine.data_sources.databento import DATASET, HistoricalClient
from research_engine.local_fs import force_project_temp
from research_engine.v6_external.env import has_databento_key, databento_api_key


START = "2010-06-06"
END = "2026-08-29"
CREDIT_USD = 125.0


def env_exists():
    return os.path.isfile(os.path.join(repo_root(), ".env"))


def write_json(path, payload):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(path, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()


def quote_one(client, schema, symbols):
    cost = client.get_cost(DATASET, schema, symbols, START, END, "parent")
    size = None
    try:
        size = client.get_billable_size(DATASET, schema, symbols, START, END, "parent")
    except Exception:
        size = None
    return {"schema": schema, "symbols": list(symbols), "cost_usd": cost, "billable_size": size}


def main():
    force_project_temp()
    print("ENV_EXISTS =", "true" if env_exists() else "false")
    print("KEY_NAME =", ENV_DATABENTO)
    present = has_databento_key()
    print("KEY_PRESENT =", "true" if present else "false")
    if not present:
        print("STOP = CREDENTIAL_REQUIRED")
        return 2
    key = databento_api_key()
    if ENV_DATABENTO.lower() in key.lower() or len(key) < 8:
        print("STOP = CREDENTIAL_INVALID_SHAPE")
        return 2
    client = HistoricalClient(key, timeout=180)
    rows = []
    for schema, symbols in (
        ("ohlcv-1d", ["GC.FUT"]),
        ("ohlcv-1d", ["CL.FUT"]),
        ("ohlcv-1d", ["GC.FUT", "CL.FUT"]),
        ("definition", ["GC.FUT", "CL.FUT"]),
        ("statistics", ["GC.FUT", "CL.FUT"]),
        ("definition", ["GC.FUT"]),
        ("definition", ["CL.FUT"]),
        ("statistics", ["GC.FUT"]),
        ("statistics", ["CL.FUT"]),
    ):
        row = quote_one(client, schema, symbols)
        rows.append(row)
        print(
            "COST",
            row["schema"],
            "+".join(row["symbols"]),
            "%.6f" % row["cost_usd"],
            "size",
            row["billable_size"],
        )
    pack_e = 0.0
    for row in rows:
        if row["schema"] in ("ohlcv-1d", "definition", "statistics") and row["symbols"] == [
            "GC.FUT",
            "CL.FUT",
        ]:
            pack_e += float(row["cost_usd"])
    dataset_range = None
    try:
        dataset_range = client.get_dataset_range(DATASET)
    except Exception as exc:
        dataset_range = {"error": type(exc).__name__}
    payload = {
        "probe_id": "V6.1_COST_PROBE",
        "checked_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataset": DATASET,
        "start": START,
        "end": END,
        "stype_in": "parent",
        "credit_cap_usd": CREDIT_USD,
        "credit_balance_usd": "UNKNOWN_API",
        "credit_balance_note": "Databento historical API does not expose remaining credits. Cap is the $125 new-user credit rule.",
        "quotes": rows,
        "pack_e_usd": pack_e,
        "within_credits": pack_e <= CREDIT_USD,
        "dataset_range": dataset_range,
        "KEY_PRESENT": True,
        "FINAL_OOS_TOUCHED": False,
    }
    dest = os.path.join(
        repo_root(),
        "data",
        "market",
        "research_engine",
        "external",
        "V61_COST_PROBE.json",
    )
    write_json(dest, payload)
    print("PACK_E_USD = %.6f" % pack_e)
    print("CREDIT_CAP_USD = %.2f" % CREDIT_USD)
    print("CREDIT_BALANCE_USD = UNKNOWN_API")
    print("WITHIN_CREDITS =", "true" if payload["within_credits"] else "false")
    if not payload["within_credits"]:
        print("STOP = BUDGET_BLOCKED")
        return 3
    print("GATE_A = PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
