#!/usr/bin/env python3
"""Second-pass H1/M15/H4 freeze. Progressive from_pos because 100k can return None."""
from __future__ import print_function

import os
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from data_layer.config import load_data_sources
from data_layer.fetch import os_path_join_logs
from data_layer.logging_util import DataLayerLogger
from data_layer.readonly_mt5 import import_readonly_mt5, initialize_readonly
from data_layer.storage import ensure_layout
from research_engine.alpha_program.evidence.extract import years_between
from research_engine.io_util import dump_json
from research_engine.mt5_history import FROZEN_TOKEN
from research_engine.mt5_history.acquire import fetch_bars, freeze_new, should_acquire
from research_protocol.bars import load_json

OUT = os.path.join(ROOT, "data", "market", "research_engine", "mt5_history")

TARGETS = (
    ("SILVER", "SILVER", ("H1", "M15")),
    ("COPPER", "COPPER", ("H1", "M15")),
    ("PLATINUM", "PLATINUM", ("H1",)),
    ("PALLADIUM", "PALLADIUM", ("H1",)),
    ("BRENT", "BRENT_OIL", ("H1", "M15")),
    ("NATGAS", "NATURAL_GAS", ("H1",)),
    ("HEATOIL", "HEATING_OIL", ("H1",)),
    ("GASOLINE", "GASOLINE", ("H1",)),
    ("GBPUSD", "GBPUSD", ("H1", "M15")),
    ("AUDUSD", "AUDUSD", ("H1",)),
    ("USDCHF", "USDCHF", ("H1",)),
    ("USDCAD", "USDCAD", ("H1",)),
    ("NZDUSD", "NZDUSD", ("H1",)),
    ("EURJPY", "EURJPY", ("H1",)),
    ("EURGBP", "EURGBP", ("H1",)),
    ("GBPJPY", "GBPJPY", ("H1",)),
    ("US30", "US_30", ("H1",)),
    ("US500", "US_500", ("H1",)),
    ("USTECH100", "US_TECH100", ("H1",)),
    ("GER40", "GERMANY_40", ("H1",)),
    ("UK100", "UK_100", ("H1",)),
    ("JPN225", "JAPAN_225", ("H1",)),
    ("DXY", "DOLLAR_INDX", ("H1",)),
    ("VIX", "VIX", ("H1",)),
    ("GOLD", "GOLD", ("M15", "H4")),
    ("OIL", "CrudeOIL", ("M15", "H4")),
    ("EURUSD", "EURUSD", ("M15", "H4")),
    ("USDJPY", "USDJPY", ("M15", "H4")),
)

HINT = {"H1": 80000, "M15": 80000, "H4": 50000}


def inventory_from_disk(storage_root):
    rows = []
    immutable = os.path.join(storage_root, "immutable")
    if not os.path.isdir(immutable):
        return rows
    for name in sorted(os.listdir(immutable)):
        man = os.path.join(immutable, name, "manifest.json")
        if not os.path.isfile(man):
            continue
        payload = load_json(man)
        start = payload.get("actual_start_utc") or payload.get("data_start_utc")
        end = payload.get("actual_end_utc") or payload.get("data_end_utc")
        rows.append(
            {
                "logical": payload.get("logical_symbol"),
                "timeframe": payload.get("timeframe"),
                "dataset_id": payload.get("dataset_id"),
                "years": years_between(start, end),
                "frozen_20260825": FROZEN_TOKEN in str(payload.get("dataset_id") or ""),
            }
        )
    return rows


def main():
    cfg = load_data_sources()
    ensure_layout(cfg["storage_root"])
    logger = DataLayerLogger(os_path_join_logs(cfg["storage_root"]))
    disk = inventory_from_disk(cfg["storage_root"])
    print("BF_INIT", flush=True)
    mt5, ver = import_readonly_mt5()
    path = cfg.get("terminal_path") or r"C:\Program Files\Ava Trade MT5 Terminal"
    try:
        initialize_readonly(mt5, cfg.get("terminal_path"))
    except Exception:
        initialize_readonly(mt5, path)
    print("BF_READY", ver, flush=True)
    acquired = []
    try:
        for logical, symbol, tfs in TARGETS:
            mt5.symbol_select(symbol, True)
            time.sleep(0.05)
            for tf in tfs:
                print("PULL", logical, tf, flush=True)
                try:
                    bars, methods = fetch_bars(mt5, symbol, tf, None, HINT[tf])
                    if not bars:
                        print("EMPTY", logical, tf, flush=True)
                        continue
                    years = (bars[-1]["timestamp_unix"] - bars[0]["timestamp_unix"]) / (365.25 * 24 * 3600)
                    probe = {"status": "OK", "calendar_span": years, "bar_count": len(bars)}
                    print("GOT", logical, tf, len(bars), round(years, 3), methods, flush=True)
                    ok, why = should_acquire(probe, logical, tf, disk, False)
                    if not ok:
                        print("SKIP", logical, tf, why, flush=True)
                        continue
                    row = freeze_new(mt5, cfg, logical, symbol, tf, bars, methods, logger, ver)
                    acquired.append(row)
                    if row.get("ok"):
                        disk.append(
                            {
                                "logical": logical,
                                "timeframe": tf,
                                "dataset_id": row["dataset_id"],
                                "years": row["years"],
                                "frozen_20260825": False,
                            }
                        )
                    print("FROZE", row.get("dataset_id"), row.get("years") or row.get("error"), flush=True)
                except Exception as exc:
                    print("FAIL", logical, tf, exc, flush=True)
        dump_json(
            os.path.join(OUT, "BACKFILL_INTRADAY_V4.json"),
            {"utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "n": len(acquired), "rows": acquired},
        )
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
    print("BF_DONE", len(acquired), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
