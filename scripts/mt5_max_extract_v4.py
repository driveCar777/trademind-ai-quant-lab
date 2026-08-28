#!/usr/bin/env python3
"""MT5 maximum symbol + history extract. Read-only. New dataset IDs only."""
from __future__ import print_function

import os
import sys
import time
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from data_layer.config import load_data_sources
from data_layer.fetch import _terminal_fields
from data_layer.logging_util import DataLayerLogger
from data_layer.readonly_mt5 import import_readonly_mt5, initialize_readonly
from data_layer.storage import ensure_layout
from data_layer.symbol_map import resolve_symbol
from research_engine.io_util import dump_json
from research_engine.mt5_history import FROZEN_TOKEN, TIMEFRAMES
from research_engine.mt5_history.acquire import (
    disk_best,
    fetch_bars,
    freeze_new,
    logical_from_symbol,
    should_acquire,
)
from research_engine.mt5_history.classify import classify, is_equity_cfd, is_priority, spec_dict
from research_engine.mt5_history.probe import merge_best, probe_from_pos, probe_range, unix_utc

OUT = os.path.join(ROOT, "data", "market", "research_engine", "mt5_history")
RANGE_START = datetime(1971, 1, 1, tzinfo=timezone.utc)
MAX_COUNT = {
    "MN1": 800,
    "W1": 5000,
    "D1": 20000,
    "H4": 50000,
    "H1": 100000,
    "M30": 80000,
    "M15": 100000,
    "M5": 20000,
    "M1": 10000,
}
ALL_SYMBOL_TFS = ("D1", "W1")
PRIORITY_TFS = ("M15", "M30", "H1", "H4", "D1", "W1", "MN1")
TINY_TFS = ("M1", "M5")
FX_DEEP = {
    "EURUSD",
    "USDJPY",
    "GBPUSD",
    "USDCHF",
    "AUDUSD",
    "USDCAD",
    "NZDUSD",
    "EURJPY",
    "EURGBP",
    "AUDJPY",
}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def inventory_from_disk(storage_root):
    rows = []
    immutable = os.path.join(storage_root, "immutable")
    if not os.path.isdir(immutable):
        return rows
    from research_protocol.bars import load_json
    from research_engine.alpha_program.evidence.extract import years_between

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
                "n": payload.get("row_count"),
                "frozen_20260825": FROZEN_TOKEN in str(payload.get("dataset_id") or ""),
            }
        )
    return rows


def terminal_payload(mt5, package_version):
    info = mt5.terminal_info()
    broker, terminal, path, terminal_version = _terminal_fields(mt5)
    row = {
        "utc": now(),
        "package_version": package_version,
        "broker": broker,
        "terminal": terminal,
        "terminal_path": path,
        "terminal_version": terminal_version,
        "maxbars": getattr(info, "maxbars", None) if info is not None else None,
        "connected": getattr(info, "connected", None) if info is not None else None,
        "tradeapi": getattr(info, "tradeapi", None) if info is not None else None,
    }
    if info is not None and hasattr(info, "_asdict"):
        raw = info._asdict()
        for key in ("maxbars", "connected", "community_account", "dlls_allowed", "trade_allowed"):
            if key in raw:
                row[key] = raw[key]
    return row


def known_map(mt5, cfg):
    mapping = {}
    for logical in ("GOLD", "EURUSD", "USDJPY", "OIL"):
        try:
            _logical, symbol = resolve_symbol(mt5, logical, cfg.get("symbol_aliases"))
            mapping[symbol] = logical
            print("KNOWN", logical, symbol, flush=True)
        except Exception as exc:
            print("KNOWN_FAIL", logical, exc, flush=True)
    return mapping


def collect_symbols(mt5):
    raw = mt5.symbols_get()
    if not raw:
        return []
    rows = []
    for item in raw:
        spec = spec_dict(item)
        category, reason = classify(spec)
        spec["category"] = category
        spec["classify_reason"] = reason
        spec["priority"] = is_priority(spec, category)
        spec["equity_cfd"] = is_equity_cfd(spec)
        rows.append(spec)
    rows.sort(key=lambda r: (r.get("category") or "", r.get("name") or ""))
    return rows


