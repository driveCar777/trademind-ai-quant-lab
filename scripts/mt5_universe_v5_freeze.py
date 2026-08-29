#!/usr/bin/env python3
"""Freeze NEW D1 IDs for interesting Stage B symbols. Never write 20260825/20260828."""
from __future__ import print_function

import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.local_fs import force_project_temp

force_project_temp(ROOT)

from data_layer.config import load_data_sources
from data_layer.logging_util import DataLayerLogger
from data_layer.readonly_mt5 import import_readonly_mt5, initialize_readonly
from data_layer.storage import ensure_layout
from research_engine.alpha_program.evidence.extract import years_between
from research_engine.io_util import dump_json
from research_engine.mt5_history import FROZEN_TOKEN
from research_engine.mt5_history.acquire import fetch_bars, freeze_new, should_acquire
from research_protocol.bars import load_json

OUT = os.path.join(ROOT, "data", "market", "research_engine", "mt5_universe")
TARGETS = (
    ("COTTON", "COTTON#2"),
    ("COCOA", "COCOA"),
    ("COFFEE", "COFFEE_C"),
    ("CORN", "CORN"),
    ("SOYBEAN", "SOYBEAN"),
    ("SUGAR", "SUGAR#11"),
    ("WHEAT", "WHEAT"),
    ("EUROBUND", "EURO-BUND"),
    ("JAPANBOND", "JAPAN_BOND"),
    ("US2000", "US_2000"),
)


def disk_free_gb(letter):
    return float(shutil.disk_usage("%s:\\" % letter).free) / (1024.0 * 1024.0 * 1024.0)


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
    c_gb = disk_free_gb("C")
    d_gb = disk_free_gb("D")
    print("FREEZE_DISK", "C", round(c_gb, 2), "D", round(d_gb, 2), flush=True)
    if c_gb < 20.0:
        raise RuntimeError("C_FREE_BELOW_20GB")
    cfg = load_data_sources()
    ensure_layout(cfg["storage_root"])
    inv = inventory_from_disk(cfg["storage_root"])
    log_path = os.path.join(OUT, "V5_FREEZE.log")
    logger = DataLayerLogger(log_path)
    mt5, ver = import_readonly_mt5()
    path = cfg.get("terminal_path") or r"C:\Program Files\Ava Trade MT5 Terminal"
    try:
        initialize_readonly(mt5, cfg.get("terminal_path"))
    except Exception:
        initialize_readonly(mt5, path)
    acquired = []
    try:
        for logical, symbol in TARGETS:
            probe = {"calendar_span": 7.7, "status": "OK"}
            ok, reason = should_acquire(probe, logical, "D1", inv, equity_cfd=False)
            print("FREEZE_CHECK", logical, ok, reason, flush=True)
            if not ok and "already_have" in str(reason):
                continue
            mt5.symbol_select(symbol, True)
            bars, methods = fetch_bars(mt5, symbol, "D1", None, 80000)
            print("FREEZE_BARS", logical, len(bars or []), methods, flush=True)
            if not bars:
                acquired.append({"logical": logical, "ok": False, "error": "empty"})
                continue
            row = freeze_new(mt5, cfg, logical, symbol, "D1", bars, methods, logger, ver)
            acquired.append(row)
            print("FREEZE_ROW", row.get("dataset_id"), row.get("n"), row.get("years"), row.get("sha256"), flush=True)
            if "20260825" in str(row.get("dataset_id") or "") or "20260828" in str(row.get("dataset_id") or ""):
                raise RuntimeError("REFUSED_OVERWRITE_TOKEN")
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
    dump_json(os.path.join(OUT, "ACQUIRED_V5.json"), {"n": len(acquired), "rows": acquired})
    print("FREEZE_DONE", len(acquired), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
