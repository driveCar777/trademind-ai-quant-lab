#!/usr/bin/env python3
"""Close V5.1 machine files after BREADTH + SIZE_SPREAD. No MT5."""
from __future__ import print_function

import os
import sys
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import json as _json

from research_engine.io_util import dump_json


def load_json(path):
    handle = open(path, "r", encoding="utf-8")
    try:
        return _json.load(handle)
    finally:
        handle.close()

UNI = os.path.join(ROOT, "data", "market", "research_engine", "mt5_universe")
RE = os.path.join(ROOT, "data", "market", "research_engine")
DOCS = os.path.join(ROOT, "docs", "research_engine")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    uni = load_json(os.path.join(UNI, "MT5_UNIVERSE_V5.json"))
    hist = load_json(os.path.join(UNI, "MT5_HISTORY_V5.json"))
    stage_b = load_json(os.path.join(UNI, "STAGE_B_HISTORY.json"))
    acquired = load_json(os.path.join(UNI, "ACQUIRED_V5.json"))
    rows = list(hist.get("rows") or [])
    for item in stage_b.get("rows") or []:
        tfs = item.get("timeframes") or {}
        for tf, rec in tfs.items():
            if not rec or rec.get("status") != "OK":
                continue
            rows.append(
                {
                    "symbol": item.get("symbol"),
                    "timeframe": tf,
                    "bars": rec.get("bar_count"),
                    "first": rec.get("first_bar"),
                    "last": rec.get("last_bar"),
                    "calendar_span": rec.get("calendar_span"),
                    "quality": rec.get("coverage"),
                    "probe_stage": "B",
                }
            )
    dump_json(
        os.path.join(UNI, "MT5_HISTORY_V5.json"),
        {
            "matrix_id": "MT5_HISTORY_DEPTH_MATRIX_V5",
            "utc": now(),
            "n": len(rows),
            "rows": rows,
            "acquired_v5": acquired.get("rows") or [],
            "note": "Stage A metadata 841. Deep TFs on first ~190 + Stage B interesting 22. New D1 IDs are 20260829.",
        },
    )
    dump_json(
        os.path.join(RE, "ALPHA_OPPORTUNITY_V5.json"),
        {
            "opportunity_id": "ALPHA_OPPORTUNITY_V5",
            "utc": now(),
            "mt5_symbols": uni.get("total_symbols"),
            "instrument_type": uni.get("instrument_type_counts"),
            "true_options": 0,
            "true_futures": 0,
            "new_information": [
                "7 agricultural CFDs 7.7y D1",
                "EURO-BUND and JAPAN_BOND CFD 7.7y D1",
                "US_2000 D1 17.12y",
                "638 equity CFDs / 67 ETF CFDs = same OHLC class, not a new object",
            ],
            "tested_v5_plus": [
                "XS_REV_V1 KILLED",
                "CORR_SHOCK_V1 KILLED",
                "ENERGY_RV_V1 KILLED",
                "VOL_TERM_V1 KILLED",
                "IDX_ASYNC_V1 KILLED",
                "BREADTH_V1 WEAK_EDGE KILLED",
                "SIZE_SPREAD_V1 NO_CANDIDATE KILLED",
            ],
            "do_not_run": [
                "RSI MA MACD Donchian simple momentum reversal breakout",
                "USD to GOLD",
                "stock-CFD breadth clone of BREADTH_V1",
                "index-breadth clone of BREADTH_V1",
                "GER40 pctl clone of IDX_ASYNC_V1",
            ],
            "next": "EXTERNAL_DATA_GATE",
            "missing_objects": ["futures_curve", "option_surface", "macro_consensus"],
            "level": 0,
            "candidate_count": 0,
            "FINAL_OOS_TOUCHED": False,
        },
    )
    mem = {
        "memory_id": "RESEARCH_MEMORY_V5",
        "utc": now(),
        "level": 0,
        "candidate_count": 0,
        "top5_status": "ALL_KILLED",
        "v51_status": "BREADTH_WEAK_EDGE_AND_SIZE_NO_CANDIDATE",
        "next": "EXTERNAL_DATA_GATE",
        "records": [
            {
                "mechanism": "BREADTH_V1",
                "contract": "2ee70c767492a23101343885b653910b0b4e757cf7d50d0417a32d03a17ecf0a",
                "result": "WEAK_EDGE Xavier 01=04 253b06ffac63bf6ca4985dec4132baf5c60ec16a4243064798484fb323ab0fae FDR 0 book_pass 0001 only p=0.84",
                "reopen_condition": "Do not retune lookback/thrust/hold. Do not flip to buy US500. Do not run stock-CFD clone.",
            },
            {
                "mechanism": "SIZE_SPREAD_V1",
                "contract": "7dce045b1207dedce7dfa2e6c9e453fea5ab1119849332b49dc583ce79aa7603",
                "result": "NO_CANDIDATE Xavier 01=04 77094eeee747c077c8a3a2f3db9bc935691f45946fac60c9bb2bd354acf49410",
                "reopen_condition": "Do not search lookback. Do not flip to buy US500.",
            },
        ],
    }
    dump_json(os.path.join(RE, "RESEARCH_MEMORY_V5.json"), mem)
    pri = load_json(os.path.join(RE, "ALPHA_PRIORITY_V5.json"))
    pri["utc"] = now()
    pri["after_top5"] = "BREADTH_V1 then SIZE_SPREAD_V1 executed. EXTERNAL_DATA_GATE."
    pri["v51"] = [
        {"rank": 1, "mechanism": "BREADTH_V1", "status": "KILLED", "outcome": "WEAK_EDGE"},
        {"rank": 2, "mechanism": "SIZE_SPREAD_V1", "status": "KILLED", "outcome": "NO_CANDIDATE"},
    ]
    dump_json(os.path.join(RE, "ALPHA_PRIORITY_V5.json"), pri)
    lib = load_json(os.path.join(RE, "ALPHA_MECHANISM_LIBRARY_V5.json"))
    lib["utc"] = now()
    for row in lib.get("mechanisms") or []:
        if row.get("mechanism") in (
            "ENERGY_RV_V1",
            "VOL_TERM_V1",
            "IDX_ASYNC_V1",
            "XS_REV_V1",
            "CORR_SHOCK_V1",
        ):
            row["status"] = "KILLED"
            row["already_tested"] = True
    lib["mechanisms"].append(
        {
            "mechanism": "BREADTH_V1",
            "economic_rationale": "Ag CFD participation thrust/contract as risk regime for GOLD / short the complex.",
            "data_required": ["7 ag D1 20260829", "GOLD D1 20260828"],
            "asset_class": "AGRICULTURAL+METAL",
            "time_horizon": "5 D1 bars",
            "already_tested": True,
            "novel": True,
            "status": "KILLED",
            "priority": 6,
        }
    )
    lib["mechanisms"].append(
        {
            "mechanism": "SIZE_SPREAD_V1",
            "economic_rationale": "US2000 minus US500 20d sign cross as size/risk thermometer into GOLD.",
            "data_required": ["US2000 D1 20260829", "US500 D1 20260828", "GOLD D1 20260828"],
            "asset_class": "INDEX+METAL",
            "time_horizon": "5 D1 bars",
            "already_tested": True,
            "novel": True,
            "status": "KILLED",
            "priority": 7,
        }
    )
    lib["n"] = len(lib["mechanisms"])
    dump_json(os.path.join(RE, "ALPHA_MECHANISM_LIBRARY_V5.json"), lib)
    failed = load_json(os.path.join(DOCS, "FAILED_ALPHA_DATABASE_V2.json"))
    failed["records"].append(
        {
            "family": "BREADTH_V1",
            "mechanism": "7-ag 20d participation thrust/contract into GOLD / short ag book",
            "what_was_tested": "HYP-BR-0001/0002/0003 local 2000 + four Xavier",
            "what_failed": "WEAK_EDGE; FDR 0/3; only 0001 gate-pass; p=0.84; CI includes 0",
            "why": "New ag class used as participation, not FX rank. Tiny GOLD TR after cost is not two-hyp FDR. Do not retune. Do not stock-CFD clone.",
            "forbidden_reopen_pattern": "lookback/thrust/hold search; buy US500; stock or index breadth clone",
            "status": "KILLED",
            "search_space_hash": "2ee70c767492a23101343885b653910b0b4e757cf7d50d0417a32d03a17ecf0a",
            "tag": "RESEARCH-2026-0020",
            "cross_check_match": True,
            "xavier_01_04_hash": "253b06ffac63bf6ca4985dec4132baf5c60ec16a4243064798484fb323ab0fae",
        }
    )
    failed["records"].append(
        {
            "family": "SIZE_SPREAD_V1",
            "mechanism": "US2000 minus US500 20d sign cross into GOLD / size book",
            "what_was_tested": "HYP-SZ-0001/0002/0003 local 2000 + four Xavier",
            "what_failed": "NO_CANDIDATE; FDR 0/3; book_pass empty",
            "why": "New 17y US2000 series. Size thermometer did not produce a costed two-hyp FDR edge. Do not search lookback. Do not buy US500.",
            "forbidden_reopen_pattern": "size lookback search; sign flip; buy US500 on lead",
            "status": "KILLED",
            "search_space_hash": "7dce045b1207dedce7dfa2e6c9e453fea5ab1119849332b49dc583ce79aa7603",
            "tag": "RESEARCH-2026-0021",
            "cross_check_match": True,
            "xavier_01_04_hash": "77094eeee747c077c8a3a2f3db9bc935691f45946fac60c9bb2bd354acf49410",
        }
    )
    failed["n"] = len(failed["records"])
    dump_json(os.path.join(DOCS, "FAILED_ALPHA_DATABASE_V2.json"), failed)
    dump_json(os.path.join(RE, "FAILED_ALPHA_DATABASE_V2.json"), failed)
    dump_json(os.path.join(RE, "forensics", "FAILED_ALPHA_DATABASE_V2.json"), failed)
    ledger = load_json(os.path.join(RE, "DATA_COST_LEDGER_V5.json"))
    ledger["utc"] = now()
    ledger["spent_usd"] = 0
    ledger["gate"] = "EXTERNAL_DATA_GATE"
    dump_json(os.path.join(RE, "DATA_COST_LEDGER_V5.json"), ledger)
    print("CLOSE", "hist", len(rows), "failed", failed["n"])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
