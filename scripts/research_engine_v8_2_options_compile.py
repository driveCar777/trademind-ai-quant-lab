# -*- coding: utf-8 -*-
"""Compile V8.2 options artifacts from RAW quote. One extra metadata GET. No download."""
from __future__ import print_function

import io
import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from research_engine.data_sources.databento import HistoricalClient
from research_engine.local_fs import force_project_temp
from research_engine.v6_external.env import databento_api_key, has_databento_key

OUT = os.path.join(ROOT, "data", "market", "research_engine", "options")
RAW_PATH = os.path.join(OUT, "OPTION_DD_RAW_V8_2.json")


def _decode(raw):
    if isinstance(raw, (dict, list)):
        return raw
    text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
    return json.loads(text)


def main():
    force_project_temp()
    raw = json.load(open(RAW_PATH, encoding="utf-8"))
    quotes = raw["phases"]["quotes"]
    resolved = raw["phases"]["symbology"]
    fields = raw["phases"]["list_fields"]
    schemas = raw["phases"]["list_schemas"]["data"]
    unit_prices = raw["phases"]["list_unit_prices"]["data"]
    dset = raw["phases"]["get_dataset_range"]["GET"]["data"]

    def_fields = {"ok": False}
    extra_quotes = []
    if has_databento_key():
        client = HistoricalClient(databento_api_key(), timeout=180)
        try:
            def_fields = {
                "ok": True,
                "data": _decode(
                    client._get(
                        "metadata.list_fields",
                        {"schema": "definition", "encoding": "dbn"},
                    )
                ),
            }
            print("definition fields", len(def_fields["data"]) if isinstance(def_fields["data"], list) else "?", flush=True)
        except Exception as exc:
            def_fields = {"ok": False, "error": str(exc)[:400]}
            print("definition fields FAIL", def_fields["error"], flush=True)
        for label, symbols, schema in (
            ("LO_1Y_TRADES", "LO.OPT", "trades"),
            ("OGLO_1Y_TRADES", "OG.OPT,LO.OPT", "trades"),
            ("LO_1Y_TBBO", "LO.OPT", "tbbo"),
        ):
            try:
                cost = float(
                    client.get_cost(
                        dataset="GLBX.MDP3",
                        schema=schema,
                        symbols=symbols,
                        start="2025-08-29",
                        end="2026-08-29",
                        stype_in="parent",
                    )
                )
                extra_quotes.append({"id": label, "symbols": symbols, "schema": schema, "ok": True, "cost_usd": cost})
                print(label, cost, flush=True)
            except Exception as exc:
                extra_quotes.append({"id": label, "ok": False, "error": str(exc)[:300]})
                print(label, "FAIL", flush=True)

    def_names = []
    if def_fields.get("ok") and isinstance(def_fields.get("data"), list):
        for row in def_fields["data"]:
            if isinstance(row, dict):
                def_names.append(row.get("name") or "")
            elif isinstance(row, str):
                def_names.append(row)
    if not def_names:
        def_names = [
            "raw_symbol",
            "instrument_id",
            "instrument_class",
            "strike_price",
            "expiration",
            "activation",
            "underlying",
            "underlying_id",
            "security_type",
            "asset",
            "ts_event",
            "ts_recv",
        ]
        def_source = "official_docs_fallback"
    else:
        def_source = "metadata.list_fields"

    fields["definition"] = {
        "ok": bool(def_fields.get("ok")),
        "error": def_fields.get("error"),
        "field_names": [n for n in def_names if n],
        "source": def_source,
    }

    parent_rows = []
    for sym, row in resolved.items():
        parent_rows.append(
            {
                "symbol": sym,
                "resolved": bool(row.get("ok") and row.get("mapping_count", 0) > 0),
                "mapping_count_complete": row.get("mapping_count"),
                "partial_n": len(row.get("partial") or []),
                "not_found_n": len(row.get("not_found") or []) if isinstance(row.get("not_found"), list) else None,
                "error": row.get("error"),
                "sample_ids": row.get("sample_ids") or [],
            }
        )

    def qfind(horizon, symbol_set, mvd):
        for row in quotes:
            if row.get("horizon") == horizon and row.get("symbol_set") == symbol_set and row.get("mvd") == mvd:
                return row
        return None

    mvd_table = []
    for horizon in ("1Y", "2Y", "3Y"):
        for symbol_set in ("OG", "LO", "OG+LO", "OG+weeklies", "LO+weeklies"):
            for mvd in ("MVD-A", "MVD-B", "MVD-C", "MVD-A-STAT", "PRICE-ONLY", "DEF-ONLY", "STAT-ONLY"):
                row = qfind(horizon, symbol_set, mvd)
                if not row:
                    continue
                mvd_table.append(
                    {
                        "horizon": horizon,
                        "symbol_set": symbol_set,
                        "mvd": mvd,
                        "start": row.get("start"),
                        "end": row.get("end"),
                        "symbols": row.get("symbols"),
                        "schemas": row.get("schemas"),
                        "ok": row.get("ok"),
                        "total_usd": row.get("total_usd"),
                        "parts": [
                            {
                                "schema": p.get("schema"),
                                "ok": p.get("ok"),
                                "cost_usd": p.get("cost_usd"),
                                "error": p.get("error"),
                            }
                            for p in row.get("parts") or []
                        ],
                    }
                )

    case_a = [r for r in mvd_table if r.get("ok") and r["mvd"] in ("MVD-A", "MVD-B") and r["total_usd"] <= 30]
    case_b = [r for r in mvd_table if r.get("ok") and r["mvd"] in ("MVD-A", "MVD-B") and 30 < r["total_usd"] <= 60]
    case_c = [r for r in mvd_table if r.get("ok") and r["mvd"] in ("MVD-A", "MVD-B") and r["total_usd"] > 60]

    coverage = {
        "catalog_id": "OPTION_COVERAGE_MATRIX_V8_2",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "downloaded": False,
        "purchased": False,
        "dataset": "GLBX.MDP3",
        "dataset_range": dset,
        "schemas_available": schemas,
        "schema_fields": {k: v.get("field_names") for k, v in fields.items()},
        "unit_prices_usd_per_gb": unit_prices,
        "official_docs": {
            "definition_has": [
                "raw_symbol",
                "instrument_id",
                "instrument_class",
                "strike_price",
                "expiration",
                "activation",
                "underlying",
                "underlying_id",
                "security_type",
                "asset",
                "ts_event",
            ],
            "instrument_class": {"C": "call", "P": "put", "T": "option_spread", "F": "future"},
            "security_type_oof": "option on future",
            "ohlcv_1d": {
                "fields": ["ts_event", "open", "high", "low", "close", "volume"],
                "is_official_settlement": False,
                "has_oi": False,
                "has_bid_ask": False,
                "empty_if_no_trade": True,
            },
            "statistics_glbx": {
                "has_settlement_stat_type_3": True,
                "has_cleared_volume_stat_type_6": True,
                "has_open_interest_stat_type_9": True,
                "has_session_high_bid_stat_type_8": True,
                "has_session_low_offer_stat_type_7": True,
                "has_implied_vol_stat_type_14": False,
                "has_delta_stat_type_15": False,
                "source": "Databento types-of-statistics-by-dataset GLBX.MDP3",
            },
        },
        "roots": [
            {
                "symbol": "GC.OPT",
                "underlying": "GC",
                "exists": False,
                "note": "HTTP 422 could not resolve. Not a Databento parent.",
            },
            {
                "symbol": "CL.OPT",
                "underlying": "CL",
                "exists": False,
                "note": "HTTP 422 could not resolve. Not a Databento parent.",
            },
            {
                "symbol": "OG.OPT",
                "underlying": "GC futures (COMEX gold options)",
                "product": "OG",
                "exists": True,
                "expiry_range": "multiple monthly expiries via parent expansion; exact min/max UNKNOWN until definition bytes",
                "strike_range": "parent expands all listed strikes; exact min/max UNKNOWN until definition bytes",
                "call_put": "YES in definition.instrument_class C/P; raw sample OGZ6 C5250 / OGZ6 P5250 resolved",
                "history": "definition/ohlcv-1d/statistics from 2010-06-06 on dataset; product listing may be shorter",
                "schema": ["definition", "ohlcv-1d", "statistics", "trades", "tbbo", "bbo-1s", "mbp-1", "mbo"],
                "volume_availability": "ohlcv-1d.volume (electronic trades only); statistics stat_type=6 cleared volume",
                "oi_availability": "statistics stat_type=9 only; not in ohlcv-1d",
                "settlement_availability": "statistics stat_type=3 only; ohlcv close is NOT official settlement",
                "quote_availability": "bbo-1s/bbo-1m/tbbo/mbp available; first-phase forbidden by cost",
                "weekly": False,
                "includes_user_defined_spreads": True,
            },
            {
                "symbol": "LO.OPT",
                "underlying": "CL futures (NYMEX WTI options)",
                "product": "LO",
                "exists": True,
                "expiry_range": "multiple monthly expiries via parent expansion; exact min/max UNKNOWN until definition bytes",
                "strike_range": "parent expands all listed strikes; exact min/max UNKNOWN until definition bytes",
                "call_put": "YES in definition.instrument_class C/P; raw sample LOU6 P7000 / LOU6 C8000 resolved",
                "history": "definition/ohlcv-1d/statistics from 2010-06-06 on dataset; product listing may be shorter",
                "schema": ["definition", "ohlcv-1d", "statistics", "trades", "tbbo", "bbo-1s", "mbp-1", "mbo"],
                "volume_availability": "ohlcv-1d.volume; statistics stat_type=6",
                "oi_availability": "statistics stat_type=9 only",
                "settlement_availability": "statistics stat_type=3 only",
                "quote_availability": "bbo-1s/tbbo/mbp available; first-phase forbidden by cost",
                "weekly": False,
                "includes_user_defined_spreads": True,
            },
        ],
        "weekly_and_special_roots_10d_20260819_20260829": parent_rows,
        "raw_symbol_samples": raw["phases"].get("symbology_raw_samples"),
        "cme_root_fragmentation": {
            "gold_monthly": "OG.OPT",
            "gold_friday_weeklies": ["OG1.OPT", "OG2.OPT", "OG3.OPT", "OG4.OPT", "OG5.OPT"],
            "gold_weekday_weeklies": ["G{1-5}{M,T,W,R}.OPT"],
            "crude_monthly": "LO.OPT",
            "crude_friday_weeklies": ["LO1.OPT", "LO2.OPT", "LO3.OPT", "LO4.OPT", "LO5.OPT"],
            "crude_weekday_weeklies": ["ML1-5", "NL1-5", "WL1-5", "XL1-5"],
            "micro_crude": "MCO.OPT",
            "og_opt_is_complete_chain": False,
            "lo_opt_is_complete_chain": False,
        },
        "field_audit": {
            "symbol_raw_symbol": "YES definition.raw_symbol",
            "underlying_futures": "YES definition.underlying / underlying_id; samples OGZ6->GC, LOU6->CL",
            "strike_price": "YES definition.strike_price (1e-9)",
            "expiration": "YES definition.expiration",
            "call_put": "YES definition.instrument_class C/P",
            "option_instrument_class": "YES; security_type OOF = option on future",
            "listing_date": "YES definition.activation (listing/activation time)",
            "daily_option_price": "CONDITIONAL ohlcv-1d if a trade occurred; official settle only in statistics",
            "daily_volume": "YES ohlcv-1d.volume and/or statistics cleared volume",
            "open_interest": "YES statistics stat_type=9; NO in ohlcv-1d",
            "settlement": "YES statistics stat_type=3; NO in ohlcv-1d",
            "bid_ask": "YES in bbo-1s/tbbo/mbp; session high bid / low offer in statistics 7/8; NOT in ohlcv-1d",
            "trade_availability": "YES trades schema; ohlcv built from electronic trades",
            "timestamp": "YES ts_event / ts_recv",
            "knowledge_time": "research rule: settlement T 21:00Z; OI T+1 21:00Z; ohlcv close != official settle",
        },
    }

    incremental = {
        "already_owned_do_not_rebuy": {
            "dataset_id": "tm-fut-GLBX-CURVE-D1-20260829-000001",
            "parents": ["GC.FUT", "CL.FUT"],
            "fields": [
                "front_settle",
                "second_settle",
                "front_open",
                "front_expiry",
                "second_expiry",
                "front_oi",
                "slope",
                "steepening",
                "settlement_knowledge_utc",
                "oi_knowledge_utc",
            ],
            "use_for": ["underlying futures price", "realized volatility", "curve reference"],
            "pack_e_billed_usd": 31.816129,
        },
        "options_must_add": [
            "option definition (strike, expiry, C/P, underlying map)",
            "option price (ohlcv close and/or official settlement)",
            "option volume (optional liquidity filter)",
            "option OI (optional liquidity filter; statistics only)",
        ],
        "options_must_not_add": [
            "GC.FUT / CL.FUT again",
            "MBO / MBP-10 / MBP-1",
            "bbo-1s (OG 1Y ~$62,745)",
            "GVZ / OVX (already failed; not the surface)",
            "$199/month Standard",
        ],
        "iv_status": "DERIVED not OBSERVED. GLBX.MDP3 statistics has no stat_type 14/15.",
        "pricing_model_if_derived": {
            "model": "Black-76",
            "not": "equity Black-Scholes",
            "inputs": [
                "underlying futures price (owned GC/CL settlement)",
                "strike (definition)",
                "expiry (definition)",
                "option price (ohlcv close or statistics settlement)",
                "risk-free (owned UST DGS10 proxy)",
            ],
            "assumptions": [
                "OG/LO are American; Black-76 is European futures-option approximation",
                "early-exercise residual not priced",
                "r from DGS10 is a proxy not the matching discount curve",
                "ohlcv close != official settlement",
            ],
        },
    }

    mvd = {
        "catalog_id": "OPTION_MVD_V8_2",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "downloaded": False,
        "purchased": False,
        "OPTION_INCREMENTAL_DATA_REQUIREMENT": incremental,
        "pre_registered_scope": {
            "strikes": ["nearest ATM", "±5%", "±10%"],
            "expiries": ["front", "second", "third_optional"],
            "history_compared": ["1Y", "2Y", "3Y"],
            "roots_phase1": ["OG.OPT", "LO.OPT"],
            "weeklies_phase1": False,
            "ai_may_not_change_after_quote": ["strike", "expiry", "hold", "sign"],
        },
        "tiers": {
            "MVD-A": {
                "schemas": ["definition", "ohlcv-1d"],
                "purpose": "instrument map + electronic daily option prices + trade volume",
                "can_compute_iv": "CONDITIONAL_DERIVED",
                "can_compute_atm_iv": "CONDITIONAL",
                "can_compute_skew": "CONDITIONAL",
                "can_compute_term": "CONDITIONAL",
                "missing": ["official settlement", "OI", "bid/ask", "venue IV"],
                "blocker": "ohlcv-1d emits no bar if no electronic trade; OTM occupancy UNKNOWN until bytes",
            },
            "MVD-B": {
                "schemas": ["definition", "ohlcv-1d", "statistics"],
                "purpose": "MVD-A plus official settlement, cleared volume, OI",
                "adds": ["settlement", "OI", "cleared volume", "session high bid / low offer"],
                "research_value_increment": "HIGH for surface construction and liquidity filter; still no venue IV",
                "og_cost_note": "OG statistics is expensive (1Y $40.79, 3Y $70.77)",
                "lo_cost_note": "LO statistics cheaper (1Y $12.10, 3Y $30.74)",
            },
            "MVD-C": {
                "schemas": ["definition", "ohlcv-1d", "bbo-1s"],
                "purpose": "only if A/B cannot answer the research question",
                "default_buy": False,
                "og_1y_usd": 62759.69,
                "forbidden_reason": "destroys the $93 credit floor",
            },
        },
        "quotes": mvd_table,
        "extra_quotes": extra_quotes,
        "recommended_if_human_later_buys": {
            "not_this_task": True,
            "cheapest_dual_attempt": "1Y OG+LO MVD-A $26.986529",
            "cheapest_official_settle_one_commodity": "1Y LO MVD-B $24.088709",
            "cheapest_2y_one_commodity": ["2Y OG MVD-A $24.886548", "2Y LO MVD-A $23.126337"],
            "do_not_buy_mvd_c": True,
        },
    }

    quote_out = {
        "catalog_id": "OPTION_QUOTE_V8_2",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": "QUOTE_ONLY",
        "downloaded": False,
        "purchased": False,
        "auto_purchase_allowed": False,
        "auto_purchase_max_usd": 30.0,
        "credit_floor_usd": 60.0,
        "credit_remaining_usd_estimate": 93.18,
        "dataset": "GLBX.MDP3",
        "end_used": "2026-08-29",
        "end_note": "today 2026-08-30 is live-cut; get_cost requires end before ~2026-08-29T18:59Z",
        "windows": raw["windows"],
        "quotes": mvd_table,
        "availability_quotes": [r for r in quotes if str(r.get("mvd", "")).startswith("AVAIL-")],
        "extra_quotes": extra_quotes,
        "case_a_mvd_ab": case_a,
        "case_b_mvd_ab": case_b,
        "case_c_mvd_ab": case_c,
        "v8_revalidated": {
            "OG_3Y_MVD-A": 32.413535,
            "LO_3Y_MVD-A": 34.224269,
            "OG+LO_3Y_MVD-A": 66.637805,
            "LO_3Y_DEF+STAT": 54.274733,
            "OG_3Y_PRICE_ONLY": 9.533126,
        },
        "do_not": [
            "timeseries.get_range",
            "batch.submit_job",
            "mbo/mbp/bbo-1s",
            "$199/month Standard",
            "rebuy GC.FUT/CL.FUT",
            "print API key",
        ],
    }

    for name, payload in (
        ("OPTION_COVERAGE_MATRIX_V8_2.json", coverage),
        ("OPTION_MVD_V8_2.json", mvd),
        ("OPTION_QUOTE_V8_2.json", quote_out),
    ):
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        print("WROTE", path, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
