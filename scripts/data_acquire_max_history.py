"""Fetch max available MT5 history into NEW dataset IDs. Never overwrite 20260825."""
from __future__ import print_function

import os
import sys
import time
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from data_layer.config import load_data_sources
from data_layer.constants import SCHEMA_VERSION
from data_layer.fetch import _terminal_fields, _volume_flags, os_path_join_logs
from data_layer.logging_util import DataLayerLogger, utc_now
from data_layer.readonly_mt5 import import_readonly_mt5, initialize_readonly
from data_layer.schema import bar_from_mt5_row, required_columns
from data_layer.storage import ensure_layout, freeze_dataset, latest_parent, next_dataset_id
from data_layer.symbol_map import resolve_symbol
from data_layer.timeframes import mt5_timeframe, timeframe_minutes
from data_layer.validation import validate_bars
from research_engine.alpha_program.evidence.extract import years_between
from research_engine.io_util import dump_json
from research_protocol.bars import load_json as load_manifest

TARGETS = (
    ("GOLD", "D1", 20, 20000),
    ("OIL", "D1", 20, 20000),
    ("EURUSD", "D1", 20, 20000),
    ("USDJPY", "D1", 20, 20000),
    ("GOLD", "H1", 8, 100000),
    ("OIL", "H1", 8, 100000),
    ("EURUSD", "H1", 8, 100000),
    ("USDJPY", "H1", 8, 100000),
)
FROZEN_TOKEN = "20260825-000001"


def _merge(bars):
    seen = {}
    out = []
    for bar in bars:
        key = bar.get("timestamp_unix") or bar.get("timestamp_utc")
        if key is None or key in seen:
            continue
        seen[key] = True
        out.append(bar)
    out.sort(key=lambda b: (b.get("timestamp_unix") is None, b.get("timestamp_unix") or 0, b.get("timestamp_utc") or ""))
    return out


def fetch_max(mt5, symbol, timeframe, years, max_count):
    tf = mt5_timeframe(mt5, timeframe)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=int(years * 365) + 40)
    collected = []
    methods = []
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, int(max_count))
    if rates is not None:
        for row in rates:
            collected.append(bar_from_mt5_row(row))
        methods.append("copy_rates_from_pos:%s" % len(rates))
        if len(rates) >= int(max_count) - 1:
            extra = mt5.copy_rates_from_pos(symbol, tf, 0, int(max_count) * 2)
            if extra is not None and len(extra) > len(rates):
                collected = []
                for row in extra:
                    collected.append(bar_from_mt5_row(row))
                methods.append("copy_rates_from_pos_2x:%s" % len(extra))
    ranged = mt5.copy_rates_range(symbol, tf, start, end)
    if ranged is not None:
        for row in ranged:
            collected.append(bar_from_mt5_row(row))
        methods.append("copy_rates_range:%s" % len(ranged))
    bars = _merge(collected)
    return bars, {
        "method": "+".join(methods) if methods else "none",
        "requested_start_utc": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "requested_end_utc": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "requested_years": years,
        "requested_count": max_count,
        "actual_count": len(bars),
    }


def already_max(inventory, logical, timeframe):
    best = None
    for row in inventory:
        if row.get("instrument") != logical or row.get("timeframe") != timeframe:
            continue
        if FROZEN_TOKEN in str(row.get("dataset_id") or ""):
            continue
        if best is None or float(row.get("calendar_span") or 0) > float(best.get("calendar_span") or 0):
            best = row
    return best


def freeze_one(mt5, cfg, logical, timeframe, years, max_count, logger, package_version):
    logical, symbol = resolve_symbol(mt5, logical, cfg.get("symbol_aliases"))
    bars, request = fetch_max(mt5, symbol, timeframe, years, max_count)
    broker, terminal, terminal_path, terminal_version = _terminal_fields(mt5)
    quality = validate_bars(bars, timeframe)
    if quality.get("validation_status") == "FAIL":
        return {"ok": False, "logical": logical, "timeframe": timeframe, "error": quality.get("fail_reasons")}
    actual_start = bars[0]["timestamp_utc"] if bars else None
    actual_end = bars[-1]["timestamp_utc"] if bars else None
    retrieved = utc_now()
    day = retrieved[0:4] + retrieved[5:7] + retrieved[8:10]
    storage_root = cfg["storage_root"]
    parent = latest_parent(storage_root, logical, timeframe)
    dataset_id = next_dataset_id(storage_root, logical, timeframe, day, parent)
    if FROZEN_TOKEN in dataset_id:
        raise RuntimeError("REFUSED_OVERWRITE")
    flags = _volume_flags(quality)
    span = years_between(actual_start, actual_end)
    status = "ACQUIRED"
    if timeframe == "D1" and logical in ("GOLD", "OIL") and span is not None and span + 0.05 < 10.0:
        status = "BROKER_LIMITATION"
        quality.setdefault("warn_reasons", []).append("BROKER_LIMITATION_GOLD_OIL_D1_LT_10Y")
        if quality.get("validation_status") == "PASS":
            quality["validation_status"] = "WARN"
    if timeframe == "H1" and span is not None and span + 0.05 < 8.0:
        quality.setdefault("warn_reasons", []).append("H1_SHORTER_THAN_8Y_REQUEST")
        if logical in ("GOLD", "OIL") and span + 0.05 < 5.0:
            status = "BROKER_LIMITATION"
    manifest = {
        "dataset_id": dataset_id,
        "parent_dataset_id": parent,
        "logical_symbol": logical,
        "mt5_symbol": symbol,
        "timeframe": timeframe,
        "timeframe_minutes": timeframe_minutes(timeframe),
        "source": "mt5",
        "source_type": "broker_terminal",
        "broker": broker,
        "terminal": terminal,
        "terminal_path": terminal_path,
        "terminal_version": terminal_version,
        "python_package_version": package_version,
        "retrieved_at_utc": retrieved,
        "timezone": "UTC",
        "data_start_utc": actual_start,
        "data_end_utc": actual_end,
        "row_count": len(bars),
        "columns": required_columns(),
        "volume_policy": flags["volume_policy"],
        "tick_volume_present": flags["tick_volume_present"],
        "real_volume_present": flags["real_volume_present"],
        "spread_present": flags["spread_present"],
        "history_request": request,
        "requested_start_utc": request.get("requested_start_utc"),
        "requested_end_utc": request.get("requested_end_utc"),
        "actual_start_utc": actual_start,
        "actual_end_utc": actual_end,
        "actual_count": len(bars),
        "sha256": None,
        "validation_status": quality.get("validation_status"),
        "schema_version": SCHEMA_VERSION,
        "role": "RESEARCH",
        "FINAL_OOS_LOCKED": False,
        "storage_policy": cfg.get("storage_policy"),
        "bars_format": "csv",
        "acquisition": "MAX_HISTORY_V1",
        "overwrite_frozen": False,
        "broker_status": status,
    }
    digest = freeze_dataset(storage_root, dataset_id, bars, manifest, quality)
    logger.emit("DATASET_FROZEN", dataset_id=dataset_id, row_count=len(bars), years=span, status=status)
    return {
        "ok": True,
        "dataset_id": dataset_id,
        "logical": logical,
        "timeframe": timeframe,
        "n": len(bars),
        "start": actual_start,
        "end": actual_end,
        "years": span,
        "sha256": digest,
        "qualification": quality.get("validation_status"),
        "status": status,
    }


