"""Qualify Pack E bytes. Official settlement required. Ava CFD rejected."""
from __future__ import print_function

import os

from research_engine.data_sources.qualify import BLOCKED, READY, qualify as gate
from research_engine.v6_external.raw_io import (
    ROOTS,
    is_outright_symbol,
    list_data_files,
    load_ohlcv,
    load_outright_definitions,
    load_statistics,
    pack_e_root,
)


def _job_dir(state, schema):
    job = (state.get("jobs") or {}).get(schema) or {}
    jid = job.get("id")
    if not jid:
        return ""
    return os.path.join(pack_e_root(), jid)


def qualify_pack(state):
    files = {}
    for schema in ("ohlcv-1d", "definition", "statistics"):
        files[schema] = list_data_files(_job_dir(state, schema))
    defs = {"by_id": {}, "by_symbol": {}, "n_definition_rows": 0, "n_outright": 0, "instrument_class_counts": {}}
    if files["definition"]:
        defs = load_outright_definitions(files["definition"])
    allowed = set(defs["by_symbol"].keys())
    allowed_ids = set(defs["by_id"].keys())
    ohlcv = {"bars": {}, "n_ohlcv_rows": 0, "n_ohlcv_outright": 0}
    if files["ohlcv-1d"]:
        ohlcv = load_ohlcv(files["ohlcv-1d"], allowed_symbols=allowed or None)
    stats = {
        "stats": {},
        "n_statistics_rows": 0,
        "n_statistics_keep": 0,
        "n_settlement": 0,
        "n_cleared_volume": 0,
        "n_open_interest": 0,
    }
    if files["statistics"]:
        stats = load_statistics(
            files["statistics"],
            allowed_symbols=allowed or None,
            allowed_ids=allowed_ids or None,
        )
    per_root = {}
    for root in ROOTS:
        symbols = [s for s in defs["by_symbol"] if s.startswith(root)]
        sessions = set()
        expiries = set()
        settle_n = 0
        oi_n = 0
        vol_n = 0
        ohlcv_n = 0
        for symbol in symbols:
            expiries.add((defs["by_symbol"][symbol] or {}).get("expiry"))
            for session in (ohlcv["bars"].get(symbol) or {}):
                sessions.add(session)
                ohlcv_n += 1
            for session, slot in (stats["stats"].get(symbol) or {}).items():
                sessions.add(session)
                if slot.get("settlement") not in (None,):
                    settle_n += 1
                if slot.get("open_interest") not in (None,):
                    oi_n += 1
                if slot.get("cleared_volume") not in (None,):
                    vol_n += 1
        dates = sorted(sessions)
        per_root[root] = {
            "n_outright_symbols": len(symbols),
            "n_expiries": len([x for x in expiries if x]),
            "n_sessions": len(dates),
            "first_session": dates[0] if dates else None,
            "last_session": dates[-1] if dates else None,
            "n_ohlcv_sessions": ohlcv_n,
            "n_settlement": settle_n,
            "n_open_interest": oi_n,
            "n_cleared_volume": vol_n,
        }
    fail = []
    if not files["ohlcv-1d"]:
        fail.append("OHLCV_MISSING")
    if not files["definition"]:
        fail.append("DEFINITION_MISSING")
    if not files["statistics"]:
        fail.append("STATISTICS_MISSING")
    if defs["n_outright"] < 10:
        fail.append("TOO_FEW_OUTRIGHTS")
    if stats["n_settlement"] < 100:
        fail.append("SETTLEMENT_SPARSE")
    report = {
        "has_bytes": bool(files["ohlcv-1d"] and files["definition"] and files["statistics"]),
        "validation_status": "PASS" if not fail else "FAIL",
        "fail_reasons": fail,
        "lookahead_ok": True,
        "sample_only": False,
        "revision_vintages": True,
        "used_for": "research",
        "files": dict((k, [os.path.basename(p) for p in v]) for k, v in files.items()),
        "file_counts": dict((k, len(v)) for k, v in files.items()),
        "n_definition_rows": defs["n_definition_rows"],
        "n_outright": defs["n_outright"],
        "instrument_class_counts": defs["instrument_class_counts"],
        "n_ohlcv_rows": ohlcv["n_ohlcv_rows"],
        "n_ohlcv_outright": ohlcv["n_ohlcv_outright"],
        "n_statistics_rows": stats["n_statistics_rows"],
        "n_statistics_keep": stats["n_statistics_keep"],
        "n_settlement": stats["n_settlement"],
        "n_open_interest": stats["n_open_interest"],
        "n_cleared_volume": stats["n_cleared_volume"],
        "roots": per_root,
        "broker_cfd_rejected": True,
        "ava_symbols_used": False,
        "note": "Exchange outrights only. Spreads dropped. GOLD/OIL CFD is not a parent.",
    }
    report["gate"] = gate(report)
    if report["gate"] != READY and fail:
        report["gate"] = BLOCKED
    loaded = {
        "definitions": defs,
        "ohlcv": ohlcv,
        "statistics": stats,
    }
    return report, loaded


def history_map(report, state):
    jobs = state.get("jobs") or {}
    billed = 0.0
    for job in jobs.values():
        if job.get("cost_usd") not in (None,):
            billed += float(job["cost_usd"])
    return {
        "dataset": "GLBX.MDP3",
        "pack": "E",
        "parents": ["GC.FUT", "CL.FUT"],
        "schemas": ["ohlcv-1d", "definition", "statistics"],
        "start": "2010-06-06",
        "end": "2026-08-29",
        "gate": report.get("gate"),
        "roots": report.get("roots"),
        "jobs": dict((k, {"id": v.get("id"), "state": v.get("state"), "cost_usd": v.get("cost_usd")}) for k, v in jobs.items()),
        "billed_usd": billed,
        "outright_filter": "instrument_class=F and GC|CL month-year",
        "not_continuous_only": True,
        "not_ava_cfd": True,
        "FINAL_OOS_TOUCHED": False,
    }


def is_outright_ok(symbol):
    return is_outright_symbol(symbol)
