"""Assemble the machine gap report. Not a blog post."""
from __future__ import print_function

from research_engine.forensics.failure_analyzer import analyze
from research_engine.forensics.search_space_coverage import coverage_summary, coverage_table
from research_protocol.hashing import canonical_hash


def build_report():
    families = analyze()
    coverage = coverage_table()
    codes = {}
    for row in families:
        for code in row.get("codes") or []:
            codes[code] = codes.get(code, 0) + 1
    dominant = None
    if codes:
        dominant = sorted(codes.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    payload = {
        "program_id": "ALPHA_GAP_REPORT_V1",
        "FINAL_OOS_TOUCHED": False,
        "coverage_pct": coverage_summary(),
        "coverage": coverage,
        "families": families,
        "code_counts": codes,
        "dominant_code": dominant,
        "reading": {
            "A": "no usable predictive information in the object tested",
            "B": "a statistical fragment exists but cost/friction removes the book",
            "C": "timescale or occupancy is wrong",
            "D": "required data was never present",
            "E": "the tested expression was the wrong object for a nearby idea",
        },
        "search_space_why_empty": (
            "Direction and state-level price rules were exhausted. "
            "The two new families (delta-state, residual) also failed after cost. "
            "Untested slots that still have on-disk data are institutional time and "
            "realized-vol term structure / volume-return divergence. "
            "IV, carry, news remain D."
        ),
    }
    payload["content_hash"] = canonical_hash(
        {"coverage": payload["coverage_pct"], "codes": codes, "families": [r["family"] for r in families]}
    )
    return payload