def probe_one(mt5, symbol, timeframe, do_range, steps=None):
    mt5.symbol_select(symbol, True)
    time.sleep(0.04)
    pos = probe_from_pos(mt5, symbol, timeframe, MAX_COUNT[timeframe], steps=steps)
    ranged = None
    if do_range and pos.get("status") == "OK":
        time.sleep(0.04)
        ranged = probe_range(mt5, symbol, timeframe, RANGE_START, datetime.now(timezone.utc))
    return merge_best(pos, ranged)


def tick_probe(mt5, symbol):
    out = {"symbol": symbol, "status": "NOT_AVAILABLE"}
    try:
        tick = mt5.symbol_info_tick(symbol)
    except Exception as exc:
        out["tick_error"] = str(exc)
        tick = None
    if tick is not None:
        out["live_tick"] = {
            "time": unix_utc(getattr(tick, "time", None)),
            "bid": getattr(tick, "bid", None),
            "ask": getattr(tick, "ask", None),
            "last": getattr(tick, "last", None),
            "volume": getattr(tick, "volume", None),
            "flags": getattr(tick, "flags", None),
        }
        out["status"] = "LIVE_TICK"
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
            out["from_method"] = "copy_ticks_from"
        except Exception as exc:
            out["from_error"] = str(exc)
    if hist is not None and len(hist):
        out["status"] = "HIST_TICKS"
        out["tick_count_window"] = len(hist)
        out["first_tick"] = unix_utc(int(hist[0]["time"]))
        out["last_tick"] = unix_utc(int(hist[-1]["time"]))
        names = hist.dtype.names if hasattr(hist, "dtype") else ()
        out["fields"] = list(names)
        out["note"] = "Broker ticks. Not an exchange order book."
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    cfg = load_data_sources()
    ensure_layout(cfg["storage_root"])
    logger = DataLayerLogger(os.path.join(cfg["storage_root"], "logs"))
    disk = inventory_from_disk(cfg["storage_root"])
    mt5 = None
    ver = None
    try:
        print("V4_INIT", flush=True)
        mt5, ver = import_readonly_mt5()
        path = cfg.get("terminal_path") or r"C:\Program Files\Ava Trade MT5 Terminal"
        try:
            initialize_readonly(mt5, cfg.get("terminal_path"))
        except Exception:
            initialize_readonly(mt5, path)
        print("V4_READY", ver, flush=True)
    except Exception as exc:
        dump_json(os.path.join(OUT, "BLOCKED.json"), {"utc": now(), "error": str(exc), "status": "HUMAN_REQUIRED"})
        print("HUMAN_REQUIRED", exc, flush=True)
        return 2

    try:
        term = terminal_payload(mt5, ver)
        dump_json(os.path.join(OUT, "TERMINAL.json"), term)
        print("MAXBARS", term.get("maxbars"), "PATH", term.get("terminal_path"), flush=True)

        known = known_map(mt5, cfg)
        symbols = collect_symbols(mt5)
        counts = {}
        for row in symbols:
            counts[row["category"]] = counts.get(row["category"], 0) + 1
        inventory = {
            "inventory_id": "MT5_SYMBOL_INVENTORY_V1",
            "utc": now(),
            "n": len(symbols),
            "category_counts": counts,
            "known_map": known,
            "FINAL_OOS_TOUCHED": False,
            "order_send": False,
            "symbols": symbols,
        }
        dump_json(os.path.join(OUT, "MT5_SYMBOL_INVENTORY_V1.json"), inventory)
        print("SYMBOLS", len(symbols), counts, flush=True)

        capability = []
        acquire_plan = []
        for spec in symbols:
            name = spec.get("name")
            if not name:
                continue
            if spec.get("equity_cfd"):
                tfs = ("D1",)
            else:
                tfs = list(ALL_SYMBOL_TFS)
                if spec.get("priority"):
                    if spec.get("category") == "FX" and name not in FX_DEEP:
                        tfs = ("D1", "H1", "W1")
                    else:
                        tfs = list(PRIORITY_TFS)
                        if name in known:
                            tfs = list(PRIORITY_TFS) + list(TINY_TFS)
            for tf in tfs:
                do_range = spec.get("priority") and tf in ("D1", "H1", "H4", "M15", "W1")
                steps = None
                if spec.get("equity_cfd"):
                    steps = (10000,)
                    do_range = False
                elif not spec.get("priority") and tf in ("D1", "W1", "MN1"):
                    steps = (10000, 20000)
                try:
                    row = probe_one(mt5, name, tf, do_range, steps=steps)
                except Exception as exc:
                    row = {"status": "NOT_AVAILABLE", "reason": str(exc), "symbol": name, "timeframe": tf}
                row["category"] = spec.get("category")
                row["priority"] = spec.get("priority")
                logical = logical_from_symbol(name, known)
                row["logical"] = logical
                capability.append(row)
                print(
                    "PROBE",
                    logical,
                    name,
                    tf,
                    row.get("status"),
                    row.get("bar_count"),
                    row.get("calendar_span"),
                    flush=True,
                )
                ok, why = should_acquire(row, logical, tf, disk, spec.get("equity_cfd"))
                if ok:
                    acquire_plan.append(
                        {
                            "logical": logical,
                            "symbol": name,
                            "timeframe": tf,
                            "years": row.get("calendar_span"),
                            "bars": row.get("bar_count"),
                            "first": row.get("first_bar"),
                            "why": why,
                        }
                    )

        cap_path = os.path.join(OUT, "MT5_HISTORY_CAPABILITY_V1.json")
        dump_json(
            cap_path,
            {
                "capability_id": "MT5_HISTORY_CAPABILITY_V1",
                "utc": now(),
                "n": len(capability),
                "acquire_plan": acquire_plan,
                "FINAL_OOS_TOUCHED": False,
                "rows": capability,
            },
        )
        print("PLAN", len(acquire_plan), flush=True)

        tick_symbol = None
        for key, logical in ((k, v) for k, v in known.items() if v == "GOLD"):
            tick_symbol = key
            break
        if tick_symbol is None and symbols:
            tick_symbol = symbols[0].get("name")
        ticks = tick_probe(mt5, tick_symbol) if tick_symbol else {"status": "NOT_AVAILABLE"}
        dump_json(os.path.join(OUT, "TICK_DATA_CAPABILITY.json"), {"utc": now(), "probe": ticks, "not_order_book": True})
        print("TICKS", ticks.get("status"), ticks.get("tick_count_window"), flush=True)

        acquired = []
        for item in acquire_plan:
            try:
                time.sleep(0.2)
                bars, methods = fetch_bars(
                    mt5,
                    item["symbol"],
                    item["timeframe"],
                    None,
                    item.get("bars") or MAX_COUNT[item["timeframe"]],
                )
                # recover first unix from bars
                first_unix = bars[0]["timestamp_unix"] if bars else None
                if first_unix and (not bars or len(bars) < int(item.get("bars") or 0) * 0.9):
                    bars, methods = fetch_bars(
                        mt5,
                        item["symbol"],
                        item["timeframe"],
                        first_unix,
                        MAX_COUNT[item["timeframe"]],
                    )
                row = freeze_new(
                    mt5,
                    cfg,
                    item["logical"],
                    item["symbol"],
                    item["timeframe"],
                    bars,
                    methods,
                    logger,
                    ver,
                )
                acquired.append(row)
                if row.get("ok"):
                    disk.append(
                        {
                            "logical": row["logical"],
                            "timeframe": row["timeframe"],
                            "dataset_id": row["dataset_id"],
                            "years": row["years"],
                            "frozen_20260825": False,
                        }
                    )
                print("ACQ", row.get("dataset_id") or item, row.get("years") or row.get("error"), flush=True)
            except Exception as exc:
                acquired.append({"ok": False, "item": item, "error": str(exc)})
                print("ACQ_FAIL", item, exc, flush=True)
        dump_json(
            os.path.join(OUT, "ACQUIRED_V4.json"),
            {"utc": now(), "n": len(acquired), "rows": acquired, "FINAL_OOS_TOUCHED": False},
        )
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
    print("V4_EXTRACT_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
