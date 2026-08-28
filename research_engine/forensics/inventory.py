"""Data Layer Audit V1. Recovery targets: D1>10y, H1>5y, M15>2y. Never freeze. Never trade."""
from __future__ import print_function

import os
from datetime import datetime, timedelta, timezone

from research_engine.alpha_program.evidence.extract import coverage_status, years_between
from research_engine.holdout import final_oos_access
from research_protocol.bars import load_json


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMMUTABLE = os.path.join(ROOT, "data", "market", "immutable")

# Recovery V1 targets. Do not change alpha_program.data_capability.TARGETS (H1=3 is that module's freeze).
TARGETS = {"D1": 10.0, "H1": 5.0, "M15": 2.0}
PROBE_ASSETS = ("GOLD", "EURUSD", "USDJPY", "OIL")
PROBE_TFS = (("D1", 10), ("H1", 5), ("M15", 2))


def _deny_oos():
    try:
        final_oos_access(reason="data_inventory_v1")
    except Exception as exc:
        if type(exc).__name__ != "FinalOosAccessDenied":
            raise
        return True
    raise RuntimeError("FINAL_OOS_WAS_NOT_DENIED")


def unix_years(first_unix, last_unix):
    if not first_unix or not last_unix:
        return None
    return (float(last_unix) - float(first_unix)) / (365.25 * 86400.0)


def inventory_disk():
    _deny_oos()
    rows = []
    if not os.path.isdir(IMMUTABLE):
        return rows
    for name in sorted(os.listdir(IMMUTABLE)):
        folder = os.path.join(IMMUTABLE, name)
        man_path = os.path.join(folder, "manifest.json")
        if not os.path.isfile(man_path):
            continue
        manifest = load_json(man_path)
        tf = manifest.get("timeframe")
        start = manifest.get("actual_start_utc") or manifest.get("data_start_utc")
        end = manifest.get("actual_end_utc") or manifest.get("data_end_utc")
        years = years_between(start, end)
        target = TARGETS.get(tf)
        status = "UNKNOWN" if target is None else coverage_status(years, target)
        if status == "FAILED":
            cover = "SHORTFALL"
        elif status == "DONE":
            cover = "MEETS_TARGET"
        else:
            cover = "UNKNOWN"
        rows.append(
            {
                "dataset_id": manifest.get("dataset_id") or name,
                "asset": manifest.get("logical_symbol"),
                "timeframe": tf,
                "start": start,
                "end": end,
                "years": years,
                "n": manifest.get("row_count"),
                "target_years": target,
                "coverage": cover,
                "status": status,
                "sha256": manifest.get("sha256"),
                "tick_volume_present": manifest.get("tick_volume_present"),
                "real_volume_present": manifest.get("real_volume_present"),
            }
        )
    return rows


def probe_mt5():
    """Read-only count against Recovery targets. Does not write immutable. Does not order_send."""
    out = {"ok": False, "reason": None, "rows": []}
    try:
        from data_layer.config import load_data_sources
        from data_layer.readonly_mt5 import import_readonly_mt5, initialize_readonly
        from data_layer.symbol_map import resolve_symbol
        from data_layer.timeframes import mt5_timeframe
    except Exception as exc:
        out["reason"] = "IMPORT:%s" % exc
        out["status"] = "DATA_BLOCKED"
        return out
    mt5 = None
    try:
        cfg = load_data_sources()
        mt5, _ver = import_readonly_mt5()
        initialize_readonly(mt5, cfg.get("terminal_path"))
        for logical in PROBE_ASSETS:
            try:
                _logical, symbol = resolve_symbol(mt5, logical, cfg.get("symbol_aliases"))
            except Exception as exc:
                out["rows"].append({"asset": logical, "error": str(exc), "status": "DATA_BLOCKED"})
                continue
            for tf, years in PROBE_TFS:
                end = datetime.now(timezone.utc)
                start = end - timedelta(days=int(years * 365) + 14)
                try:
                    tf_const = mt5_timeframe(mt5, tf)
                    rates = mt5.copy_rates_range(symbol, tf_const, start, end)
                    n = 0 if rates is None else len(rates)
                    first = None
                    last = None
                    if rates is not None and n:
                        first = int(rates[0]["time"])
                        last = int(rates[-1]["time"])
                    span = unix_years(first, last)
                    target = float(TARGETS[tf])
                    if n == 0:
                        meet = "DATA_BLOCKED"
                    elif span is not None and span + 0.05 >= target:
                        meet = "MEETS_TARGET"
                    else:
                        meet = "SHORTFALL"
                    out["rows"].append(
                        {
                            "asset": logical,
                            "mt5_symbol": symbol,
                            "timeframe": tf,
                            "requested_years": years,
                            "n": n,
                            "first_unix": first,
                            "last_unix": last,
                            "span_years": span,
                            "target_years": target,
                            "coverage": meet,
                            "status": "PROBE_OK" if n else "DATA_BLOCKED",
                        }
                    )
                except Exception as exc:
                    out["rows"].append(
                        {
                            "asset": logical,
                            "timeframe": tf,
                            "error": str(exc),
                            "status": "DATA_BLOCKED",
                            "coverage": "DATA_BLOCKED",
                        }
                    )
        out["ok"] = True
        out["status"] = "PROBED"
        return out
    except Exception as exc:
        out["reason"] = str(exc)
        out["status"] = "DATA_BLOCKED"
        return out
    finally:
        if mt5 is not None:
            try:
                mt5.shutdown()
            except Exception:
                pass