def history_map(storage_root):
    rows = []
    immutable = os.path.join(storage_root, "immutable")
    if not os.path.isdir(immutable):
        return rows
    for name in sorted(os.listdir(immutable)):
        man = os.path.join(immutable, name, "manifest.json")
        if not os.path.isfile(man):
            continue
        m = load_manifest(man)
        start = m.get("actual_start_utc") or m.get("data_start_utc")
        end = m.get("actual_end_utc") or m.get("data_end_utc")
        rows.append(
            {
                "instrument": m.get("logical_symbol"),
                "timeframe": m.get("timeframe"),
                "first_bar": start,
                "last_bar": end,
                "bar_count": m.get("row_count"),
                "calendar_span": years_between(start, end),
                "dataset_id": m.get("dataset_id"),
                "sha256": m.get("sha256"),
                "qualification": m.get("validation_status"),
                "acquisition": m.get("acquisition"),
                "broker_status": m.get("broker_status"),
                "immutable_frozen": FROZEN_TOKEN in str(m.get("dataset_id") or ""),
            }
        )
    return rows


def write_map(cfg, acquired, extra=None):
    mapping = {
        "map_id": "DATA_HISTORY_MAP_V1",
        "FINAL_OOS_TOUCHED": False,
        "overwrite_frozen": False,
        "acquired": acquired,
        "inventory": history_map(cfg["storage_root"]),
        "note": "GOLD/OIL D1 must not be labeled 10y if span is ~7.7y. IT V1.0 still uses 20260825 parents.",
    }
    if extra:
        mapping.update(extra)
    out_dir = os.path.join(ROOT, "data", "market", "research_engine", "forensics")
    dump_json(os.path.join(out_dir, "DATA_HISTORY_MAP_V1.json"), mapping)
    dump_json(os.path.join(ROOT, "docs", "research_engine", "DATA_HISTORY_MAP_V1.json"), mapping)
    return mapping


def main():
    cfg = load_data_sources()
    ensure_layout(cfg["storage_root"])
    logger = DataLayerLogger(os_path_join_logs(cfg["storage_root"]))
    inventory = history_map(cfg["storage_root"])
    acquired = []
    mt5 = None
    ver = None
    try:
        print("ACQ_INIT_START", flush=True)
        mt5, ver = import_readonly_mt5()
        print("ACQ_MT5_IMPORTED", ver, flush=True)
        initialize_readonly(mt5, cfg.get("terminal_path"))
        print("ACQ_MT5_READY", flush=True)
    except Exception as exc:
        mapping = write_map(cfg, [], {"probe_error": str(exc), "status": "DATA_BLOCKED"})
        print("DATA_BLOCKED", exc)
        print("DATA_HISTORY_MAP_V1", len(mapping["inventory"]))
        return 1
    try:
        for logical, tf, years, max_count in TARGETS:
            prior = already_max(inventory, logical, tf)
            if prior and float(prior.get("calendar_span") or 0) >= (7.0 if tf == "D1" else 4.9):
                acquired.append(
                    {
                        "ok": True,
                        "skipped": True,
                        "logical": logical,
                        "timeframe": tf,
                        "dataset_id": prior.get("dataset_id"),
                        "years": prior.get("calendar_span"),
                        "status": "REUSE_EXISTING_MAX",
                    }
                )
                print("ACQ_REUSE", logical, tf, prior.get("dataset_id"), prior.get("calendar_span"))
                continue
            try:
                time.sleep(0.35)
                row = freeze_one(mt5, cfg, logical, tf, years, max_count, logger, ver)
                acquired.append(row)
                inventory = history_map(cfg["storage_root"])
                print("ACQ", row.get("dataset_id") or logical, row.get("status") or row.get("error"), row.get("n"), row.get("years"))
            except Exception as exc:
                acquired.append({"ok": False, "logical": logical, "timeframe": tf, "error": str(exc)})
                print("ACQ_FAIL", logical, tf, exc)
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
    mapping = write_map(cfg, acquired)
    print("DATA_HISTORY_MAP_V1", len(mapping["inventory"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
