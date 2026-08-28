from research_engine.alt_market_structure.rank import rank_program
from research_engine.alt_market_structure.space import canonical_search_space_hash


def audit_rows(rows, search_space_hash):
    if search_space_hash != canonical_search_space_hash():
        raise RuntimeError("CONTRACT_MISMATCH")
    ranking = rank_program(rows)
    return {
        "search_space_hash": search_space_hash,
        "outcome": ranking.get("outcome"),
        "candidate": ranking.get("outcome") == "CANDIDATE",
        "fdr": ranking.get("fdr"),
        "FINAL_OOS_TOUCHED": False,
        "z_cut_changed": False,
        "fd_level_reused": False,
    }
