# -*- coding: utf-8 -*-
"""V8.2 Options catalog / schema / symbology / MVD quote.

NO DOWNLOAD. NO PURCHASE. Never prints the API key.
Never calls timeseries.get_range or batch.submit_job.
"""
from __future__ import print_function

import io
import json
import os
import sys
import time
from datetime import date, timedelta

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
elif sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from research_engine.data_sources.databento import HistoricalClient
from research_engine.local_fs import force_project_temp
from research_engine.v6_external.env import databento_api_key, has_databento_key

OUT_DIR = os.path.join(ROOT, "data", "market", "research_engine", "options")
DATASET = "GLBX.MDP3"
KEY_SCHEMAS = (
    "definition",
    "ohlcv-1d",
    "statistics",
    "trades",
    "tbbo",
    "bbo-1s",
    "bbo-1m",
    "mbp-1",
    "mbp-10",
    "mbo",
    "status",
)
HIST_END = date(2026, 8, 29)
RAW_SAMPLES = (
    "OGZ6 C5250",
    "OGZ6 P5250",
    "LOU6 P7000",
    "LOU6 C8000",
    "GCZ6",
    "CLZ6",
)
PARENTS_TO_RESOLVE = (
    "GC.OPT",
    "CL.OPT",
    "OG.OPT",
    "LO.OPT",
    "OG1.OPT",
    "OG2.OPT",
    "OG3.OPT",
    "OG4.OPT",
    "OG5.OPT",
    "G1M.OPT",
    "G2M.OPT",
    "G3M.OPT",
    "G1T.OPT",
    "G1W.OPT",
    "G2W.OPT",
    "G1R.OPT",
    "LO1.OPT",
    "LO2.OPT",
    "LO3.OPT",
    "LO4.OPT",
    "LO5.OPT",
    "ML1.OPT",
    "ML2.OPT",
    "NL1.OPT",
    "WL1.OPT",
    "XL1.OPT",
    "MCO.OPT",
    "OGW.OPT",
    "LOW.OPT",
)


def _flush(msg):
    print(msg, flush=True)


def _iso(d):
    return d.isoformat()


def _windows(end):
    # Historical license ends before the live cut. Never quote through "today".
    return {
        "1Y": (_iso(end - timedelta(days=365)), _iso(end)),
        "2Y": (_iso(end - timedelta(days=730)), _iso(end)),
        "3Y": (_iso(end - timedelta(days=1095)), _iso(end)),
    }


def _decode(raw):
    if raw is None:
        return None
    if isinstance(raw, (dict, list, int, float, bool)):
        return raw
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="replace").strip()
    else:
        text = str(raw).strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return text


def _safe_get(client, method, fields):
    try:
        return {"ok": True, "data": _decode(client._get(method, fields))}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:500]}


def _safe_post(client, method, fields):
    try:
        return {"ok": True, "data": _decode(client._post(method, fields))}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:500]}


def _field_names(payload):
    data = payload.get("data") if isinstance(payload, dict) else payload
    names = []
    if isinstance(data, list):
        for row in data:
            if isinstance(row, dict):
                names.append(row.get("name") or row.get("field") or "")
            elif isinstance(row, str):
                names.append(row)
    elif isinstance(data, dict):
        rows = data.get("fields") or data.get("result") or []
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    names.append(row.get("name") or row.get("field") or "")
                elif isinstance(row, str):
                    names.append(row)
        else:
            names = list(data.keys())
    return [n for n in names if n]


def resolve_symbols(client, symbols, stype_in, stype_out, start, end):
    return _safe_post(
        client,
        "symbology.resolve",
        {
            "dataset": DATASET,
            "symbols": symbols,
            "stype_in": stype_in,
            "stype_out": stype_out,
            "start_date": start,
            "end_date": end,
        },
    )


def resolve_parent(client, symbol, start, end):
    # GLBX does not support parent -> raw_symbol. Parent -> instrument_id is valid.
    return resolve_symbols(client, symbol, "parent", "instrument_id", start, end)


