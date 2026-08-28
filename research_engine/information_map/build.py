"""Build ALPHA_INFORMATION_MAP_V1 from sources + forensics coverage."""
from __future__ import print_function

from research_engine.forensics.search_space_coverage import coverage_summary
from research_engine.information_map.sources import all_sources
from research_protocol.hashing import canonical_hash


def build_map():
    rows = all_sources()
    by_class = {}
    for row in rows:
        key = row["class"]
        by_class.setdefault(key, []).append(row["id"])
    payload = {
        "map_id": "ALPHA_INFORMATION_MAP_V1",
        "FINAL_OOS_TOUCHED": False,
        "coverage_pct": coverage_summary(),
        "n_sources": len(rows),
        "by_class": by_class,
        "sources": rows,
        "not_v08": True,
        "not_indicator_farm": True,
    }
    payload["content_hash"] = canonical_hash(
        {"ids": [r["id"] for r in rows], "coverage": payload["coverage_pct"]}
    )
    return payload
