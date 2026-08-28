#!/usr/bin/env python3
"""Freeze high-value MT5 symbols only. One-shot pulls. Never overwrite 20260825."""
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
from research_engine.io_util import dump_json
from research_engine.mt5_history.acquire import fetch_bars, freeze_new, should_acquire
from research_engine.mt5_history import FROZEN_TOKEN
from research_engine.alpha_program.evidence.extract import years_between
from research_protocol.bars import load_json


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

OUT = os.path.join(ROOT, "data", "market", "research_engine", "mt5_history")

# Logical, mt5 name, timeframes. Spec-backed names from inventory.
TARGETS = (
    ("SILVER", "SILVER", ("D1", "H1", "M15", "H4")),
    ("COPPER", "COPPER", ("D1", "H1", "M15")),
    ("PLATINUM", "PLATINUM", ("D1", "H1")),
    ("PALLADIUM", "PALLADIUM", ("D1", "H1")),
    ("BRENT", "BRENT_OIL", ("D1", "H1", "M15", "H4")),
    ("NATGAS", "NATURAL_GAS", ("D1", "H1", "H4")),
    ("HEATOIL", "HEATING_OIL", ("D1", "H1")),
    ("GASOLINE", "GASOLINE", ("D1", "H1")),
    ("GBPUSD", "GBPUSD", ("D1", "H1", "M15")),
    ("AUDUSD", "AUDUSD", ("D1", "H1")),
    ("USDCHF", "USDCHF", ("D1", "H1")),
    ("USDCAD", "USDCAD", ("D1", "H1")),
    ("NZDUSD", "NZDUSD", ("D1", "H1")),
    ("EURJPY", "EURJPY", ("D1", "H1")),
    ("EURGBP", "EURGBP", ("D1", "H1")),
    ("GBPJPY", "GBPJPY", ("D1", "H1")),
    ("US30", "US_30", ("D1", "H1")),
    ("US500", "US_500", ("D1", "H1")),
    ("USTECH100", "US_TECH100", ("D1", "H1")),
    ("GER40", "GERMANY_40", ("D1", "H1")),
    ("UK100", "UK_100", ("D1", "H1")),
    ("JPN225", "JAPAN_225", ("D1", "H1")),
    ("DXY", "DOLLAR_INDX", ("D1", "H1")),
    ("VIX", "VIX", ("D1", "H1")),
    ("GOLD", "GOLD", ("M15", "H4")),
    ("OIL", "CrudeOIL", ("M15", "H4")),
    ("EURUSD", "EURUSD", ("M15", "H4")),
    ("USDJPY", "USDJPY", ("M15", "H4")),
)

COUNT_HINT = {"D1": 20000, "H1": 100000, "H4": 50000, "M15": 100000}


def _tick_probe(mt5, symbol):
    from datetime import timedelta

    out = {"symbol": symbol, "status": "NOT_AVAILABLE", "note": "Broker ticks. Not an exchange order book."}
    try:
        tick = mt5.symbol_info_tick(symbol)
    except Exception as exc:
        out["tick_error"] = str(exc)
        tick = None
    if tick is not None:
        out["status"] = "LIVE_TICK"
        out["live_tick"] = {
            "bid": getattr(tick, "bid", None),
            "ask": getattr(tick, "ask", None),
            "last": getattr(tick, "last", None),
        }
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=2)
    flags = getattr(mt5, "COPY_TICKS_ALL", 1)
    hist = None
    try:
        hist = mt5.copy_ticks_range(symbol, start, end, flags)
    except Exception as exc:
        out["range_error"] = str(exc)
    if hist is None:
        try:
            hist = mt5.copy_ticks_from(symbol, start, 5000, flags)
        except Exception as exc:
            out["from_error"] = str(exc)
    if hist is not None and len(hist):
        out["status"] = "HIST_TICKS"
        out["tick_count_window"] = len(hist)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    cfg = load_data_sources()
    ensure_layout(cfg["storage_root"])
    logger = DataLayerLogger(os_path_join_logs(cfg["storage_root"]))
    disk = inventory_from_disk(cfg["storage_root"])
    print("ACQ_INIT", flush=True)
    mt5, ver = import_readonly_mt5()
    path = cfg.get("terminal_path") or r"C:\Program Files\Ava Trade MT5 Terminal"
    try:
        initialize_readonly(mt5, cfg.get("terminal_path"))
    except Exception:
        initialize_readonly(mt5, path)
    print("ACQ_READY", ver, flush=True)
    acquired = []
    capability = []
    try:
        for logical, symbol, tfs in TARGETS:
            mt5.symbol_select(symbol, True)
            time.sleep(0.05)
            for tf in tfs:
                try:
                    print("PULL", logical, symbol, tf, flush=True)
                    bars, methods = fetch_bars(mt5, symbol, tf, None, COUNT_HINT[tf])
                    if not bars:
                        capability.append({"logical": logical, "symbol": symbol, "timeframe": tf, "status": "NOT_AVAILABLE"})
                        print("EMPTY", logical, tf, flush=True)
                        continue
                    n = len(bars)
                    years = (
                        (bars[-1]["timestamp_unix"] - bars[0]["timestamp_unix"]) / (365.25 * 24 * 3600)
                    )
                    probe = {
                        "status": "OK",
                        "calendar_span": years,
                        "bar_count": n,
                        "first_bar": bars[0]["timestamp_utc"],
                        "last_bar": bars[-1]["timestamp_utc"],
                    }
                    capability.append(dict(probe, logical=logical, symbol=symbol, timeframe=tf))
                    print("GOT", logical, symbol, tf, n, round(years, 3), flush=True)
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
                    acquired.append({"ok": False, "logical": logical, "timeframe": tf, "error": str(exc)})
                    print("FAIL", logical, tf, exc, flush=True)
        dump_json(
            os.path.join(OUT, "ACQUIRED_V4.json"),
            {"utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "n": len(acquired), "rows": acquired},
        )
        dump_json(
            os.path.join(OUT, "MT5_HISTORY_CAPABILITY_V1.json"),
            {
                "capability_id": "MT5_HISTORY_CAPABILITY_V1",
                "mode": "priority_oneshot",
                "n": len(capability),
                "rows": capability,
                "FINAL_OOS_TOUCHED": False,
            },
        )
        ticks = [_tick_probe(mt5, "GOLD")]
        dump_json(
            os.path.join(OUT, "TICK_CAPABILITY_V1.json"),
            {
                "note": "Broker ticks only. Not an exchange order book.",
                "rows": ticks,
            },
        )
        print("TICK", ticks[0].get("status"), ticks[0].get("tick_count_window"), flush=True)
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
    print("ACQ_DONE", len(acquired), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
