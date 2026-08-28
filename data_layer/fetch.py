"""Read-only MT5 fetch → validate → immutable freeze. Never starts a backtest."""

import time
from datetime import datetime, timedelta, timezone

from data_layer.config import load_data_sources
from data_layer.constants import SCHEMA_VERSION
from data_layer.errors import ValidationFailedError
from data_layer.logging_util import DataLayerLogger, utc_now
from data_layer.readonly_mt5 import import_readonly_mt5, initialize_readonly
from data_layer.schema import bar_from_mt5_row, required_columns
from data_layer.storage import (
    ensure_layout,
    freeze_dataset,
    latest_parent,
    next_dataset_id,
)
from data_layer.symbol_map import resolve_symbol
from data_layer.timeframes import mt5_timeframe, normalize_timeframe, timeframe_minutes
from data_layer.validation import validate_bars


def _terminal_fields(mt5):
    info = mt5.terminal_info()
    version = mt5.version()
    broker = None
    terminal = None
    path = None
    if info is not None:
        broker = getattr(info, "company", None)
        terminal = getattr(info, "name", None)
        path = getattr(info, "path", None)
    terminal_version = None
    if version is not None:
        terminal_version = {
            "version": version[0] if len(version) > 0 else None,
            "build": version[1] if len(version) > 1 else None,
            "build_date": str(version[2]) if len(version) > 2 else None,
        }
    return broker, terminal, path, terminal_version


def _slice_last(bars, count):
    if count and len(bars) > count:
        return bars[-count:]
    return bars


def fetch_rates(mt5, mt5_symbol, timeframe, requested_count, slack_factor):
    tf = mt5_timeframe(mt5, timeframe)
    minutes = timeframe_minutes(timeframe)
    end = datetime.now(timezone.utc)
    window = int(requested_count * minutes * slack_factor)
    start = end - timedelta(minutes=window)
    method = "copy_rates_range"
    last_error = None
    rates = mt5.copy_rates_range(mt5_symbol, tf, start, end)
    if rates is None:
        last_error = mt5.last_error()
        method = "copy_rates_from_pos"
        rates = mt5.copy_rates_from_pos(mt5_symbol, tf, 0, requested_count)
        if rates is None:
            last_error = mt5.last_error()
    bars = []
    if rates is not None:
        for row in rates:
            bars.append(bar_from_mt5_row(row))
    bars = _slice_last(bars, requested_count)
    request = {
        "method": method,
        "requested_start_utc": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "requested_end_utc": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "requested_count": requested_count,
        "actual_count": len(bars),
        "last_error": None if last_error is None else list(last_error) if hasattr(last_error, "__iter__") else str(last_error),
        "fallback_used": method == "copy_rates_from_pos",
    }
    return bars, request


def _volume_flags(quality):
    return {
        "tick_volume_present": quality.get("tick_volume_present"),
        "real_volume_present": quality.get("real_volume_present"),
        "spread_present": quality.get("spread_present"),
        "volume_policy": quality.get("volume_policy"),
    }


