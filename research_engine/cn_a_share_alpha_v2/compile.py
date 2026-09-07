"""Write V15 human reports from machine JSON. Does not overwrite the write-once plan."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share.paths import DOCS
from research_engine.cn_a_share_alpha_v2.paths import OUT


def _pct(x, digits=2):
    if x is None:
        return "n/a"
    return ("%." + str(digits) + "f%%") % (100.0 * float(x))


def _num(x, digits=4):
    if x is None:
        return "n/a"
    return ("%." + str(digits) + "f") % float(x)


def _md(name, body):
    path = os.path.join(DOCS, name)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write(body)
        if not body.endswith("\n"):
            handle.write("\n")
    finally:
        handle.close()


def _table(hyps):
    lines = [
        "| ID | Family | L | H | Val MEAN_FORWARD_RETURN | Res cap | Val cap | Val CAGR | FDR | L1 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for h in hyps:
        pv = h["predictive"]["validation"]
        cr = h["capital"]["research"]
        cv = h["capital"]["validation"]
        fam = h["family"].replace("CROSS_SECTIONAL_", "").replace("MARKET_", "").replace("PRICE_ACTIVITY_", "")
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                h["id"],
                fam,
                h["lookback"],
                h["hold_days"],
                _pct(pv.get("MEAN_FORWARD_RETURN"), 3),
                _pct(cr.get("total"), 2),
                _pct(cv.get("total"), 2),
                _pct(cv.get("CAGR"), 2),
                "Y" if h.get("fdr_discovery") else "N",
                "Y" if h.get("level1") else "N",
            )
        )
    return "\n".join(lines)


def _year_lines(years):
    if not years:
        return "(none)"
    rows = ["| Year | n | compound | mean period |", "|---|---|---|---|"]
    for y in sorted(years):
        rec = years[y]
        rows.append("| %s | %s | %s | %s |" % (y, rec.get("n"), _pct(rec.get("compound"), 2), _pct(rec.get("mean"), 3)))
    return "\n".join(rows)


def compile_v15():
    d = load_json(os.path.join(OUT, "DECISION.json"))
    res = load_json(os.path.join(OUT, "RESULTS.json"))
    fail = load_json(os.path.join(OUT, "FAILURES.json"))
    fdr = load_json(os.path.join(OUT, "FDR.json"))
    cl = load_json(os.path.join(OUT, "CLUSTER.json"))
    bench = load_json(os.path.join(OUT, "BENCHMARKS.json"))
    contract = load_json(os.path.join(OUT, "CONTRACT.json"))
    hyps = res["hypotheses"]
    table = _table(hyps)
    by_id = dict((h["id"], h) for h in hyps)
    h24 = by_id["H24_DISP_HIGH_RESID_20_H20"]
    h21 = by_id["H21_RESID_REV_20_H20"]

    _md(
        "A_SHARE_ALPHA_V2_REPORT.md",
        "\n".join(
            [
                "# A-share Alpha V2 Report",
                "",
                "Decision: **%s**. New Level-1 candidates: **%s**." % (d.get("OVERALL"), d.get("NEW_CANDIDATE")),
                "",
                "Contract hash: `%s`." % contract.get("contract_hash"),
                "Dataset: `%s` / `%s`." % (contract.get("dataset_id"), contract.get("dataset_hash")),
                "H11/H12: KEEP_LOW_PRIORITY. No reopen. No H13. No tenth hypothesis. Final OOS DENIED. Purchase = FALSE.",
                "",
                "## Dual books",
                "",
                "Predictive column is overlapping H-day filled open-to-open minus one round-trip. Name: **MEAN_FORWARD_RETURN**. It is not CAGR.",
                "Capital columns are non-overlapping 1/N books. Only those curves may be called CAGR.",
                "",
                table,
                "",
                "## Benchmarks (MEAN_FORWARD_RETURN, not CAGR)",
                "",
                "Hold 20 research: %s. Hold 20 validation: %s."
                % (
                    _pct(bench["20"]["research"]["MEAN_FORWARD_RETURN"], 3),
                    _pct(bench["20"]["validation"]["MEAN_FORWARD_RETURN"], 3),
                ),
                "Hold 5 research: %s. Hold 5 validation: %s."
                % (
                    _pct(bench["5"]["research"]["MEAN_FORWARD_RETURN"], 3),
                    _pct(bench["5"]["validation"]["MEAN_FORWARD_RETURN"], 3),
                ),
                "",
                "Validation EW was itself negative. Several hypotheses beat EW (FDR) and still lost money on the capital book. That is the V14.1 gap, not a hidden edge.",
                "",
                "## Closest miss",
                "",
                "H24 (dispersion-high residual-reversal): validation MEAN_FORWARD_RETURN %s, research capital %s, validation capital %s, FDR pass, evidence 2/2. Failed only `validation_capital`. Predictive corr vs H11 = %s. Not independent. Not a Candidate."
                % (
                    _pct(h24["predictive"]["validation"].get("MEAN_FORWARD_RETURN"), 3),
                    _pct(h24["capital"]["research"].get("total"), 2),
                    _pct(h24["capital"]["validation"].get("total"), 2),
                    _num((h24.get("corr_vs_low_vol") or {}).get("H11_VOL_60", {}).get("predictive"), 3),
                ),
                "",
                "H21 residual-reversal 20/20 predictive corr vs H11 = %s (SAME_CLUSTER if it had passed)."
                % _num((h21.get("corr_vs_low_vol") or {}).get("H11_VOL_60", {}).get("predictive"), 3),
                "",
            ]
        ),
    )

    profit = [
        "# A-share Alpha V2 Profitability",
        "",
        "CAGR / MaxDD / Sharpe below are **capital-account only**. Predictive means stay named MEAN_FORWARD_RETURN.",
        "",
        table,
        "",
    ]
    for h in hyps:
        cr = h["capital"]["research"]
        cv = h["capital"]["validation"]
        conc = h.get("concentration") or {}
        stock = conc.get("stock") or {}
        profit.extend(
            [
                "## %s" % h["id"],
                "",
                "- Research capital total %s, CAGR %s, MaxDD %s, Sharpe %s, unfilled %s."
                % (
                    _pct(cr.get("total"), 2),
                    _pct(cr.get("CAGR"), 2),
                    _pct(cr.get("maxdd"), 2),
                    _num(cr.get("sharpe"), 3),
                    _pct(cr.get("unfilled_rate"), 2),
                ),
                "- Validation capital total %s, CAGR %s, MaxDD %s, Sharpe %s, unfilled %s."
                % (
                    _pct(cv.get("total"), 2),
                    _pct(cv.get("CAGR"), 2),
                    _pct(cv.get("maxdd"), 2),
                    _num(cv.get("sharpe"), 3),
                    _pct(cv.get("unfilled_rate"), 2),
                ),
                "- Rank IC research / validation: %s / %s."
                % (
                    _num(h["predictive"]["research"].get("rank_ic"), 4),
                    _num(h["predictive"]["validation"].get("rank_ic"), 4),
                ),
                "- Stock profit top 1%% / 5%% / 10%% of positive names: %s / %s / %s. No AUM claim. trade/ADV not a gate."
                % (
                    _pct(stock.get("top_1_of_pos"), 1),
                    _pct(stock.get("top_5_of_pos"), 1),
                    _pct(stock.get("top_10_of_pos"), 1),
                ),
                "",
                "Validation capital years:",
                "",
                _year_lines(cv.get("years")),
                "",
            ]
        )
    _md("A_SHARE_ALPHA_V2_PROFITABILITY.md", "\n".join(profit))

    fdr_lines = [
        "# A-share Alpha V2 FDR",
        "",
        "BH q = 0.05. All 9 onesided validation **excess vs EW** p-values entered the ledger. No silent extra tests.",
        "",
        "| ID | onesided p | BH adj p | discovery |",
        "|---|---|---|---|",
    ]
    for h in hyps:
        fdr_lines.append(
            "| %s | %s | %s | %s |"
            % (h["id"], h.get("onesided_p"), h.get("fdr_adj_p"), h.get("fdr_discovery"))
        )
    fdr_lines.extend(
        [
            "",
            "Discoveries (0-based indices): %s." % (fdr.get("discoveries"),),
            "",
            "FDR here tests excess vs a losing EW book. A discovery is not a Candidate and is not CAGR.",
            "H23 / H27 / H28 did not discover. H21 / H22 / H24 / H25 / H26 / H29 did — and still failed capital gates.",
            "",
            "Bootstrap / cost-stress / permutation: not run. Those fire only on Level-1 positives. Count = 0.",
            "",
        ]
    )
    _md("A_SHARE_ALPHA_V2_FDR.md", "\n".join(fdr_lines))

    fail_lines = [
        "# A-share Alpha V2 Failures",
        "",
        "n = %s / 9. Reopen = new contract only. Do not flip sign. Do not retune lookback / hold / quantile." % fail.get("n"),
        "",
    ]
    for r in fail.get("rows") or []:
        fail_lines.extend(
            [
                "## %s" % r["id"],
                "",
                "- Family: %s" % r["family"],
                "- Mechanism: %s" % r["mechanism"],
                "- Why failed: %s" % ", ".join(r.get("why_failed") or []),
                "- Reopen: %s" % r.get("reopen"),
                "",
            ]
        )
    _md("A_SHARE_ALPHA_V2_FAILURES.md", "\n".join(fail_lines))

    qs = [
        "1. New Candidate? **NO**.",
        "2. How many? **0**.",
        "3. Independent of H11/H12? No new Candidate. Residual / disagreement-corr tracks LOW_VOL (predictive corr ≈ 0.90–0.94). Dispersion states thin the book; predictive corr still ≈ 0.91.",
        "4. Research capital positive? Some (H21/H22/H24/H26/H29). Not a Candidate without validation capital.",
        "5. Validation capital positive? **NO for all 9.**",
        "6. Real CAGR? None official. Closest miss H24 research CAGR %s; validation CAGR %s."
        % (_pct(h24["capital"]["research"].get("CAGR"), 2), _pct(h24["capital"]["validation"].get("CAGR"), 2)),
        "7. MaxDD? H24 research %s (2015-12-28 → 2018-10-24). Validation %s."
        % (_pct(h24["capital"]["research"].get("maxdd"), 1), _pct(h24["capital"]["validation"].get("maxdd"), 1)),
        "8. Sharpe? H24 research %s; validation %s."
        % (_num(h24["capital"]["research"].get("sharpe"), 3), _num(h24["capital"]["validation"].get("sharpe"), 3)),
        "9. Rank IC? H24 research %s; validation %s."
        % (
            _num(h24["predictive"]["research"].get("rank_ic"), 4),
            _num(h24["predictive"]["validation"].get("rank_ic"), 4),
        ),
        "10. FDR? 6/9 discoveries on excess-vs-EW. 0/9 Level 1.",
        "11. Profit concentration? Typical top 10% of positive names ≈ 50–70% of positive stock PnL. Left tail remains.",
        "12. Year stability? 2015 large; 2011/2017/2018 drawdowns. Validation 2023 often the killer year. Years are diagnostic, not a selector.",
        "13. Cost sensitivity? Not run (no Level-1). 5-day hold H23 already dies at 1x — turnover, not a cheaper model.",
        "14. Capacity? Unfilled 0.3–3%. No AUM announced. trade/ADV is not a gate.",
        "15. PIT clean? **YES** — same frozen listed/ST/eligibility rules. No live API.",
        "16. External data? **NO**. NEW_PURCHASE = FALSE. Databento ≈ $93 remains reserve. Options not bought.",
        "17. Strategy construction? **NO**. No new Candidate. Do not build a portfolio from H11/H12 + failed V15 rows.",
    ]
    _md(
        "A_SHARE_ALPHA_V2_DECISION.md",
        "\n".join(
            [
                "# A-share Alpha V2 Decision",
                "",
                "**%s**" % d.get("OVERALL"),
                "",
                "NEXT = `%s`" % d.get("NEXT"),
                "",
                "```",
                "LEVEL = %s" % d.get("LEVEL"),
                "EXISTING_CANDIDATE = %s" % d.get("EXISTING_CANDIDATE"),
                "NEW_CANDIDATE = %s" % d.get("NEW_CANDIDATE"),
                "CANDIDATE = %s" % d.get("CANDIDATE"),
                "STRATEGY = %s" % d.get("STRATEGY"),
                "PORTFOLIO = %s" % d.get("PORTFOLIO"),
                "```",
                "",
                "H11/H12 remain KEEP_LOW_PRIORITY. Do not reopen. Do not retune. Do not Long Validate.",
                "Do not flip signs. Do not add a tenth hypothesis. Final OOS DENIED. Purchase = FALSE.",
                "",
                "Cluster diagnostic (not a portfolio): %s" % cl.get("tags"),
                "",
                "## Questions",
                "",
                "\n".join(qs),
                "",
            ]
        ),
    )

    _md(
        "A_SHARE_PRICE_ALPHA_REVIEW_V2.md",
        "\n".join(
            [
                "# A-share Price Alpha Review V2",
                "",
                "Written because V15 finished **9/9 fail**. This is a review, not a new search. No purchase.",
                "",
                "## What price-only has already shown",
                "",
                "- V13: one mechanism family survived Level 1 — low volatility (H11/H12). Same cluster, corr ≈ 0.996.",
                "- V14 / V14.1: that cluster is a **real weak Candidate** and **not capital-ready**. Predictive mean ≠ CAGR.",
                "- V15: three new families, nine pre-registered hypotheses, dual books, BH-FDR on all nine.",
                "- V15 result: **NO_NEW_CANDIDATE**. Validation capital negative for every hypothesis.",
                "",
                "## Is the price-only universe exhausted?",
                "",
                "**Independent second alpha: yes, this panel is marginally exhausted.**",
                "",
                "Not the same as “no cross-sectional structure.” Residual-reversal still beats EW in validation (FDR) and still correlates 0.90+ with H11/H12. That is the same low-vol / defensive CS cluster under another name, not Alpha B.",
                "",
                "Dispersion states are a switch on residual-reversal, not a new sleeve. Capitulation (price down + amount up) failed sign/IC. Price–amount correlation also tracks LOW_VOL (predictive corr ≈ 0.93).",
                "",
                "A 5-day hold (H23) is killed by cost at 1x. Do not search cheaper costs.",
                "",
                "## What this does **not** authorize",
                "",
                "- No H13 / H30 / lookback 120–250 / quantile retune / sign flip.",
                "- No Long Validation of H11/H12 or of H24.",
                "- No official portfolio.",
                "- No ML (V10 already FDR 0/62).",
                "- No live API. No Tushare / Wind / Choice / CSMAR / Databento / options buy.",
                "- No unlocking FINANCIAL / INDUSTRY / EVENT in this review.",
                "",
                "## Decision of the review",
                "",
                "`PRICE_ONLY_INDEPENDENT_ALPHA_MARGINALLY_EXHAUSTED`",
                "",
                "Keep H11/H12 as LOW_PRIORITY Candidates. Keep Strategy WEAK. Do not optimize them into 10%.",
                "Do not buy the $93 reserve to rescue a second price-only CS factor.",
                "A new information set requires a new contract and a human unlock. That is not this task.",
                "",
            ]
        ),
    )
    print("COMPILE_V15", d.get("OVERALL"), d.get("NEXT"), flush=True)
    return d


if __name__ == "__main__":
    compile_v15()
