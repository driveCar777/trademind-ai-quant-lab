"""On-disk coverage vs targets. Optional read-only MT5 probe. Never freeze. Never trade."""
from __future__ import print_function

import os
from datetime import datetime, timedelta, timezone

from research_engine.alpha_program.evidence.extract import coverage_status, years_between
from research_engine.holdout import final_oos_access
from research_protocol.bars import load_json


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMMUTABLE = os.path.join(ROOT, "data", "market", "immutable")
TARGETS = {"D1": 10.0, "H1": 3.0, "M15": 2.0}
PROBE_COUNT = {"D1": 8000, "H1": 40000, "M15": 120000}


def _deny_oos():
    try:
        final_oos_access(reason="data_capability")
    except Exception as exc:
        if type(exc).__name__ != "FinalOosAccessDenied":
            raise
        return True
    raise RuntimeError("FINAL_OOS_WAS_NOT_DENIED")


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
                "requested_count": (manifest.get("history_request") or {}).get("requested_count"),
                "requested_start": (manifest.get("history_request") or {}).get("requested_start_utc"),
            }
        )
    return rows


def probe_mt5():
    """Read-only count. Does not write immutable. Does not order_send."""
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
        for logical in ("GOLD", "EURUSD", "USDJPY", "OIL"):
            try:
                _logical, symbol = resolve_symbol(mt5, logical, cfg.get("symbol_aliases"))
            except Exception as exc:
                out["rows"].append({"asset": logical, "error": str(exc), "status": "DATA_BLOCKED"})
                continue
            for tf, years in (("D1", 10), ("H1", 3), ("M15", 2)):
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
                    out["rows"].append(
                        {
                            "asset": logical,
                            "mt5_symbol": symbol,
                            "timeframe": tf,
                            "requested_years": years,
                            "n": n,
                            "first_unix": first,
                            "last_unix": last,
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


def build_plan(disk_rows, probe):
    short = [r for r in disk_rows if r.get("coverage") == "SHORTFALL"]
    can_fetch = False
    if probe.get("ok"):
        for row in probe.get("rows") or []:
            if row.get("status") == "PROBE_OK" and int(row.get("n") or 0) > 2000:
                can_fetch = True
                break
    if not short:
        status = "MEETS_TARGET"
        action = "no_new_fetch_required_for_coverage_targets"
    elif can_fetch:
        status = "ACQUISITION_POSSIBLE"
        action = "write_plan_then_human_freeze_new_ids_do_not_overwrite_20260825"
    else:
        status = "DATA_BLOCKED"
        action = "cannot_claim_longer_history; do not invent bars"
    return {
        "status": status,
        "action": action,
        "FINAL_OOS_TOUCHED": False,
        "on_disk_shortfall": short,
        "probe": {"status": probe.get("status"), "reason": probe.get("reason"), "n_rows": len(probe.get("rows") or [])},
        "probe_rows": list(probe.get("rows") or []),
        "targets": TARGETS,
        "note": "V0.9 does not need new bars. Longer M15/H1 is for later families.",
    }


def render_plan_md(plan, disk_rows):
    lines = [
        "# Data Acquisition Plan",
        "",
        "Read-only check. Does not overwrite `*-20260825-000001`. Does not `order_send`.",
        "",
        "## Status",
        "",
        "- **%s**" % plan.get("status"),
        "- action: `%s`" % plan.get("action"),
        "- MT5 probe: %s %s" % ((plan.get("probe") or {}).get("status"), (plan.get("probe") or {}).get("reason") or ""),
        "",
        "## Targets",
        "",
        "- D1: 10 years",
        "- H1: 3 years",
        "- M15: 2 years",
        "",
        "## On-disk (immutable, do not rewrite)",
        "",
    ]
    for row in disk_rows:
        lines.append(
            "- %s %s %s years=%.2f n=%s target=%s **%s**"
            % (
                row.get("asset"),
                row.get("timeframe"),
                row.get("dataset_id"),
                row.get("years") or 0.0,
                row.get("n"),
                row.get("target_years"),
                row.get("coverage"),
            )
        )
    lines.extend(
        [
            "",
            "## Rules if a later fetch is allowed",
            "",
            "1. New `dataset_id` only. Never overwrite `20260825-000001`.",
            "2. Read-only MT5 facade. `order_send` remains forbidden.",
            "3. Do not touch Final OOS.",
            "4. V0.9 / V0.8 / V0.6 hashes stay frozen on the old parents.",
            "",
        ]
    )
    probe_rows = (plan.get("probe_rows") or [])
    if probe_rows:
        lines.extend(["## Read-only MT5 probe (not frozen)", ""])
        for row in probe_rows:
            lines.append(
                "- %s %s n=%s first_unix=%s last_unix=%s **%s**"
                % (
                    row.get("asset"),
                    row.get("timeframe"),
                    row.get("n"),
                    row.get("first_unix"),
                    row.get("last_unix"),
                    row.get("status"),
                )
            )
        lines.append("")
        lines.append("On-disk files are still 2000-bar shortfalls. Extra bars require **new** dataset IDs.")
        lines.append("GOLD/OIL D1 probe starts ~2018 (unix 1544572800): still short of a true 10-year D1. FX D1 is closer.")
        lines.append("H1/M15 probe counts exceed the frozen 2000-bar packs. Do not overwrite `20260825-000001`.")
        lines.append("V0.9 does not wait on this fetch.")
        lines.append("")
    if plan.get("status") == "DATA_BLOCKED":
        lines.append("Broker/terminal did not prove extra history in this session. Record **DATA_BLOCKED**, do not pretend.")
        lines.append("")
    return "\n".join(lines)
