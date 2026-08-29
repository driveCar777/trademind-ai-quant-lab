#!/usr/bin/env python3
"""Resume Pack E quotes one request at a time. Never prints the key."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.data_sources.databento import DATASET, HistoricalClient
from research_engine.local_fs import force_project_temp
from research_engine.v6_external.env import databento_api_key, has_databento_key


START = "2010-06-06"
END = "2026-08-29"
CREDIT = 125.0
OUT = os.path.join(
    ROOT, "data", "market", "research_engine", "external", "V61_COST_PROBE.json"
)

JOBS = (
    ("ohlcv-1d", ("GC.FUT",)),
    ("ohlcv-1d", ("CL.FUT",)),
    ("definition", ("GC.FUT",)),
    ("definition", ("CL.FUT",)),
    ("statistics", ("GC.FUT",)),
    ("statistics", ("CL.FUT",)),
)


def load_existing():
    if not os.path.isfile(OUT):
        return []
    handle = open(OUT, encoding="utf-8")
    try:
        payload = json.load(handle)
    finally:
        handle.close()
    return list(payload.get("quotes") or [])


def already(quotes, schema, symbols):
    want = list(symbols)
    for row in quotes:
        if row.get("schema") == schema and list(row.get("symbols") or []) == want:
            return True
    return False


def main():
    force_project_temp()
    print("KEY_PRESENT =", "true" if has_databento_key() else "false")
    client = HistoricalClient(databento_api_key(), timeout=180)
    quotes = load_existing()
    for schema, symbols in JOBS:
        if already(quotes, schema, symbols):
            print("SKIP", schema, "+".join(symbols))
            continue
        cost = client.get_cost(DATASET, schema, symbols, START, END, "parent")
        try:
            size = client.get_billable_size(
                DATASET, schema, symbols, START, END, "parent"
            )
        except Exception:
            size = None
        row = {
            "schema": schema,
            "symbols": list(symbols),
            "cost_usd": float(cost),
            "billable_size": size,
        }
        quotes.append(row)
        print("COST", schema, "+".join(symbols), "%.6f" % cost, "size", size)
    by_schema = {}
    for row in quotes:
        if len(row.get("symbols") or []) != 1:
            continue
        by_schema.setdefault(row["schema"], 0.0)
        by_schema[row["schema"]] += float(row["cost_usd"])
    pack_e = (
        float(by_schema.get("ohlcv-1d") or 0)
        + float(by_schema.get("definition") or 0)
        + float(by_schema.get("statistics") or 0)
    )
    have = set(by_schema)
    complete = have == set(["ohlcv-1d", "definition", "statistics"])
    payload = {
        "probe_id": "V6.1_COST_PROBE",
        "checked_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataset": DATASET,
        "start": START,
        "end": END,
        "stype_in": "parent",
        "method": "sum of single-root quotes (same Pack E fields; not a reduced pack)",
        "credit_cap_usd": CREDIT,
        "credit_balance_usd": "UNKNOWN_API",
        "quotes": quotes,
        "pack_e_usd": pack_e,
        "quote_complete": complete,
        "within_credits": pack_e <= CREDIT if complete else None,
        "KEY_PRESENT": True,
        "FINAL_OOS_TOUCHED": False,
    }
    parent = os.path.dirname(OUT)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(OUT, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    print("PACK_E_USD = %.6f" % pack_e)
    print("QUOTE_COMPLETE =", "true" if complete else "false")
    if complete:
        print("WITHIN_CREDITS =", "true" if pack_e <= CREDIT else "false")
        return 0 if pack_e <= CREDIT else 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
