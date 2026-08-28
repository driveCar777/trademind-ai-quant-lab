"""Information Gap Matrix loader. Index IV is not an option surface."""
from __future__ import print_function

from research_engine.data_expansion.paths import expansion_dir, load_json

REQUIRED_GAP_FIELDS = (
    "source",
    "mechanism",
    "currently_available",
    "currently_tested",
    "data_required",
    "historical_depth_required",
    "timestamp_requirement",
    "lookahead_risk",
    "economic_plausibility",
    "expected_edge_type",
)


def gap_matrix():
    return load_json(expansion_dir(), "INFORMATION_GAP_MATRIX_V2.json")


def gap_row(source_id):
    for row in gap_matrix().get("rows") or []:
        if row.get("id") == source_id or row.get("source") == source_id:
            return row
    return None


def assert_index_iv_not_surface():
    row = gap_row("GAP-OPTION-SURFACE")
    if not row:
        raise ValueError("missing GAP-OPTION-SURFACE")
    if row.get("currently_tested") is True:
        raise ValueError("option surface must not be marked tested because GVZ/OVX ran")
    note = str(row.get("note") or "")
    if "index IV" not in note and "GVZ" not in note:
        raise ValueError("surface row must distinguish index IV from underlying options")


def assert_physical_not_all_failed():
    row = gap_row("GAP-PHYSICAL-FLOW")
    if not row:
        raise ValueError("missing GAP-PHYSICAL-FLOW")
    if row.get("all_physical_failed") is True:
        raise ValueError("EIA stocks failure is not all physical data")