def _summarize_resolve(result, symbol):
    out = {
        "symbol": symbol,
        "ok": bool(result.get("ok")),
        "error": result.get("error"),
        "mapping_count": 0,
        "sample_raw": [],
        "sample_ids": [],
        "sample_call_put": [],
        "sample_underlyings": [],
        "not_found": None,
        "partial": None,
    }
    if not result.get("ok"):
        return out
    data = result.get("data") or {}
    mappings = data.get("result") or {}
    samples = []
    cps = set()
    unders = set()
    n = 0
    for _key, rows in mappings.items() if isinstance(mappings, dict) else []:
        if not isinstance(rows, list):
            continue
        n += len(rows)
        for row in rows:
            raw = ""
            if isinstance(row, dict):
                raw = str(row.get("s") or row.get("symbol") or "")
            else:
                raw = str(row)
            if raw:
                samples.append(raw)
                if raw.isdigit() or (raw[:1].isdigit() and raw.replace(".", "", 1).isdigit()):
                    pass
                else:
                    parts = raw.replace("  ", " ").split()
                    if len(parts) >= 2:
                        right = parts[-1]
                        if right[:1] in ("C", "P"):
                            cps.add(right[:1])
                    if parts:
                        root = parts[0]
                        if len(root) >= 3:
                            unders.add(root)
            if len(samples) >= 12:
                break
        if len(samples) >= 12:
            break
    out["mapping_count"] = n
    out["sample_raw"] = samples[:8]
    out["sample_ids"] = samples[:8]
    out["sample_call_put"] = sorted(cps)
    out["sample_underlyings"] = sorted(unders)[:12]
    out["not_found"] = data.get("not_found")
    out["partial"] = data.get("partial")
    return out


def quote(client, schema, symbols, start, end):
    row = {
        "schema": schema,
        "symbols": symbols,
        "start": start,
        "end": end,
        "ok": False,
    }
    try:
        row["cost_usd"] = float(
            client.get_cost(
                dataset=DATASET,
                start=start,
                end=end,
                symbols=symbols,
                schema=schema,
                stype_in="parent",
            )
        )
        row["ok"] = True
    except Exception as exc:
        row["error"] = str(exc)[:400]
    return row


