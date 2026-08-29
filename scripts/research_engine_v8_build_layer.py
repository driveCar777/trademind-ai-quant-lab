#!/usr/bin/env python3
"""Build V8 census, provenance, fusion, opportunity. No Databento network."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.io_util import dump_json
from research_engine.local_fs import force_project_temp
from research_engine.v8_fusion.census import build_census
from research_engine.v8_fusion.matrix import fusion_matrix
from research_engine.v8_fusion.opportunity import opportunity_v8
from research_engine.v8_fusion.provenance import provenance_catalog
from research_engine.v8_fusion.states import market_states


OUT = os.path.join(ROOT, "data", "market", "research_engine", "v8_fusion")


def main():
    force_project_temp()
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    census = build_census()
    dump_json(os.path.join(OUT, "DATA_ASSET_CENSUS_V8.json"), census)
    dump_json(os.path.join(OUT, "PROVENANCE_V8.json"), provenance_catalog())
    dump_json(os.path.join(OUT, "INFORMATION_FUSION_MATRIX_V8.json"), fusion_matrix())
    dump_json(os.path.join(OUT, "MARKET_INFORMATION_STATE_V8.json"), market_states())
    opp = opportunity_v8()
    dump_json(os.path.join(OUT, "ALPHA_OPPORTUNITY_V8.json"), opp)
    dump_json(
        os.path.join(OUT, "DATA_COST_LEDGER_V8.json"),
        {
            "catalog_id": "DATA_COST_LEDGER_V8",
            "this_mission_usd": 0,
            "pack_e_historical_usd": 31.816129,
            "credits_remaining_usd_estimate": 93.18,
            "credit_floor_usd": 60.0,
            "auto_purchase_max_usd": 30.0,
            "NO_NEW_PURCHASE": True,
        },
    )
    print(
        "V8_LAYER",
        "n",
        census.get("n_datasets"),
        "free",
        census.get("n_free"),
        "paid",
        census.get("n_paid"),
        "derived",
        census.get("n_derived"),
        "selected",
        opp.get("selected"),
    )
    for row in opp.get("top5") or []:
        guard = row.get("novelty_guard") or {}
        print("OPP", row.get("rank"), row.get("id"), guard.get("decision"), guard.get("why"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
