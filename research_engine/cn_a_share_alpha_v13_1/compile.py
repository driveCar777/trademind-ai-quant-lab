"""V13.1 reports from machine JSON."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share_alpha_v13_1.paths import DOCS_DIR, OUT


def _md(name, lines):
    path = os.path.join(DOCS_DIR, name)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write("\n".join(lines).rstrip() + "\n")
    finally:
        handle.close()


def compile_v13_1():
    d = load_json(os.path.join(OUT, "DECISION.json"))
    h11 = load_json(os.path.join(OUT, "H11_REPRODUCTION.json"))
    h12 = load_json(os.path.join(OUT, "H12_REPRODUCTION.json"))
    _md(
        "A_SHARE_CANDIDATE_REPRODUCTION_V13_1.md",
        [
            "# Candidate reproduction V13.1",
            "",
            "H11 status: **%s**" % h11.get("status"),
            "H12 status: **%s**" % h12.get("status"),
            "",
            "- H11 match original: %s  determinism: %s  path B: %s"
            % (h11.get("match_original"), h11.get("determinism"), h11.get("path_b_agrees")),
            "- H12 match original: %s  determinism: %s  path B: %s"
            % (h12.get("match_original"), h12.get("determinism"), h12.get("path_b_agrees")),
            "- H11 val net Path A: %s original: %s" % (h11.get("gate", {}).get("validation_mean_net"), h11.get("original_validation_mean_net")),
            "- H12 val net Path A: %s original: %s" % (h12.get("gate", {}).get("validation_mean_net"), h12.get("original_validation_mean_net")),
        ],
    )
    _md(
        "A_SHARE_CANDIDATE_ROBUSTNESS_V13_1.md",
        [
            "# Candidate robustness V13.1",
            "",
            "- H11 years: %s" % h11.get("years"),
            "- H12 years: %s" % h12.get("years"),
            "- H11 regime: %s" % h11.get("regime"),
            "- H12 regime: %s" % h12.get("regime"),
            "- H11 bootstrap: %s" % h11.get("bootstrap"),
            "- H12 permutation p: %s" % h12.get("permutation_p_ge_obs"),
            "- Denied window not used: %s" % h11.get("denied_years_not_used"),
        ],
    )
    _md(
        "A_SHARE_CANDIDATE_CONCENTRATION_V13_1.md",
        [
            "# Candidate concentration V13.1",
            "",
            "- H11 stock: %s" % h11.get("concentration", {}).get("stock"),
            "- H12 stock: %s" % h12.get("concentration", {}).get("stock"),
            "- H11 time: %s" % h11.get("concentration", {}).get("time_overlapping_val"),
            "- H12 time: %s" % h12.get("concentration", {}).get("time_overlapping_val"),
            "- H11 breadth: %s" % h11.get("breadth"),
            "- H12 breadth: %s" % h12.get("breadth"),
            "- H11 liquidity: %s" % h11.get("liquidity"),
        ],
    )
    _md(
        "A_SHARE_CANDIDATE_COST_AUDIT_V13_1.md",
        [
            "# Candidate cost audit V13.1",
            "",
            "- H11 cost: %s" % h11.get("cost"),
            "- H12 cost: %s" % h12.get("cost"),
            "- H11 stress: %s" % h11.get("cost_stress"),
            "- H12 stress: %s" % h12.get("cost_stress"),
            "- Zero-cost is diagnostic only.",
        ],
    )
    _md(
        "A_SHARE_CANDIDATE_DECISION_V13_1.md",
        [
            "# Candidate decision V13.1",
            "",
            "```",
            "H11 = %s" % d.get("H11"),
            "H12 = %s" % d.get("H12"),
            "LEVEL = %s" % d.get("LEVEL"),
            "CANDIDATE = %s" % d.get("CANDIDATE"),
            "NEXT = %s" % d.get("NEXT"),
            "FINAL_OOS = DENIED",
            "STRATEGY = FALSE",
            "```",
            "",
            "1. H11 independent repro: %s" % h11.get("path_b_agrees"),
            "2. H12 independent repro: %s" % h12.get("path_b_agrees"),
            "3. Research still +: %s / %s" % (h11.get("gate", {}).get("research_mean_net"), h12.get("gate", {}).get("research_mean_net")),
            "4. Validation still +: %s / %s" % (h11.get("gate", {}).get("validation_mean_net"), h12.get("gate", {}).get("validation_mean_net")),
            "5. Cost-adjusted +: same as 3-4",
            "6. Rank IC: %s / %s" % (h11.get("gate", {}).get("validation_rank_ic"), h12.get("gate", {}).get("validation_rank_ic")),
            "7. Historical FDR: %s / %s" % (h11.get("gate", {}).get("historical_fdr_discovery"), h12.get("gate", {}).get("historical_fdr_discovery")),
            "8. Stock concentration: see concentration report",
            "9. Day concentration: see concentration report",
            "10. Year concentration: see years",
            "11. Capacity: diagnostic only",
            "12. Beta/liquidity: %s" % h11.get("beta"),
            "13. PIT: %s" % h11.get("pit"),
            "14. CA limitation: raw close ranking",
            "15. Suspension fills: %s / %s" % (h11.get("execution", {}).get("suspended_fills"), h12.get("execution", {}).get("suspended_fills")),
            "16. Hold 20: %s" % h11.get("execution", {}).get("hold_days_locked"),
            "17. H11: %s" % d.get("H11"),
            "18. H12: %s" % d.get("H12"),
            "19. Next if survive: STRATEGY_CONSTRUCTION (not started)",
            "20. If failed: see status fields. Do not retune.",
        ],
    )
    print("COMPILE_V13_1", d.get("NEXT"), flush=True)
    return d
