"""Freeze NEW dataset IDs from live MT5. Never write 20260825."""
from __future__ import print_function

from datetime import datetime, timezone

from data_layer.constants import SCHEMA_VERSION
from data_layer.fetch import _terminal_fields, _volume_flags
from data_layer.logging_util import utc_now
from data_layer.schema import bar_from_mt5_row, required_columns
from data_layer.storage import freeze_dataset, latest_parent, next_dataset_id
from research_engine.alpha_program.evidence.extract import years_between
from research_engine.mt5_history import ACQUIRE_RULES, FROZEN_TOKEN, TF_MINUTES
from research_engine.mt5_history.probe import tf_const
from research_engine.mt5_history.qualify import qualify_bars


def logical_from_symbol(mt5_symbol, known):
    if mt5_symbol in known:
        return known[mt5_symbol]
    compact = "".join(ch for ch in str(mt5_symbol) if ch.isalnum())
    return compact.upper() or "UNKNOWN"


def disk_best(inventory, logical, timeframe):
    best = None
    for row in inventory:
        if row.get("logical") != logical or row.get("timeframe") != timeframe:
            continue
        if FROZEN_TOKEN in str(row.get("dataset_id") or ""):
            continue
        if best is None or float(row.get("years") or 0) > float(best.get("years") or 0):
            best = row
    return best


def should_acquire(probe, logical, timeframe, inventory, equity_cfd=False):
    if equity_cfd:
        return False, "equity_cfd_inventory_only"
    years = float(probe.get("calendar_span") or 0)
    rule = ACQUIRE_RULES.get(timeframe)
    if rule is None:
        return False, "no_auto_rule"
    existing = disk_best(inventory, logical, timeframe)
    if existing and float(existing.get("years") or 0) + 0.05 >= years:
        return False, "already_have_%s" % existing.get("dataset_id")
    if years + 0.02 >= rule:
        return True, "meets_%sy" % rule
    if existing is None and years >= max(2.0, rule * 0.5) and timeframe == "D1":
        return True, "new_symbol_d1_partial"
    return False, "below_threshold"


def fetch_bars(mt5, symbol, timeframe, first_unix, count_hint):
    const = tf_const(mt5, timeframe)
    collected = []
    methods = []
    # Never range from 1970: Ava copy_rates_range can stall minutes with no bars.
    if first_unix:
        end = datetime.now(timezone.utc)
        start = datetime.fromtimestamp(int(first_unix), tz=timezone.utc)
        ranged = mt5.copy_rates_range(symbol, const, start, end)
        if ranged is not None:
            for row in ranged:
                collected.append(bar_from_mt5_row(row))
            methods.append("copy_rates_range:%s" % len(ranged))
    want = max(int(count_hint or 0), 2000)
    want = min(want, 400000)
    pos = mt5.copy_rates_from_pos(symbol, const, 0, want)
    if pos is None:
        for step in (2000, 10000, 50000, 80000):
            pos = mt5.copy_rates_from_pos(symbol, const, 0, step)
            if pos is not None:
                methods.append("copy_rates_from_pos_fallback:%s" % len(pos))
                break
    if pos is not None:
        if not collected or len(pos) > len(collected):
            collected = [bar_from_mt5_row(row) for row in pos]
        methods.append("copy_rates_from_pos:%s" % len(pos))
    seen = {}
    out = []
    for bar in collected:
        key = bar.get("timestamp_unix")
        if key is None or key in seen:
            continue
        seen[key] = True
        out.append(bar)
    out.sort(key=lambda b: b.get("timestamp_unix") or 0)
    return out, "+".join(methods)


def freeze_new(mt5, cfg, logical, symbol, timeframe, bars, methods, logger, package_version):
    if not bars:
        return {"ok": False, "error": "empty"}
    quality = qualify_bars(bars, timeframe)
    if quality.get("validation_status") == "FAIL":
        return {"ok": False, "logical": logical, "timeframe": timeframe, "error": quality.get("fail_reasons")}
    start = bars[0]["timestamp_utc"]
    end = bars[-1]["timestamp_utc"]
    retrieved = utc_now()
    day = retrieved[0:4] + retrieved[5:7] + retrieved[8:10]
    storage_root = cfg["storage_root"]
    parent = latest_parent(storage_root, logical, timeframe)
    dataset_id = next_dataset_id(storage_root, logical, timeframe, day, parent)
    if FROZEN_TOKEN in dataset_id:
        raise RuntimeError("REFUSED_OVERWRITE")
    broker, terminal, terminal_path, terminal_version = _terminal_fields(mt5)
    flags = _volume_flags(quality)
    span = years_between(start, end)
    manifest = {
        "dataset_id": dataset_id,
        "parent_dataset_id": parent,
        "logical_symbol": logical,
        "mt5_symbol": symbol,
        "timeframe": timeframe,
        "timeframe_minutes": TF_MINUTES.get(timeframe),
        "source": "mt5",
        "source_type": "broker_terminal",
        "broker": broker,
        "terminal": terminal,
        "terminal_path": terminal_path,
        "terminal_version": terminal_version,
        "python_package_version": package_version,
        "retrieved_at_utc": retrieved,
        "timezone": "UTC",
        "data_start_utc": start,
        "data_end_utc": end,
        "row_count": len(bars),
        "columns": required_columns(),
        "volume_policy": flags.get("volume_policy"),
        "tick_volume_present": flags.get("tick_volume_present"),
        "real_volume_present": flags.get("real_volume_present"),
        "spread_present": flags.get("spread_present"),
        "history_request": {"method": methods, "actual_count": len(bars)},
        "actual_start_utc": start,
        "actual_end_utc": end,
        "actual_count": len(bars),
        "sha256": None,
        "validation_status": quality.get("validation_status"),
        "schema_version": SCHEMA_VERSION,
        "role": "RESEARCH",
        "FINAL_OOS_LOCKED": False,
        "storage_policy": cfg.get("storage_policy"),
        "bars_format": "csv",
        "acquisition": "MT5_MAX_V4",
        "overwrite_frozen": False,
        "calendar_span_years": span,
    }
    digest = freeze_dataset(storage_root, dataset_id, bars, manifest, quality)
    if logger:
        try:
            logger.emit("DATASET_FROZEN", dataset_id=dataset_id, row_count=len(bars), years=span)
        except Exception:
            pass
    return {
        "ok": True,
        "dataset_id": dataset_id,
        "logical": logical,
        "mt5_symbol": symbol,
        "timeframe": timeframe,
        "n": len(bars),
        "start": start,
        "end": end,
        "years": span,
        "sha256": digest,
        "qualification": quality.get("validation_status"),
    }
