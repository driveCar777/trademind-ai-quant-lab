# -*- coding: utf-8 -*-
"""Compile V8.3 feasibility artifacts from RAW. No API calls."""
from __future__ import print_function

import json
import os
import sys
import time
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "market", "research_engine", "options")
RAW = os.path.join(OUT, "OPTION_FEASIBILITY_RAW_V8_3.json")


def _rate(rows):
    sessions = sorted(set(x["session"] for x in rows))
    bar_sessions = sorted(set(x["session"] for x in rows if x.get("has_bar")))
    listed_sessions = sorted(set(x["session"] for x in rows if x.get("listed")))
    return {
        "n_obs": len(rows),
        "n_sessions": len(sessions),
        "listed_sessions": len(listed_sessions),
        "bar_sessions": len(bar_sessions),
        "ATM_OBSERVATION_RATE": (float(len(bar_sessions)) / len(sessions)) if sessions else None,
        "sessions": sessions,
        "bar_sessions_list": bar_sessions,
    }


def main():
    raw = json.load(open(RAW, encoding="utf-8"))
    obs = raw["observations"]
    occupancy = {}
    for root in ("GC", "CL"):
        occupancy[root] = {}
        for tenor in ("front", "second"):
            occupancy[root][tenor] = {}
            for bucket, name in (
                (0.0, "ATM"),
                (-0.05, "OTM_PUT_5"),
                (0.05, "OTM_CALL_5"),
                (-0.10, "OTM_PUT_10"),
                (0.10, "OTM_CALL_10"),
            ):
                rows = [
                    x
                    for x in obs
                    if x["root"] == root
                    and x["tenor"] == tenor
                    and abs(float(x["bucket"]) - bucket) < 1e-9
                ]
                occupancy[root][tenor][name] = _rate(rows)

        term = 0
        skew = {"front": 0, "second": 0}
        sessions = sorted(set(x["session"] for x in obs if x["root"] == root))
        for session in sessions:
            xs = [x for x in obs if x["root"] == root and x["session"] == session]
            atm_f = any(
                x["tenor"] == "front" and abs(x["bucket"]) < 1e-12 and x.get("has_bar")
                for x in xs
            )
            atm_s = any(
                x["tenor"] == "second" and abs(x["bucket"]) < 1e-12 and x.get("has_bar")
                for x in xs
            )
            if atm_f and atm_s:
                term += 1
            for tenor in ("front", "second"):
                sub = [x for x in xs if x["tenor"] == tenor]
                atm = any(abs(x["bucket"]) < 1e-12 and x.get("has_bar") for x in sub)
                op = any(x["bucket"] < 0 and x.get("has_bar") for x in sub)
                oc = any(x["bucket"] > 0 and x.get("has_bar") for x in sub)
                if atm and op and oc:
                    skew[tenor] += 1
        occupancy[root]["term_front_and_second_atm_sessions"] = term
        occupancy[root]["term_rate"] = float(term) / len(sessions) if sessions else None
        occupancy[root]["skew_sessions"] = skew
        occupancy[root]["skew_rate"] = {
            k: (float(v) / len(sessions) if sessions else None) for k, v in skew.items()
        }

    parents = {}
    for row in raw["parent_counts"]:
        parents[row["id"]] = {
            "symbols": row["symbols"],
            "schema": row["schema"],
            "start": row["start"],
            "end": row["end"],
            "record_count": row["record_count"].get("value") if row["record_count"].get("ok") else None,
            "record_count_error": row["record_count"].get("error"),
            "billable_size": row["billable_size"].get("value") if row["billable_size"].get("ok") else None,
        }

    coverage = {
        "catalog_id": "OPTION_DEFINITION_COVERAGE_V8_3",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "downloaded": False,
        "purchased": False,
        "source": "symbology.resolve raw_symbol + constructed ATM/OTM from owned futures. Not a definition download.",
        "phase1_kind": "outright_call_put_only",
        "excluded": ["weekly", "calendar_spread", "user_defined_UD", "micro_MCO"],
        "n": len(raw["definition_coverage"]),
        "instruments": raw["definition_coverage"],
        "listing": "UNKNOWN without definition.activation bytes",
        "expiration": "UNKNOWN exact; month code inferred from raw_symbol",
        "weekly_parents": raw["weekly_resolve"],
    }

    feasibility = {
        "catalog_id": "OPTION_FEASIBILITY_V8_3",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": "METADATA_ONLY",
        "downloaded": False,
        "purchased": False,
        "atm_definition": raw["atm_definition"],
        "snapshot_targets_preregistered": [
            "2025-08-29",
            "2025-10-31",
            "2025-12-31",
            "2026-02-27",
            "2026-04-30",
            "2026-06-30",
            "2026-08-14",
            "2026-08-28",
        ],
        "full_1y_census": "NOT_RUN",
        "parent_record_counts": parents,
        "occupancy_sample": occupancy,
        "notes": {
            "og_futures_front_is_not_live_option": True,
            "og_live_option_in_this_mapping": "futures second month",
            "ohlcv_count_gt_0_means_electronic_trade_that_utc_day": True,
            "definition_available_not_equal_ohlcv_available": True,
        },
        "iv": {
            "status": "DERIVED",
            "exchange_iv": False,
            "model": "Black-76",
            "inputs": [
                "option price from ohlcv-1d if bar exists",
                "owned GC/CL front_settle",
                "strike from raw_symbol / definition",
                "expiry from definition (exact UNKNOWN until bytes)",
                "UST DGS10 proxy",
            ],
        },
        "research_limitation": [
            "MVD-A has no bid/ask; IV is last-trade not mid",
            "ohlcv close is not official settlement",
            "American early exercise",
            "8-date sample is not a 252-day census",
        ],
    }

    selection = {
        "catalog_id": "OPTION_MVD_SELECTION_V8_3",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "downloaded": False,
        "this_mission_purchase": False,
        "case": "B",
        "case_meaning": "MVD likely researchable on the 8-date sample; full-year occupancy not censused",
        "preferred_if_human_later": {
            "package": "OG_1Y_MVD-A",
            "symbols": "OG.OPT",
            "schemas": ["definition", "ohlcv-1d"],
            "window": ["2025-08-29", "2026-08-29"],
            "cost_usd": 14.994811,
            "unlocks": ["DERIVED ATM IV on live gold option month", "IV-RV vs owned GC RV", "likely skew on that month"],
            "still_impossible": [
                "venue IV",
                "bid/ask mid IV",
                "official option settlement",
                "proven OG term (front+second under futures mapping is 0/8)",
                "252-day ATM census",
            ],
        },
        "ranking": [
            {"rank": 1, "package": "OG_1Y_MVD-A", "cost_usd": 14.994811, "why": "Answers IV-RV if live option month is used; cheapest gold surface"},
            {"rank": 2, "package": "LO_1Y_MVD-A", "cost_usd": 11.991718, "why": "Stronger sample occupancy for IV+skew+term; not preferred because OG IV-RV is the first question"},
            {"rank": 3, "package": "LO_1Y_MVD-B", "cost_usd": 24.088709, "why": "Adds official settle+OI; not auto-preferred"},
            {"rank": 4, "package": "OG+LO_1Y_MVD-A", "cost_usd": 26.986529, "why": "Do not auto-buy dual"},
        ],
        "PURCHASE": "NO",
        "REASON": "CASE B: 8-date sample is not a 1Y census; OG futures-front ATM rate 0/8; OG term 0/8; MVD-A has no bid/ask or official settle. This mission does not spend.",
    }

    for name, payload in (
        ("OPTION_DEFINITION_COVERAGE_V8_3.json", coverage),
        ("OPTION_FEASIBILITY_V8_3.json", feasibility),
        ("OPTION_MVD_SELECTION_V8_3.json", selection),
    ):
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        print("WROTE", path)

    print(json.dumps(occupancy, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