def fetch_and_freeze(logical, timeframe, config=None, logger=None):
    cfg = config or load_data_sources()
    storage_root = cfg["storage_root"]
    ensure_layout(storage_root)
    if logger is None:
        logger = DataLayerLogger(os_path_join_logs(storage_root))

    logical = (logical or "").strip().upper()
    timeframe = normalize_timeframe(timeframe)
    logger.emit(
        "DATA_FETCH_START",
        logical_symbol=logical,
        timeframe=timeframe,
        requested_count=cfg["requested_bars"],
    )

    mt5, package_version = import_readonly_mt5()
    initialize_readonly(mt5, cfg.get("terminal_path"))
    broker, terminal, terminal_path, terminal_version = _terminal_fields(mt5)
    logger.emit(
        "MT5_INITIALIZED",
        broker=broker,
        terminal=terminal,
        terminal_path=terminal_path,
        python_package_version=package_version,
    )

    logical, mt5_symbol = resolve_symbol(mt5, logical, cfg.get("symbol_aliases"))
    logger.emit("SYMBOL_RESOLVED", logical_symbol=logical, mt5_symbol=mt5_symbol)

    time.sleep(max(0.0, float(cfg.get("rate_limit_seconds") or 0)))
    bars, history_request = fetch_rates(
        mt5,
        mt5_symbol,
        timeframe,
        cfg["requested_bars"],
        cfg["request_slack_factor"],
    )
    try:
        mt5.shutdown()
    except Exception:
        pass

    actual_start = bars[0]["timestamp_utc"] if bars else None
    actual_end = bars[-1]["timestamp_utc"] if bars else None
    history_shortfall = max(0, cfg["requested_bars"] - len(bars))
    logger.emit(
        "RATES_FETCHED",
        logical_symbol=logical,
        timeframe=timeframe,
        mt5_symbol=mt5_symbol,
        row_count=len(bars),
        data_start_utc=actual_start,
        data_end_utc=actual_end,
        history_shortfall=history_shortfall,
        method=history_request.get("method"),
    )

    quality = validate_bars(bars, timeframe)
    if history_shortfall:
        quality.setdefault("warn_reasons", []).append("history_shortfall")
        if quality.get("validation_status") == "PASS":
            quality["validation_status"] = "WARN"
        quality["history_shortfall"] = history_shortfall
    else:
        quality["history_shortfall"] = 0
    logger.emit(
        "DATA_VALIDATED",
        logical_symbol=logical,
        timeframe=timeframe,
        validation_status=quality.get("validation_status"),
        row_count=quality.get("row_count"),
        gap_count=quality.get("gap_count"),
    )
    if quality.get("validation_status") == "FAIL":
        logger.emit(
            "ERROR",
            logical_symbol=logical,
            timeframe=timeframe,
            fail_reasons=quality.get("fail_reasons"),
        )
        raise ValidationFailedError(
            "%s %s validation FAIL: %s" % (logical, timeframe, quality.get("fail_reasons"))
        )

    retrieved = utc_now()
    day = retrieved[0:4] + retrieved[5:7] + retrieved[8:10]
    parent = latest_parent(storage_root, logical, timeframe)
    dataset_id = next_dataset_id(storage_root, logical, timeframe, day, parent)
    flags = _volume_flags(quality)
    manifest = {
        "dataset_id": dataset_id,
        "parent_dataset_id": parent,
        "logical_symbol": logical,
        "mt5_symbol": mt5_symbol,
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
        "history_request": history_request,
        "history_shortfall": history_shortfall,
        "requested_start_utc": history_request.get("requested_start_utc"),
        "requested_end_utc": history_request.get("requested_end_utc"),
        "requested_count": history_request.get("requested_count"),
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
    }
    digest = freeze_dataset(storage_root, dataset_id, bars, manifest, quality)
    logger.emit("DATA_WRITTEN", dataset_id=dataset_id, row_count=len(bars))
    logger.emit("MANIFEST_WRITTEN", dataset_id=dataset_id)
    logger.emit("HASH_CREATED", dataset_id=dataset_id, sha256=digest)
    logger.emit(
        "DATASET_FROZEN",
        dataset_id=dataset_id,
        logical_symbol=logical,
        timeframe=timeframe,
        row_count=len(bars),
        data_start_utc=actual_start,
        data_end_utc=actual_end,
    )
    manifest["sha256"] = digest
    return {
        "dataset_id": dataset_id,
        "manifest": manifest,
        "quality": quality,
    }


def os_path_join_logs(storage_root):
    import os

    return os.path.join(storage_root, "logs", "data_layer.log")


def fetch_matrix(config=None, logger=None):
    cfg = config or load_data_sources()
    results = []
    for logical in cfg["logical_symbols"]:
        for timeframe in cfg["timeframes"]:
            try:
                results.append(
                    {
                        "ok": True,
                        "result": fetch_and_freeze(logical, timeframe, cfg, logger),
                    }
                )
            except Exception as exc:
                if logger is None:
                    logger = DataLayerLogger(os_path_join_logs(cfg["storage_root"]))
                logger.emit(
                    "ERROR",
                    logical_symbol=logical,
                    timeframe=timeframe,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
                results.append(
                    {
                        "ok": False,
                        "logical_symbol": logical,
                        "timeframe": timeframe,
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    }
                )
            time.sleep(max(0.0, float(cfg.get("rate_limit_seconds") or 0)))
    return results
