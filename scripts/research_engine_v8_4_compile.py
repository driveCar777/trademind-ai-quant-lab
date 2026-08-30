# -*- coding: utf-8 -*-
"""Compile V8.4 census + sufficiency JSON from the partial checkpoint. No API."""
from __future__ import print_function

import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "market", "research_engine", "options")
PARTIAL = os.path.join(OUT, "OPTION_FULL_YEAR_CENSUS_PARTIAL_V8_4.json")


def main():
    raw = json.load(open(PARTIAL, encoding="utf-8"))
    if not raw.get("summary"):
        raise SystemExit("census not finished: no summary")
    census = {
        "catalog_id": "OPTION_FULL_YEAR_CENSUS_V8_4",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "downloaded": False,
        "purchased": False,
        "window": raw.get("window"),
        "n_days": len(raw.get("days") or []),
        "atm_rule": raw.get("atm_rule"),
        "active_option_month_rule": raw.get("active_option_month_rule"),
        "gates": raw.get("gates"),
        "monthly_parent_ohlcv": raw.get("monthly"),
        "summary": raw.get("summary"),
        "days": raw.get("days"),
        "phase_b_note": "Parent monthly counts mix C/P/spreads/UD. Outright C/P occupancy is the constructed ATM/OTM raw_symbol census only. Full chain outright count is UNKNOWN without definition download.",
        "dte_note": "Exact option expiration UNKNOWN without definition. Month code only.",
    }
    gc = raw["summary"]["GC"]
    cl = raw["summary"]["CL"]
    scores = {"GC": gc["score"], "CL": cl["score"]}
    # Prefer the only CASE A metal. If both A, gold IV-RV first. If both B, gold IV-RV first.
    if cl["score"] == "A" and gc["score"] != "A":
        preferred = {
            "package": "LO_1Y_MVD-A",
            "cost_usd": 11.991718,
            "score": cl["score"],
            "why": "Only metal that meets locked gate A on the 251-day census",
        }
    elif gc["score"] in ("A", "B"):
        preferred = {
            "package": "OG_1Y_MVD-A",
            "cost_usd": 14.994811,
            "score": gc["score"],
            "why": "Gold IV-RV first when OG meets A or when neither is uniquely A",
        }
    elif cl["score"] in ("A", "B"):
        preferred = {
            "package": "LO_1Y_MVD-A",
            "cost_usd": 11.991718,
            "score": cl["score"],
            "why": "LO meets B+ and OG does not",
        }
    else:
        preferred = None
    if preferred:
        purchase = "NO"
        reason = (
            "This mission does not spend. Data sufficiency is %s/%s (OG/LO). "
            "If a human later buys, single package is %s $%.2f."
            % (gc["score"], cl["score"], preferred["package"], preferred["cost_usd"])
        )
    else:
        purchase = "NO"
        reason = "OG and LO scores are C/D. Do not buy. Credits stay unused."
    sufficiency = {
        "catalog_id": "OPTION_RESEARCH_SUFFICIENCY_V8_4",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "not_an_alpha_gate": True,
        "gates_locked_before_counts": raw.get("gates"),
        "scores": scores,
        "detail": raw.get("summary"),
        "preferred_if_human_later": preferred,
        "this_mission_purchase": False,
        "PURCHASE": purchase,
        "REASON": reason,
        "limitations": [
            "MVD-A has no bid/ask",
            "MVD-A has no official option settlement",
            "MVD-A has no OI",
            "IV is DERIVED Black-76 not venue IV",
            "American early exercise",
            "Parent monthly counts include spreads/UD",
        ],
    }
    for name, payload in (
        ("OPTION_FULL_YEAR_CENSUS_V8_4.json", census),
        ("OPTION_RESEARCH_SUFFICIENCY_V8_4.json", sufficiency),
    ):
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        print("WROTE", path)
    print("SCORES", scores)
    print("PREFERRED", preferred)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
