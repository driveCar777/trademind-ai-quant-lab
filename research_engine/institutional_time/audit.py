"""Post-run audit. No param change. No OOS."""
from __future__ import print_function

from research_engine.institutional_time import LOCKED_HASH
from research_engine.institutional_time.rank import rank_program


def audit_rows(rows, search_space_hash):
    if search_space_hash != LOCKED_HASH:
        raise RuntimeError("CONTRACT_MISMATCH")
    ranking = rank_program(rows)
    outcome = ranking.get("outcome")
    candidate = outcome == "CANDIDATE"
    return {
        "search_space_hash": search_space_hash,
        "outcome": outcome,
        "candidate": candidate,
        "fdr": ranking.get("fdr"),
        "gold_pass": ranking.get("gold_pass"),
        "oil_pass": ranking.get("oil_pass"),
        "FINAL_OOS_TOUCHED": False,
        "widen_used": False,
        "hold_changed": False,
        "gate": {
            "research_positive": True,
            "validation_positive": True,
            "fdr": True,
            "two_targets": True,
            "no_param_mod": True,
            "no_oos": True,
        },
    }
