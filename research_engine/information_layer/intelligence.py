"""Answers: what was tested, what exists, what is still unused."""
from __future__ import print_function


def intelligence(inventory, preserve, catalog, fusion, opportunity, failed_n):
    return {
        "catalog_id": "RESEARCH_INTELLIGENCE_V7",
        "questions": {
            "what_was_tested": "28 killed families in FAILED_ALPHA_V2 including TERM_STRUCTURE_V1",
            "why_failed": "cost, occupancy/level-leak, wrong sign, sparse weekly events, CFD-only information",
            "what_data_exists": "%s frozen datasets; Pack E complete=%s"
            % (inventory.get("n_datasets"), (preserve or {}).get("complete")),
            "what_features_derived": [row.get("name") for row in (catalog.get("features") or [])],
            "what_is_untested": [
                "official OI x price flow",
                "cleared volume x price",
                "third-contract curvature",
                "curve + EIA/COT/UST10 fusion",
            ],
        },
        "n_failed_families": failed_n,
        "credits_remaining_usd_estimate": inventory.get("credits_remaining_usd_estimate"),
        "NO_NEW_PURCHASE": True,
        "FINAL_OOS_TOUCHED": False,
    }