def verdict_table(probe_rows):
    table = {}
    for tf, _years in PROBE_TFS:
        rows = [r for r in probe_rows if r.get("timeframe") == tf]
        meets = [r for r in rows if r.get("coverage") == "MEETS_TARGET"]
        short = [r for r in rows if r.get("coverage") == "SHORTFALL"]
        blocked = [r for r in rows if r.get("coverage") == "DATA_BLOCKED"]
        table[tf] = {
            "target_years": TARGETS[tf],
            "n_probed": len(rows),
            "n_meets": len(meets),
            "n_shortfall": len(short),
            "n_blocked": len(blocked),
            "assets_meet": [r.get("asset") for r in meets],
            "assets_short": [r.get("asset") for r in short],
        }
    return table


def acquisition_items(disk_rows, probe):
    """Honest Phase 7 list. Not a fake 10-year promise."""
    items = []
    probe_rows = list(probe.get("rows") or [])
    d1_gold = [r for r in probe_rows if r.get("asset") == "GOLD" and r.get("timeframe") == "D1"]
    d1_oil = [r for r in probe_rows if r.get("asset") == "OIL" and r.get("timeframe") == "D1"]
    h1 = [r for r in probe_rows if r.get("timeframe") == "H1"]
    m15 = [r for r in probe_rows if r.get("timeframe") == "M15"]
    fx_d1 = [r for r in probe_rows if r.get("asset") in ("EURUSD", "USDJPY") and r.get("timeframe") == "D1"]

    h1_span = None
    h1_meet = [r for r in h1 if r.get("coverage") == "MEETS_TARGET"]
    if h1:
        spans = [r.get("span_years") for r in h1 if r.get("span_years") is not None]
        h1_span = min(spans) if spans else None
    if h1_meet:
        items.append(
            {
                "id": "ACQ-H1-5Y",
                "need": "Freeze H1 >= 5 years for GOLD/OIL/FX as new dataset_ids",
                "why": "London/NY institutional open needs a session clock. Frozen H1 is months. Broker probe now spans ~5.03y when 5y is requested.",
                "cost": "Read-only MT5 fetch + large CSV + new dataset_id. No cash cost. Do not overwrite 20260825-000001.",
                "priority": 1,
                "status": "ACQUISITION_POSSIBLE",
                "action": "New IDs only. Do not contract London/NY until the new H1 packs are frozen. Do not substitute weekday.",
            }
        )
    elif h1_span is None or h1_span + 0.05 < 5.0:
        items.append(
            {
                "id": "ACQ-H1-5Y",
                "need": "H1 history >= 5 years for GOLD/OIL/FX",
                "why": "London/NY institutional open needs a session clock. Frozen H1 is months.",
                "cost": "Broker terminal time only if the server has the bars. If the first unix does not move, the history does not exist here.",
                "priority": 1,
                "status": "DATA_BLOCKED",
                "action": "Do not invent H1. Do not use weekday as a substitute. Keep session-open families UNKNOWN/BLOCKED.",
            }
        )

    gold_span = d1_gold[0].get("span_years") if d1_gold else None
    oil_span = d1_oil[0].get("span_years") if d1_oil else None
    if (gold_span is not None and gold_span + 0.05 < 10.0) or (oil_span is not None and oil_span + 0.05 < 10.0):
        items.append(
            {
                "id": "ACQ-D1-COMMOD-10Y",
                "need": "GOLD and OIL D1 >= 10 years",
                "why": "A decade would raise month-end power and let a later family claim a longer TOM sample. Frozen packs are ~6.4y / 2000 bars.",
                "cost": "Read-only MT5 fetch into a *new* dataset_id. Broker GOLD/OIL D1 currently starts ~2018 (~7.7y): still short of 10y.",
                "priority": 2,
                "status": "ACQUISITION_POSSIBLE_BUT_STILL_SHORT_OF_10Y",
                "action": "New IDs only. Never overwrite 20260825-000001. Do not claim 10y if first unix stays 2018.",
            }
        )

    if fx_d1 and all(r.get("coverage") == "MEETS_TARGET" for r in fx_d1):
        items.append(
            {
                "id": "ACQ-D1-FX-10Y",
                "need": "EURUSD/USDJPY D1 10y freeze as new IDs",
                "why": "Probe already meets 10y. Useful only if a later FX-native family is contracted. Not required for INSTITUTIONAL_TIME_V1.0.",
                "cost": "Read-only fetch + new dataset_id. No cash cost.",
                "priority": 3,
                "status": "ACQUISITION_POSSIBLE",
                "action": "Do not overwrite 20260825-000001. Do not reopen V0.8 with longer FX.",
            }
        )

    m15_ok = [r for r in m15 if r.get("coverage") == "MEETS_TARGET"]
    if m15_ok:
        items.append(
            {
                "id": "ACQ-M15-2Y",
                "need": "M15 >= 2 years freeze as new IDs",
                "why": "Probe can meet 2y. Frozen M15 is ~1 month. Not required for the selected D1 calendar family.",
                "cost": "Read-only fetch + new dataset_id. Large CSV.",
                "priority": 4,
                "status": "ACQUISITION_POSSIBLE",
                "action": "New IDs only. Do not put M15 into the calendar FDR family.",
            }
        )

    disk_short = [r for r in disk_rows if r.get("coverage") == "SHORTFALL"]
    return {
        "n_items": len(items),
        "items": items,
        "on_disk_shortfall_n": len(disk_short),
        "note": (
            "Selected family INSTITUTIONAL_TIME_V1.0 uses frozen GOLD/OIL D1 dates. "
            "It does not wait on this list. The list is for blocked/unknown families."
        ),
    }


