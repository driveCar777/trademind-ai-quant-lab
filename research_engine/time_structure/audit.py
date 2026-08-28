"""Post-run audit. No param change. No OOS."""
from __future__ import print_function

from research_engine.time_structure.rank import rank_program
from research_engine.time_structure.space import canonical_search_space_hash


def audit_rows(rows, search_space_hash):
    locked = canonical_search_space_hash()
    if search_space_hash != locked:
        raise RuntimeError("CONTRACT_MISMATCH")
    ranking = rank_program(rows)
    outcome = ranking.get("outcome")
    return {
        "search_space_hash": search_space_hash,
        "outcome": outcome,
        "candidate": outcome == "CANDIDATE",
        "fdr": ranking.get("fdr"),
        "gold_pass": ranking.get("gold_pass"),
        "oil_pass": ranking.get("oil_pass"),
        "FINAL_OOS_TOUCHED": False,
        "tokyo_used": False,
        "hold_changed": False,
        "weekday_used": False,
    }
