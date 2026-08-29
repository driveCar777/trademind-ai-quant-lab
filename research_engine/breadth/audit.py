"""Post-run audit. No param change. No OOS."""
from __future__ import print_function

from research_engine.breadth.rank import rank_program
from research_engine.breadth.space import canonical_search_space_hash


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
        "book_pass": ranking.get("book_pass"),
        "fdr_pass": ranking.get("fdr_pass"),
        "FINAL_OOS_TOUCHED": False,
        "lookback_changed": False,
        "hold_changed": False,
        "sign_flipped_to_us500": False,
    }