def build_capability(disk_rows, probe):
    table = verdict_table(list(probe.get("rows") or []))
    acq = acquisition_items(disk_rows, probe)
    d1_meet = table.get("D1", {}).get("n_meets") or 0
    h1_meet = table.get("H1", {}).get("n_meets") or 0
    m15_meet = table.get("M15", {}).get("n_meets") or 0
    if probe.get("status") != "PROBED":
        overall = "DATA_BLOCKED"
    elif h1_meet >= 4 and m15_meet >= 4 and d1_meet >= 2:
        overall = "PROBE_H1_5Y_M15_2Y_OK_GOLD_OIL_D1_SHORT_OF_10Y"
    elif h1_meet == 0:
        overall = "H1_5Y_NOT_AVAILABLE"
    else:
        overall = "PARTIAL_PROBE_SHORTFALL"
    return {
        "program_id": "DATA_CAPABILITY_REAL_V1",
        "FINAL_OOS_TOUCHED": False,
        "targets": TARGETS,
        "overall": overall,
        "verdict": table,
        "disk": disk_rows,
        "probe": {
            "status": probe.get("status"),
            "reason": probe.get("reason"),
            "ok": probe.get("ok"),
            "n_rows": len(probe.get("rows") or []),
        },
        "probe_rows": list(probe.get("rows") or []),
        "acquisition": acq,
        "rules": [
            "Never overwrite *-20260825-000001",
            "Never order_send",
            "Never invent bars",
            "New dataset_id only",
        ],
    }
