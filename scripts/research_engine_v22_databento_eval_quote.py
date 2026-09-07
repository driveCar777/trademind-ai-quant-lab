#!/usr/bin/env python3
"""Databento remaining-credit evaluation: metadata.get_cost only. Never downloads. Never prints the key."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.data_sources.databento import HistoricalClient  # noqa: E402
from research_engine.io_util import dump_json  # noqa: E402
from research_engine.local_fs import force_project_temp  # noqa: E402
from research_engine.v6_external.env import databento_api_key, has_databento_key  # noqa: E402

OUT = os.path.join(ROOT, "data", "market", "research_engine", "databento_eval_v22")
CREDIT_EST = 93.18
END = "2026-08-29"

# Broad CME futures universe: index, rates, FX, metals, energy, grains, livestock
CME_ROOTS = [
    "ES.FUT", "NQ.FUT", "YM.FUT", "RTY.FUT",
    "ZN.FUT", "ZB.FUT", "ZF.FUT", "ZT.FUT",
    "6E.FUT", "6J.FUT", "6B.FUT", "6A.FUT", "6C.FUT", "6S.FUT",
    "GC.FUT", "SI.FUT", "HG.FUT", "PL.FUT",
    "CL.FUT", "NG.FUT", "HO.FUT", "RB.FUT",
    "ZC.FUT", "ZS.FUT", "ZW.FUT", "ZM.FUT", "ZL.FUT",
    "LE.FUT", "HE.FUT", "GF.FUT",
]
CME_NO_GC_CL = [r for r in CME_ROOTS if r not in ("GC.FUT", "CL.FUT")]

MENU_FULL = [
    # id, dataset, schema, symbols, stype_in, start, purpose
    ("CME30_OHLCV_2010", "GLBX.MDP3", "ohlcv-1d", CME_ROOTS, "parent", "2010-06-06", "cross-sectional futures universe (30 roots) daily bars"),
    ("CME30_STATS_2010", "GLBX.MDP3", "statistics", CME_ROOTS, "parent", "2010-06-06", "official settle / OI / volume for curve + carry"),
    ("CME30_DEF_2010", "GLBX.MDP3", "definition", CME_ROOTS, "parent", "2010-06-06", "contract definitions (expiry) for roll/carry"),
    ("CME28_OHLCV_2010_noGCCL", "GLBX.MDP3", "ohlcv-1d", CME_NO_GC_CL, "parent", "2010-06-06", "same minus already-owned GC/CL"),
    ("CME28_STATS_2010_noGCCL", "GLBX.MDP3", "statistics", CME_NO_GC_CL, "parent", "2010-06-06", "same minus owned"),
    ("CME28_DEF_2010_noGCCL", "GLBX.MDP3", "definition", CME_NO_GC_CL, "parent", "2010-06-06", "same minus owned"),
    ("CME30_OHLCV_2015", "GLBX.MDP3", "ohlcv-1d", CME_ROOTS, "parent", "2015-01-02", "shorter window fallback"),
    ("CME30_STATS_2015", "GLBX.MDP3", "statistics", CME_ROOTS, "parent", "2015-01-02", "shorter window fallback"),
    ("CME30_DEF_2015", "GLBX.MDP3", "definition", CME_ROOTS, "parent", "2015-01-02", "shorter window fallback"),
    ("LO_1Y_MVDA_DEF", "GLBX.MDP3", "definition", ["LO.OPT"], "parent", "2025-08-29", "V8.4 preferred pack part 1"),
    ("LO_1Y_MVDA_OHLCV", "GLBX.MDP3", "ohlcv-1d", ["LO.OPT"], "parent", "2025-08-29", "V8.4 preferred pack part 2"),
    ("OG_1Y_MVDA_DEF", "GLBX.MDP3", "definition", ["OG.OPT"], "parent", "2025-08-29", "gold options"),
    ("OG_1Y_MVDA_OHLCV", "GLBX.MDP3", "ohlcv-1d", ["OG.OPT"], "parent", "2025-08-29", "gold options"),
    ("USEQ_SUMMARY_ALL", "EQUS.SUMMARY", "ohlcv-1d", ["ALL_SYMBOLS"], "raw_symbol", None, "US equities consolidated daily, all names"),
    ("USEQ_DBEQ_BASIC_ALL", "DBEQ.BASIC", "ohlcv-1d", ["ALL_SYMBOLS"], "raw_symbol", None, "US equities basic daily, all names"),
    ("USEQ_XNAS_ITCH_ALL", "XNAS.ITCH", "ohlcv-1d", ["ALL_SYMBOLS"], "raw_symbol", None, "Nasdaq daily, all names"),
    ("USEQ_XNAS_DEF", "XNAS.ITCH", "definition", ["ALL_SYMBOLS"], "raw_symbol", None, "Nasdaq definitions (listing status)"),
    ("USEQ_XNAS_ITCH_2018", "XNAS.ITCH", "ohlcv-1d", ["ALL_SYMBOLS"], "raw_symbol", "2018-05-01", "Nasdaq daily since 2018"),
    ("USEQ_SUMMARY_2018", "EQUS.SUMMARY", "ohlcv-1d", ["ALL_SYMBOLS"], "raw_symbol", "2018-05-01", "consolidated daily since 2018"),
    ("USEQ_SUMMARY_STATS", "EQUS.SUMMARY", "statistics", ["ALL_SYMBOLS"], "raw_symbol", None, "consolidated stats"),
    ("CME30_OHLCV_2012", "GLBX.MDP3", "ohlcv-1d", CME_ROOTS, "parent", "2012-01-03", "mid window"),
    ("CME30_STATS_2012", "GLBX.MDP3", "statistics", CME_ROOTS, "parent", "2012-01-03", "mid window"),
]
ONLY = set(sys.argv[1:])
MENU = [m for m in MENU_FULL if not ONLY or m[0] in ONLY]


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    force_project_temp()
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    print("KEY_PRESENT", has_databento_key())
    if not has_databento_key():
        return 2
    client = HistoricalClient(databento_api_key(), timeout=180)
    ranges = {}
    for ds in sorted(set(m[1] for m in MENU)):
        try:
            ranges[ds] = client.get_dataset_range(ds)
        except Exception as exc:
            ranges[ds] = {"error": str(exc)[:200]}
        print("RANGE", ds, json.dumps(ranges[ds])[:160])
    rows = []
    for mid, ds, schema, syms, stype, start, purpose in MENU:
        if start is None:
            r = ranges.get(ds) or {}
            start = (r.get("start") or "2018-01-01")[:10]
        row = {"id": mid, "dataset": ds, "schema": schema, "symbols": syms, "stype_in": stype,
               "start": start, "end": END, "purpose": purpose, "ok": False}
        try:
            row["cost_usd"] = float(client.get_cost(ds, schema, syms, start, END, stype))
            row["ok"] = True
        except Exception as exc:
            row["error"] = str(exc)[:240]
        try:
            row["billable_bytes"] = client.get_billable_size(ds, schema, syms, start, END, stype)
        except Exception:
            row["billable_bytes"] = None
        rows.append(row)
        print("QUOTE", mid, "ok" if row["ok"] else "FAIL", row.get("cost_usd"), row.get("billable_bytes"), row.get("error", "")[:100])
    payload = {"id": "DATABENTO_EVAL_QUOTE_V22", "utc": now(), "credit_estimate_usd": CREDIT_EST,
               "downloaded": False, "this_run_usd": 0, "dataset_ranges": ranges, "quotes": rows}
    dump_json(os.path.join(OUT, "QUOTE.json"), payload)
    print("wrote", os.path.join(OUT, "QUOTE.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
