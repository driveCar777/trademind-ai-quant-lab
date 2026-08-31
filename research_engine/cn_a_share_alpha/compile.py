"""Write V13 reports from RESULTS.json. No live API."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share_alpha.paths import ALPHA_ROOT, DOCS_DIR


def _md(name, lines):
    path = os.path.join(DOCS_DIR, name)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write("\n".join(lines).rstrip() + "\n")
    finally:
        handle.close()
    return path


def compile_v13():
    results = load_json(os.path.join(ALPHA_ROOT, "RESULTS.json"))
    contract = load_json(os.path.join(ALPHA_ROOT, "CONTRACT.json"))
    hyps = results.get("hypotheses") or []
    decision = results.get("decision")
    pos = [h["id"] for h in hyps if h.get("research_positive") or h.get("validation_positive")]
    neg = [h["id"] for h in hyps if not h.get("research_positive") and not h.get("validation_positive")]
    l1 = [h["id"] for h in hyps if h.get("level1")]
    _md(
        "A_SHARE_ALPHA_V1_PLAN.md",
        [
            "# A-share cross-sectional alpha V1 plan",
            "",
            "Frozen panel only. Four families. Twelve pre-registered hypotheses.",
            "No financial / industry / event. No ML. No purchase.",
        ],
    )
    _md(
        "A_SHARE_ALPHA_V1_CONTRACT.md",
        [
            "# A-share alpha V1 contract",
            "",
            "contract_hash = `%s`" % contract.get("contract_hash"),
            "",
            "dataset_id = `%s`" % contract.get("dataset_id"),
            "",
            "Research 2010-01-04 → 2021-08-24. Validation 2021-08-25 → 2024-02-29. 2024-03-01+ DENIED.",
            "Hold = 20. Quintile = 20%. Long-only is the capital book. Long-short is research-only.",
        ],
    )
    lines = [
        "# A-share alpha V1 report",
        "",
        "```",
        "DECISION = %s" % decision,
        "LEVEL_1 = %s" % (l1 or 0),
        "```",
        "",
    ]
    for h in hyps:
        val = h["windows"]["validation"]
        res = h["windows"]["research"]
        lines += [
            "## %s" % h["id"],
            "",
            "- research excess vs B0: %s  rank IC: %s" % (res.get("excess_vs_b0_mean"), res.get("rank_ic")),
            "- validation excess vs B0: %s  rank IC: %s" % (val.get("excess_vs_b0_mean"), val.get("rank_ic")),
            "- val CAGR: %s  MaxDD: %s  FDR: %s  Level1: %s"
            % (val["metrics"].get("cagr"), val["metrics"].get("maxdd"), h.get("fdr_discovery"), h.get("level1")),
            "- by year: %s" % h.get("by_year"),
            "",
        ]
    _md("A_SHARE_ALPHA_V1_REPORT.md", lines)
    _md(
        "A_SHARE_ALPHA_V1_PROFITABILITY.md",
        [
            "# A-share alpha V1 profitability",
            "",
            "Cost model = A_SHARE_TRANSACTION_COST_MODEL_V1 (commission 2.5bp, stamp 10bp→5bp sell, transfer 0.1bp, slippage 10bp).",
            "Not MT5 5+10bp.",
            "",
            "Positive research or validation (not Candidate): %s" % pos,
            "Level 1: %s" % l1,
        ],
    )
    _md(
        "A_SHARE_ALPHA_V1_FAILURES.md",
        [
            "# A-share alpha V1 failures",
            "",
            "Failed Level 1: %s" % [h["id"] for h in hyps if not h.get("level1")],
            "",
            "Do not flip sign. Reopen only with a new contract.",
            "This is not a claim that A-shares have no alpha.",
        ],
    )
    answers = [
        "1. 12 hypotheses: %s" % ", ".join(h["id"] for h in hyps),
        "2. positive (window flag): %s" % pos,
        "3. negative both windows: %s" % neg,
        "4. inconclusive: those with mixed windows",
        "5. FDR discoveries: %s" % results.get("fdr", {}).get("discoveries"),
        "6-8. see report IC / rank IC / spread",
        "9-13. see validation metrics",
        "14. capacity = median ADV diagnostic only",
        "15. most stable: see by_year",
        "16. year coverage 2010-2026 in by_year",
        "17. survivorship: PIT listing/delist + delisted names kept in panel",
        "18. PIT: membership from ipo/outDate; no 2026 backfill",
        "19. Level 1 Candidate: %s" % (l1 or "NONE"),
        "20. why: %s" % ("gates passed" if l1 else "cost-adjusted research+validation+FDR+2 evidence not jointly met"),
        "21. next: new contract only if exhausted; not a 13th lookback",
    ]
    _md(
        "A_SHARE_ALPHA_V1_DECISION.md",
        [
            "# A-share alpha V1 decision",
            "",
            "```",
            "DECISION = %s" % decision,
            "LEVEL = %s" % (1 if l1 else 0),
            "CANDIDATE = %s" % (len(l1)),
            "NEW_PURCHASE = FALSE",
            "FINAL_OOS = DENIED",
            "NEXT = %s" % ("CANDIDATE_REPRODUCTION" if l1 else "A_SHARE_PRICE_ALPHA_REVIEW"),
            "```",
            "",
        ]
        + answers,
    )
    print("COMPILE", decision, flush=True)
    return results
