#!/usr/bin/env python3
"""Live MT5 universe V5. Progressive probe. Equity CFDs inventory-only. No 20260825 overwrite."""
from __future__ import print_function

import os
import sys
import time
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from data_layer.config import load_data_sources
from data_layer.readonly_mt5 import import_readonly_mt5, initialize_readonly
from research_engine.alpha_program.evidence.extract import years_between
from research_engine.io_util import dump_json
from research_engine.mt5_history import FROZEN_TOKEN
from research_engine.mt5_history.classify import classify, is_equity_cfd, spec_dict
from research_engine.mt5_history.probe import probe_from_pos, unix_utc
from research_engine.mt5_universe import CLASS_MAP, PROBE_STEPS, TIMEFRAMES
from research_engine.mt5_universe.qualify import coverage
from research_protocol.bars import load_json

OUT = os.path.join(ROOT, "data", "market", "research_engine", "mt5_universe")
CORE_M1 = ("GOLD", "SILVER", "EURUSD", "GBPUSD", "US_500", "CrudeOIL")
DEEP_TF = ("M15", "M30", "H1", "H4", "D1", "W1")
META_FIELDS = (
    "name",
    "description",
    "path",
    "currency_base",
    "currency_profit",
    "digits",
    "point",
    "trade_tick_size",
    "trade_tick_value",
    "trade_contract_size",
    "swap_long",
    "swap_short",
    "trade_mode",
)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def disk_inventory(storage_root):
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
                "mt5_symbol": payload.get("mt5_symbol"),
                "timeframe": payload.get("timeframe"),
                "dataset_id": payload.get("dataset_id"),
                "years": years_between(start, end),
                "n": payload.get("row_count") or payload.get("actual_count"),
                "sha256": payload.get("sha256"),
                "frozen_20260825": FROZEN_TOKEN in str(payload.get("dataset_id") or ""),
                "start": start,
                "end": end,
            }
        )
    return rows


def pick_meta(spec):
    out = {}
    for key in META_FIELDS:
        out[key] = spec.get(key)
    return out


def probe_tf(mt5, symbol, timeframe, steps):
    row = probe_from_pos(mt5, symbol, timeframe, 250000, sleep_s=0.02, steps=steps)
    if row is None:
        return {"status": "NOT_AVAILABLE", "timeframe": timeframe}
    years = float(row.get("calendar_span") or 0)
    status = row.get("status") or "NOT_AVAILABLE"
    if status == "OK":
        label = coverage(timeframe, years)
    else:
        label = "NOT_AVAILABLE"
    row["coverage"] = label
    row["qualification"] = label
    return row


def tick_probe(mt5, symbol):
    out = {"symbol": symbol, "status": "NOT_AVAILABLE", "note": "Broker ticks. Not an exchange order book."}
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is not None:
            out["status"] = "LIVE_TICK"
            out["bid"] = getattr(tick, "bid", None)
            out["ask"] = getattr(tick, "ask", None)
    except Exception as exc:
        out["tick_error"] = str(exc)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=2)
    hist = None
    try:
        hist = mt5.copy_ticks_range(symbol, start, end, mt5.COPY_TICKS_ALL)
    except Exception as exc:
        out["range_error"] = str(exc)
    if hist is None:
        try:
            hist = mt5.copy_ticks_from(symbol, start, 5000, mt5.COPY_TICKS_ALL)
            out["from_method"] = "copy_ticks_from"
        except Exception as exc:
            out["from_error"] = str(exc)
    if hist is not None and len(hist):
        out["status"] = "HIST_TICKS"
        out["count"] = int(len(hist))
        out["first_tick"] = unix_utc(int(hist[0]["time"]))
        out["last_tick"] = unix_utc(int(hist[-1]["time"]))
    elif out.get("status") == "LIVE_TICK":
        out["history"] = "BROKER_LIMITATION"
    else:
        out["history"] = "BROKER_LIMITATION"
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    cfg = load_data_sources()
    disk = disk_inventory(cfg["storage_root"])
    print("V5_UNI_INIT", now(), flush=True)
    mt5, ver = import_readonly_mt5()
    path = cfg.get("terminal_path") or r"C:\Program Files\Ava Trade MT5 Terminal"
    try:
        initialize_readonly(mt5, cfg.get("terminal_path"))
    except Exception:
        initialize_readonly(mt5, path)
    info = mt5.terminal_info()
    maxbars = getattr(info, "maxbars", None) if info is not None else None
    print("V5_UNI_READY", ver, "MAXBARS", maxbars, flush=True)
    symbols = mt5.symbols_get() or []
    assets = []
    ticks = []
    try:
        for item in symbols:
            spec = spec_dict(item)
            name = spec.get("name") or getattr(item, "name", None)
            category, reason = classify(spec)
            klass = CLASS_MAP.get(category, "OTHER")
            equity = is_equity_cfd(spec)
            mt5.symbol_select(name, True)
            history = {}
            if equity:
                history["D1"] = probe_tf(mt5, name, "D1", (10000,))
            else:
                history["D1"] = probe_tf(mt5, name, "D1", (2000, 10000, 20000, 80000))
                deep = klass in ("METAL", "ENERGY", "FX", "INDEX", "CRYPTO", "RATE")
                if deep:
                    for tf in DEEP_TF:
                        if tf == "D1":
                            continue
                        history[tf] = probe_tf(mt5, name, tf, (2000, 10000, 50000, 80000))
                    if name in CORE_M1:
                        history["M1"] = probe_tf(mt5, name, "M1", (2000, 10000, 50000, 80000))
                        history["M5"] = probe_tf(mt5, name, "M5", (2000, 10000, 50000, 80000))
                        history["MN1"] = probe_tf(mt5, name, "MN1", (2000, 5000))
            row = {
                "asset": name,
                "symbol": name,
                "class": klass,
                "classify_reason": reason,
                "equity_cfd": equity,
                "meta": pick_meta(spec),
                "timeframes": history,
                "history_depth": dict(
                    (tf, (history[tf] or {}).get("calendar_span")) for tf in history
                ),
                "data_fields": ["OHLC", "tick_volume", "spread"],
                "qualification": (history.get("D1") or {}).get("qualification"),
            }
            assets.append(row)
            if len(assets) % 50 == 0:
                print("UNI_PROG", len(assets), "/", len(symbols), flush=True)
        for sym in ("GOLD", "EURUSD", "SILVER"):
            print("TICK", sym, flush=True)
            ticks.append(tick_probe(mt5, sym))
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
    counts = {}
    for row in assets:
        counts[row["class"]] = counts.get(row["class"], 0) + 1
    payload = {
        "universe_id": "MT5_UNIVERSE_V5",
        "utc": now(),
        "package": ver,
        "maxbars": maxbars,
        "n": len(assets),
        "class_counts": counts,
        "disk_frozen": disk,
        "ticks": ticks,
        "assets": assets,
        "FINAL_OOS_TOUCHED": False,
        "overwrite_20260825": False,
    }
    dump_json(os.path.join(OUT, "MT5_UNIVERSE_V5.json"), payload)
    dump_json(
        os.path.join(OUT, "TICK_CAPABILITY_V5.json"),
        {"utc": now(), "rows": ticks, "note": "Broker ticks. Not an order book."},
    )
    print("V5_UNI_DONE", len(assets), counts, flush=True)
    for row in ticks:
        print("TICK_ROW", row.get("symbol"), row.get("status"), row.get("count"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
