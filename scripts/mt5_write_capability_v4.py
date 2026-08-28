#!/usr/bin/env python3
"""Write capability map from frozen manifests. Optional GOLD tick probe."""
from __future__ import print_function

import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from data_layer.config import load_data_sources
from data_layer.readonly_mt5 import import_readonly_mt5, initialize_readonly
from research_engine.io_util import dump_json
from research_protocol.bars import load_json

OUT = os.path.join(ROOT, "data", "market", "research_engine", "mt5_history")


def scan():
    cfg = load_data_sources()
    immutable = os.path.join(cfg["storage_root"], "immutable")
    rows = []
    for name in sorted(os.listdir(immutable)):
        man = os.path.join(immutable, name, "manifest.json")
        if not os.path.isfile(man):
            continue
        payload = load_json(man)
        rows.append(
            {
                "logical": payload.get("logical_symbol"),
                "mt5_symbol": payload.get("mt5_symbol"),
                "timeframe": payload.get("timeframe"),
                "dataset_id": payload.get("dataset_id"),
                "years": payload.get("calendar_span_years"),
                "n": payload.get("row_count") or payload.get("actual_count"),
                "sha256": payload.get("sha256"),
                "acquisition": payload.get("acquisition"),
                "frozen_20260825": "20260825-000001" in str(payload.get("dataset_id") or ""),
                "start": payload.get("actual_start_utc") or payload.get("data_start_utc"),
                "end": payload.get("actual_end_utc") or payload.get("data_end_utc"),
            }
        )
    return rows


def tick_gold():
    cfg = load_data_sources()
    mt5, ver = import_readonly_mt5()
    path = cfg.get("terminal_path") or r"C:\Program Files\Ava Trade MT5 Terminal"
    try:
        initialize_readonly(mt5, cfg.get("terminal_path"))
    except Exception:
        initialize_readonly(mt5, path)
    out = {"symbol": "GOLD", "package": ver, "note": "Broker ticks. Not an exchange order book."}
    try:
        tick = mt5.symbol_info_tick("GOLD")
        if tick is not None:
            out["status"] = "LIVE_TICK"
            out["bid"] = getattr(tick, "bid", None)
            out["ask"] = getattr(tick, "ask", None)
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=2)
        hist = mt5.copy_ticks_range("GOLD", start, end, mt5.COPY_TICKS_ALL)
        if hist is not None and len(hist):
            out["status"] = "HIST_TICKS"
            out["tick_count_window"] = len(hist)
    except Exception as exc:
        out["error"] = str(exc)
        out["status"] = out.get("status") or "NOT_AVAILABLE"
    try:
        mt5.shutdown()
    except Exception:
        pass
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = scan()
    v4 = [r for r in rows if r.get("acquisition") == "MT5_MAX_V4"]
    dump_json(
        os.path.join(OUT, "MT5_HISTORY_CAPABILITY_V1.json"),
        {
            "capability_id": "MT5_HISTORY_CAPABILITY_V1",
            "mode": "frozen_manifest_scan_plus_priority",
            "n": len(rows),
            "n_v4_new": len(v4),
            "rows": rows,
            "notes": {
                "vix_d1": "37 bars / 1.448y — below acquire threshold, not frozen",
                "uk100_d1": "999 bars / 3.97y — below acquire threshold, not frozen",
                "h1_m15": "first-pass copy_rates_from_pos(100000) empty; progressive backfill separate",
                "equity_cfd": "# prefix inventory only",
            },
            "FINAL_OOS_TOUCHED": False,
        },
    )
    dump_json(
        os.path.join(OUT, "ACQUIRED_V4.json"),
        {
            "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "n": len(v4),
            "rows": v4,
        },
    )
    ticks = tick_gold()
    dump_json(os.path.join(OUT, "TICK_CAPABILITY_V1.json"), {"rows": [ticks]})
    print("CAP_DONE", len(rows), "v4", len(v4), "tick", ticks.get("status"), ticks.get("tick_count_window"))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
