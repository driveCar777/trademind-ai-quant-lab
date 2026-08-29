#!/usr/bin/env python3
"""V8 options metadata + get_cost. Never prints the key. Never downloads."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.data_sources.databento import HistoricalClient
from research_engine.io_util import dump_json
from research_engine.local_fs import force_project_temp
from research_engine.v6_external.env import databento_api_key, has_databento_key


DATASET = "GLBX.MDP3"
AUTO_PURCHASE_MAX = 30.0
CREDIT_FLOOR = 60.0
CREDIT_REMAINING_EST = 93.18
OUT = os.path.join(ROOT, "data", "market", "research_engine", "v8_fusion")
FORBIDDEN = ("mbo", "mbp-10", "mbp-1", "tbbo", "trades", "ohlcv-1s", "ohlcv-1m", "ohlcv-1h")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def quote_one(client, schema, symbols, start, end, stype_in="parent"):
    row = {
        "dataset": DATASET,
        "schema": schema,
        "symbols": list(symbols),
        "stype_in": stype_in,
        "start": start,
        "end": end,
        "ok": False,
    }
    try:
        row["cost_usd"] = float(client.get_cost(DATASET, schema, symbols, start, end, stype_in))
        row["ok"] = True
    except Exception as exc:
        row["error"] = type(exc).__name__
        row["error_detail"] = str(exc)[:240]
    try:
        row["billable_size"] = client.get_billable_size(DATASET, schema, symbols, start, end, stype_in)
    except Exception:
        row["billable_size"] = None
    return row


def main():
    force_project_temp()
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    print("V8_OPTIONS_QUOTE", now())
    print("KEY_PRESENT", "true" if has_databento_key() else "false")
    if not has_databento_key():
        payload = {
            "catalog_id": "OPTIONS_QUOTE_V8",
            "utc": now(),
            "KEY_PRESENT": False,
            "STOP": "CREDENTIAL_REQUIRED",
            "downloaded": False,
            "this_mission_usd": 0,
        }
        dump_json(os.path.join(OUT, "OPTIONS_QUOTE_V8.json"), payload)
        print("STOP CREDENTIAL_REQUIRED")
        return 2
    key = databento_api_key()
    if "DATABENTO" in key.upper() and len(key) < 12:
        print("STOP CREDENTIAL_INVALID_SHAPE")
        return 2
    client = HistoricalClient(key, timeout=180)
    coverage = None
    try:
        coverage = client.get_dataset_range(DATASET)
    except Exception as exc:
        coverage = {"error": str(exc)[:240]}
    windows = (
        ("MVD_3Y", "2023-08-30", "2026-08-29"),
        ("RESEARCH_8Y", "2018-01-02", "2026-08-29"),
    )
    parents = (
        ("GC.OPT",),
        ("CL.OPT",),
        ("OG.OPT",),
        ("LO.OPT",),
        ("GC.OPT", "CL.OPT"),
        ("OG.OPT", "LO.OPT"),
    )
    schemas = ("definition", "statistics", "ohlcv-1d")
    quotes = []
    for label, start, end in windows:
        for schema in schemas:
            if schema in FORBIDDEN:
                continue
            for symbols in parents:
                row = quote_one(client, schema, symbols, start, end, "parent")
                row["window"] = label
                quotes.append(row)
                print(
                    "QUOTE",
                    label,
                    schema,
                    ",".join(symbols),
                    "ok" if row.get("ok") else "FAIL",
                    row.get("cost_usd") if row.get("ok") else row.get("error_detail", "")[:80],
                )
    ok_rows = [r for r in quotes if r.get("ok")]
    cheapest = None
    if ok_rows:
        cheapest = min(ok_rows, key=lambda r: r.get("cost_usd") if r.get("cost_usd") is not None else 1e18)
    mvd_candidates = [
        r
        for r in ok_rows
        if r.get("window") == "MVD_3Y" and r.get("schema") in ("definition", "statistics")
    ]
    mvd_sum = None
    if mvd_candidates:
        # cheapest definition + cheapest statistics for a working parent pair
        by_key = {}
        for row in mvd_candidates:
            key = (tuple(row["symbols"]), row["schema"])
            prev = by_key.get(key)
            if prev is None or row["cost_usd"] < prev["cost_usd"]:
                by_key[key] = row
        pair_cost = {}
        for (symbols, schema), row in by_key.items():
            pair_cost.setdefault(symbols, {})[schema] = row
        best = None
        for symbols, parts in pair_cost.items():
            if "definition" in parts and "statistics" in parts:
                total = parts["definition"]["cost_usd"] + parts["statistics"]["cost_usd"]
                item = {"symbols": list(symbols), "definition": parts["definition"], "statistics": parts["statistics"], "total_usd": total}
                if best is None or total < best["total_usd"]:
                    best = item
        mvd_sum = best
    auto = False
    stop = "HUMAN_REQUIRED"
    if not ok_rows:
        stop = "OPTIONS_QUOTE_BLOCKED"
    elif mvd_sum and mvd_sum["total_usd"] <= AUTO_PURCHASE_MAX:
        auto = True
        stop = "AUTO_PURCHASE_ALLOWED"
    elif cheapest and cheapest.get("cost_usd", 999) > AUTO_PURCHASE_MAX:
        stop = "HUMAN_REQUIRED"
    payload = {
        "catalog_id": "OPTIONS_QUOTE_V8",
        "utc": now(),
        "KEY_PRESENT": True,
        "dataset": DATASET,
        "coverage": coverage,
        "downloaded": False,
        "this_mission_usd": 0,
        "credit_remaining_usd_estimate": CREDIT_REMAINING_EST,
        "credit_floor_usd": CREDIT_FLOOR,
        "auto_purchase_max_usd": AUTO_PURCHASE_MAX,
        "quotes": quotes,
        "n_ok": len(ok_rows),
        "cheapest": cheapest,
        "mvd_definition_plus_statistics": mvd_sum,
        "NEW_MECHANISM": True,
        "GVZ_OVX_NOTE": "Public IV index != GC/CL option surface.",
        "auto_purchase_allowed": auto,
        "STOP": stop,
        "do_not": [
            "timeseries.get_range",
            "batch.submit_job",
            "ohlcv-1s/1m/1h",
            "mbo/mbp/tbbo/trades",
            "$199/month Standard",
            "print API key",
            "ship key to Xavier",
        ],
    }
    dump_json(os.path.join(OUT, "OPTIONS_QUOTE_V8.json"), payload)
    print("STOP", stop, "ok", len(ok_rows), "mvd", None if mvd_sum is None else mvd_sum.get("total_usd"))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
