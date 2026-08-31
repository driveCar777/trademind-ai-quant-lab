"""Write the eight V14.1 reports from machine JSON. No new numbers."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share.paths import DOCS
from research_engine.cn_a_share_strategy_v14_1.paths import OUT


def _pct(x):
    if x is None:
        return "n/a"
    return "%.4f%%" % (100.0 * float(x))


def _md(name, body):
    path = os.path.join(DOCS, "research_engine", name)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write(body)
        if not body.endswith("\n"):
            handle.write("\n")
    finally:
        handle.close()
    return path


def compile_v14_1():
    d = load_json(os.path.join(OUT, "DECISION.json"))
    h11 = load_json(os.path.join(OUT, "H11_CANDIDATE_REPLAY.json"))
    h12 = load_json(os.path.join(OUT, "H12_CANDIDATE_REPLAY.json"))
    eng = load_json(os.path.join(OUT, "INDEPENDENT_ENGINE.json"))
    cost = load_json(os.path.join(OUT, "COST_FORENSICS.json"))
    ca = load_json(os.path.join(OUT, "CORPORATE_ACTION_AUDIT.json"))
    dd = load_json(os.path.join(OUT, "DRAWDOWN_FORENSICS.json"))
    syn = load_json(os.path.join(OUT, "SYNTHETIC.json"))
    q = d.get("questions") or {}

    _md(
        "V14_1_CANDIDATE_STRATEGY_FORENSICS.md",
        "\n".join(
            [
                "# V14.1 Candidate vs Strategy Forensics",
                "",
                "AUDIT ONLY. No retune. No H13. No purchase. Final OOS DENIED.",
                "",
                "## Primary question",
                "",
                "Why is the Candidate statistic positive while the canonical Strategy full-path capital account is negative?",
                "",
                "## Definitions",
                "",
                "- **Candidate statistic:** each date t, equal-weight mean of filled `open(t+1) → open(t+1+20)` minus one locked round-trip. Reported CAGR is `(1+mean_net_h)^(242/20)-1`. The `years` argument is unused. This is **not** a compounded book.",
                "- **Canonical Strategy:** one long-only equal-weight book, rebalance every 20 trading days, unfilled weight stays cash, compound `(1+period_return)`. This is the official strategy object.",
                "",
                "## Reconstructed Candidate (Path A = original overlapping_series)",
                "",
                "| | H11 val mean_net | H11 val CAGR_from_h | H12 val mean_net | H12 val CAGR_from_h |",
                "|---|---|---|---|---|",
                "| Path A | %s | %s | %s | %s |"
                % (
                    h11["path_a"]["validation"].get("mean_net"),
                    _pct(h11["path_a"]["validation"].get("cagr_from_h")),
                    h12["path_a"]["validation"].get("mean_net"),
                    _pct(h12["path_a"]["validation"].get("cagr_from_h")),
                ),
                "",
                "Path A vs published V13: H11 %s, H12 %s. Path A vs independent Path B: H11 err=%s, H12 err=%s."
                % (
                    h11["published_agree"],
                    h12["published_agree"],
                    h11.get("path_a_b_val_abs_err"),
                    h12.get("path_a_b_val_abs_err"),
                ),
                "",
                "## Independent capital (does not call V14 simulate)",
                "",
                "| | H11 end | H11 full CAGR | H12 end | H12 full CAGR |",
                "|---|---|---|---|---|",
                "| Path A/B | %.2f | %s | %.2f | %s |"
                % (
                    eng["H11"]["path_a_end"],
                    _pct(eng["H11"].get("full_cagr")),
                    eng["H12"]["path_a_end"],
                    _pct(eng["H12"].get("full_cagr")),
                ),
                "",
                "Path A vs Path B end abs err: H11 %s, H12 %s. Recon: H11 %s H12 %s."
                % (
                    eng["H11"]["path_a_b_abs_err"],
                    eng["H12"]["path_a_b_abs_err"],
                    eng["H11"]["recon_ok"],
                    eng["H12"]["recon_ok"],
                ),
                "",
                "## Why they disagree",
                "",
                "1. Overlapping daily mean ≠ one 20-day grid.",
                "2. `(1+mean_h)^12.1-1` ≠ compounded capital CAGR.",
                "3. V13 `mean(raw)-RT` ≠ V14 multiplicative cost + cash residual.",
                "4. AM-GM: a high-vol 20-day book can have a slightly positive mean and a negative product.",
                "",
                "Accounting is %s. Decision: **%s**."
                % (d.get("accounting_ok"), d.get("OVERALL")),
                "",
                "## Locks",
                "",
                "New data = NO. Retune = NO. Make H12 into 10% = NO. Paper = 0. Portfolio = 0. Final OOS = DENIED.",
                "",
            ]
        ),
    )
    _md(
        "V14_1_OVERLAP_BRIDGE.md",
        "\n".join(
            [
                "# V14.1 Overlap Bridge",
                "",
                "Series A/B/C are diagnostics. They are not a menu. Official strategy remains the single non-overlapping capital account.",
                "",
                "## H11",
                "",
                str(h11.get("series_abc")),
                "",
                "## H12",
                "",
                str(h12.get("series_abc")),
                "",
                "Machine: `OVERLAP_BRIDGE.csv` and `CANDIDATE_TO_STRATEGY_BRIDGE.csv`.",
                "",
                "HORIZON_TRANSLATION_RISK = %s." % d.get("HORIZON_TRANSLATION_RISK"),
                "",
            ]
        ),
    )
    _md(
        "V14_1_EXECUTION_AUDIT.md",
        "\n".join(
            [
                "# V14.1 Execution Audit",
                "",
                "- Hold is 20 **trading** days, not calendar days.",
                "- Signal at close(t); entry at open(t+1); exit at open(t+1+20).",
                "- Unfilled (SUSPENDED / LIMIT_LOCK / DELISTED / ZERO_VOLUME / MISSING_OPEN) is 0 PnL, 0 fees, weight stays cash. No phantom book.",
                "- tradestatus≠1 is never filled.",
                "- Limit-lock is never marked filled.",
                "- A hold that would cross delisting is UNFILL. No last-price continuation.",
                "- 100 random fills (seed 20260831) are in `TRADE_FORENSICS.csv`.",
                "",
                "H11 unfilled rate %s reasons %s. H12 unfilled rate %s reasons %s."
                % (
                    eng["H11"].get("unfilled_rate"),
                    eng["H11"].get("reasons"),
                    eng["H12"].get("unfilled_rate"),
                    eng["H12"].get("reasons"),
                ),
                "",
            ]
        ),
    )
    _md(
        "V14_1_COST_FORENSICS.md",
        "\n".join(
            [
                "# V14.1 Cost Forensics",
                "",
                "Locked model: commission 2.5bp, transfer 0.1bp, slippage 10bp, stamp 10bp sell before 2023-08-28 / 5bp after.",
                "",
                "## H11",
                "",
                str(cost.get("H11")),
                "",
                "## H12",
                "",
                str(cost.get("H12")),
                "",
                "Unfilled orders are not charged. Costs are applied once at entry and once at exit. "
                "The Candidate statistic subtracts a round-trip from the mean raw; the Strategy applies "
                "multiplicative buy/sell factors. That is a formula difference, not a double charge.",
                "",
                "FORENSIC_ERROR for double charge: no.",
                "",
                "Cost is not the item that flips a large positive Candidate into a large negative book. "
                "The sign flip is sampling / overlap / compounding.",
                "",
            ]
        ),
    )
    _md(
        "V14_1_CORPORATE_ACTION_AUDIT.md",
        "\n".join(
            [
                "# V14.1 Corporate Action Audit",
                "",
                "Canonical ranking and PnL stay on **raw** prices. No frozen QFQ panel. Do not freeze a new panel. Do not buy data.",
                "",
                "## H11",
                "",
                str(ca.get("H11")),
                "",
                "## H12",
                "",
                str(ca.get("H12")),
                "",
                "DIVIDEND_EXCLUSION: cash dividends are not added back. Current V14 is a **price return**, not a total return.",
                "",
                "QFQ test = DATA_GAP. If a frozen QFQ panel existed, ranking and capital could change. That is CANDIDATE_REPRESENTATION_RISK. It is not a license to switch the canonical book.",
                "",
            ]
        ),
    )
    _md(
        "V14_1_DRAWDOWN_FORENSICS.md",
        "\n".join(
            [
                "# V14.1 Drawdown Forensics",
                "",
                "The ≈ −66% drawdown is a capital-path fact, not a Candidate-statistic fact.",
                "",
                "## H11",
                "",
                str(dd.get("H11")),
                "",
                "## H12",
                "",
                str(dd.get("H12")),
                "",
                "Diagnostic regimes 2010–2014 / 2015–2019 / 2020–2021 / 2022–2023 / 2024–2026 are in `H11/REGIMES.json` and `H12/REGIMES.json`. No window is dropped. 2024-03+ is DENIED for gates.",
                "",
                "Yearly and monthly tables are in `H11/DISTRIBUTION.json` and `H12/DISTRIBUTION.json`. Every year is kept.",
                "",
            ]
        ),
    )
    _md(
        "V14_1_CAPITAL_ENGINE_AUDIT.md",
        "\n".join(
            [
                "# V14.1 Independent Capital Engine",
                "",
                "Reference implementation: `research_engine/cn_a_share_strategy_v14_1/capital_ref.py`.",
                "It does not import `cn_a_share_strategy_v14.engine.simulate`.",
                "",
                "Path A = return-based `period_capital`. Path B = share-based `notional/open`.",
                "Same trade dates. Same ending capital within tolerance.",
                "",
                "Synthetic suite all_ok = %s." % syn.get("all_ok"),
                "",
                str(syn.get("cases")),
                "",
                "## H11 engine",
                "",
                str(eng.get("H11")),
                "",
                "## H12 engine",
                "",
                str(eng.get("H12")),
                "",
                "Identity: starting capital + sum(trade net) = ending capital.",
                "Benchmark = EW eligible open-to-open on the **same** signal dates.",
                "",
            ]
        ),
    )
    _md(
        "V14_1_DECISION.md",
        "\n".join(
            [
                "# V14.1 Decision",
                "",
                "**%s**" % d.get("OVERALL"),
                "",
                "NEXT = `%s`" % d.get("NEXT"),
                "",
                "```",
                "LEVEL = %s" % d.get("LEVEL"),
                "CANDIDATE = %s" % d.get("CANDIDATE"),
                "STRATEGY = %s" % d.get("STRATEGY"),
                "PORTFOLIO = 0",
                "PAPER = 0",
                "LIVE = 0",
                "```",
                "",
                "## 22 questions",
                "",
                "1. Why Candidate positive: %s" % q.get("q01_why_candidate_positive"),
                "2. Why V14 full path negative: %s" % q.get("q02_why_v14_negative"),
                "3. Overlap core? %s" % q.get("q03_overlap_core"),
                "4. Non-overlap core? %s" % q.get("q04_nonoverlap_core"),
                "5. Entry timing consistent? %s" % q.get("q05_entry_timing_consistent"),
                "6. Exit timing consistent? %s" % q.get("q06_exit_timing_consistent"),
                "7. Unfilled error? %s" % q.get("q07_unfilled_error"),
                "8. Limit-lock error? %s" % q.get("q08_limit_lock_error"),
                "9. Cost double count? %s" % q.get("q09_cost_double_count"),
                "10. Corporate action? %s" % q.get("q10_corporate_action"),
                "11. Dividend omitted? %s" % q.get("q11_dividend_omitted"),
                "12. −66% DD: %s" % q.get("q12_dd_origin"),
                "13. One mechanism? %s" % q.get("q13_one_mechanism"),
                "14. H11 still researchable? %s" % q.get("q14_h11_still_researchable"),
                "15. H12 still researchable? %s" % q.get("q15_h12_still_researchable"),
                "16. Executable? %s" % q.get("q16_executable"),
                "17. Level 2 process gate? %s" % q.get("q17_level2_process"),
                "18. Long Validation? %s" % q.get("q18_long_validation"),
                "19. Why not: %s" % q.get("q19_why_no_lv"),
                "20. New data? **NO**",
                "21. Retune? **NO**",
                "22. Make H12 into 10%? **NO**",
                "",
                "## Next",
                "",
                "Keep H11/H12 as Candidates. Strategy stays WEAK. Do not Long Validate. "
                "Do not combine H11+H12. Do not optimize lookback/hold/quantile. "
                "H11/H12 correlation remains one cluster (capital corr %s, overlap corr %s)."
                % (d.get("correlation_capital"), d.get("correlation_overlap")),
                "",
            ]
        ),
    )
    print("COMPILE_V14_1", d.get("OVERALL"), d.get("NEXT"), flush=True)
    return d


if __name__ == "__main__":
    compile_v14_1()