def main():
    force_project_temp()
    os.makedirs(OUT_DIR, exist_ok=True)
    t0 = time.time()
    windows = _windows(HIST_END)
    sample_start = _iso(HIST_END - timedelta(days=10))
    sample_end = _iso(HIST_END)

    _flush("V8.2 OPTIONS DD START  NO_DOWNLOAD  NO_PURCHASE")
    if not has_databento_key():
        raise SystemExit("DATABENTO key missing")
    key = databento_api_key()
    if "DATABENTO" in key.upper() and len(key) < 12:
        raise SystemExit("DATABENTO key shape invalid")
    client = HistoricalClient(key, timeout=180)

    report = {
        "version": "V8.2",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": "QUOTE_ONLY",
        "downloaded": False,
        "purchased": False,
        "dataset": DATASET,
        "windows": windows,
        "phases": {},
    }

    _flush("PHASE A metadata.list_schemas / list_fields / list_unit_prices / dataset_range")
    schemas = _safe_get(client, "metadata.list_schemas", {"dataset": DATASET})
    if not schemas.get("ok"):
        schemas = _safe_post(client, "metadata.list_schemas", {"dataset": DATASET})
    report["phases"]["list_schemas"] = schemas
    _flush("  list_schemas ok=%s n=%s" % (
        schemas.get("ok"),
        len(schemas.get("data") or []) if isinstance(schemas.get("data"), list) else "?",
    ))

    fields = {}
    for schema in KEY_SCHEMAS:
        payload = _safe_get(
            client,
            "metadata.list_fields",
            {"schema": schema, "encoding": "dbn"},
        )
        if not payload.get("ok"):
            payload = _safe_get(
                client,
                "metadata.list_fields",
                {"schema": schema},
            )
        names = _field_names(payload) if payload.get("ok") else []
        fields[schema] = {
            "ok": payload.get("ok"),
            "error": payload.get("error"),
            "field_names": names,
            "raw_type": type(payload.get("data")).__name__ if payload.get("ok") else None,
        }
        _flush("  fields %s ok=%s n=%s" % (schema, payload.get("ok"), len(names)))
    report["phases"]["list_fields"] = fields

    unit_prices = _safe_get(client, "metadata.list_unit_prices", {"dataset": DATASET})
    if not unit_prices.get("ok"):
        unit_prices = _safe_post(client, "metadata.list_unit_prices", {"dataset": DATASET})
    report["phases"]["list_unit_prices"] = unit_prices
    _flush("  list_unit_prices ok=%s" % unit_prices.get("ok"))

    dset_get = _safe_get(client, "metadata.get_dataset_range", {"dataset": DATASET})
    dset_post = _safe_post(client, "metadata.get_dataset_range", {"dataset": DATASET})
    report["phases"]["get_dataset_range"] = {"GET": dset_get, "POST": dset_post}
    _flush("  dataset_range GET ok=%s POST ok=%s" % (dset_get.get("ok"), dset_post.get("ok")))

    _flush("PHASE B symbology.resolve (10-day sample, no download)")
    resolved = {}
    live_parents = []
    for sym in PARENTS_TO_RESOLVE:
        raw = resolve_parent(client, sym, sample_start, sample_end)
        summary = _summarize_resolve(raw, sym)
        resolved[sym] = summary
        if summary["ok"] and summary["mapping_count"] > 0:
            live_parents.append(sym)
        _flush(
            "  resolve %s ok=%s n=%s sample=%s"
            % (sym, summary["ok"], summary["mapping_count"], ",".join(summary["sample_raw"][:3]))
        )
    report["phases"]["symbology"] = resolved
    report["live_parents_10d"] = live_parents

    _flush("PHASE B2 raw_symbol -> instrument_id samples (no download)")
    raw_resolved = {}
    for raw in RAW_SAMPLES:
        raw_res = resolve_symbols(
            client, raw, "raw_symbol", "instrument_id", sample_start, sample_end
        )
        raw_resolved[raw] = _summarize_resolve(raw_res, raw)
        _flush(
            "  raw %s ok=%s n=%s"
            % (raw, raw_resolved[raw]["ok"], raw_resolved[raw]["mapping_count"])
        )
    report["phases"]["symbology_raw_samples"] = raw_resolved

    _flush("PHASE C get_cost MVD grid (quote only)")
    quotes = []
    mvd_specs = (
        ("MVD-A", ("definition", "ohlcv-1d")),
        ("MVD-B", ("definition", "ohlcv-1d", "statistics")),
        ("MVD-C", ("definition", "ohlcv-1d", "bbo-1s")),
        ("MVD-A-STAT", ("definition", "statistics")),
        ("PRICE-ONLY", ("ohlcv-1d",)),
        ("DEF-ONLY", ("definition",)),
        ("STAT-ONLY", ("statistics",)),
    )
    symbol_sets = [
        ("OG", "OG.OPT"),
        ("LO", "LO.OPT"),
        ("OG+LO", "OG.OPT,LO.OPT"),
        ("OG+weeklies", "OG.OPT,OG1.OPT,OG2.OPT,OG3.OPT,OG4.OPT,OG5.OPT"),
        ("LO+weeklies", "LO.OPT,LO1.OPT,LO2.OPT,LO3.OPT,LO4.OPT,LO5.OPT"),
        ("GC.OPT", "GC.OPT"),
        ("CL.OPT", "CL.OPT"),
    ]

    for horizon, (start, end) in windows.items():
        for set_name, symbols in symbol_sets:
            specs = mvd_specs
            if set_name in ("OG+weeklies", "LO+weeklies", "GC.OPT", "CL.OPT"):
                if horizon != "1Y":
                    continue
                specs = (("MVD-A", ("definition", "ohlcv-1d")),)
            for mvd_name, schemas_needed in specs:
                line = {
                    "horizon": horizon,
                    "start": start,
                    "end": end,
                    "symbol_set": set_name,
                    "symbols": symbols,
                    "mvd": mvd_name,
                    "schemas": list(schemas_needed),
                    "parts": [],
                    "total_usd": 0.0,
                    "ok": True,
                }
                for schema in schemas_needed:
                    part = quote(client, schema, symbols, start, end)
                    line["parts"].append(part)
                    if part.get("ok"):
                        line["total_usd"] += float(part["cost_usd"])
                    else:
                        line["ok"] = False
                line["total_usd"] = round(line["total_usd"], 6)
                quotes.append(line)
                _flush(
                    "  %s %s %s $%s ok=%s"
                    % (horizon, set_name, mvd_name, line["total_usd"], line["ok"])
                )

    _flush("PHASE D schema availability cost sample (OG 1Y only)")
    y1_start, y1_end = windows["1Y"]
    for schema in ("bbo-1s", "bbo-1m", "trades", "tbbo", "mbp-1", "mbo"):
        part = quote(client, schema, "OG.OPT", y1_start, y1_end)
        quotes.append(
            {
                "horizon": "1Y",
                "start": y1_start,
                "end": y1_end,
                "symbol_set": "OG",
                "symbols": "OG.OPT",
                "mvd": "AVAIL-%s" % schema,
                "schemas": [schema],
                "parts": [part],
                "total_usd": part.get("cost_usd") if part.get("ok") else None,
                "ok": part.get("ok"),
            }
        )
        _flush(
            "  AVAIL %s $%s ok=%s"
            % (schema, part.get("cost_usd"), part.get("ok"))
        )

    report["phases"]["quotes"] = quotes
    report["elapsed_sec"] = round(time.time() - t0, 1)

    path = os.path.join(OUT_DIR, "OPTION_DD_RAW_V8_2.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    _flush("WROTE %s elapsed=%ss n_quotes=%s" % (path, report["elapsed_sec"], len(quotes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
