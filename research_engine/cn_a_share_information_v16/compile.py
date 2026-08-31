"""Write V16 human reports from machine JSON."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share.paths import DOCS
from research_engine.cn_a_share_information_v16.paths import OUT


def _md(name, body):
    path = os.path.join(DOCS, name)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write(body if body.endswith("\n") else body + "\n")
    finally:
        handle.close()


def _load(name):
    path = os.path.join(OUT, name)
    if not os.path.isfile(path):
        return {}
    return load_json(path)


def _pct(x):
    if x is None:
        return "n/a"
    return "%.2f%%" % (100.0 * float(x))


def compile_v16():
    d = _load("DECISION.json")
    fin_pit = _load("FINANCIAL_PIT.json")
    ind_pit = _load("INDUSTRY_PIT.json")
    ready = _load("READINESS.json")
    fin_res = _load("FINANCIAL_RESULTS.json")
    cand = _load("CANDIDATES.json")
    fail = _load("FAILURES.json")
    fdr = _load("FDR.json")
    audit = _load("SOURCE_AUDIT.json")
    cat = _load("FINANCIAL_CATALOG.json")
    hyps = fin_res.get("hypotheses") or []
    lines = ["| ID | Family | Val MEAN_FORWARD_RETURN | Res cap | Val cap | Val CAGR | FDR | L1 |", "|---|---|---|---|---|---|---|---|"]
    for h in hyps:
        pv = (h.get("predictive") or {}).get("validation") or {}
        cr = (h.get("capital") or {}).get("research") or {}
        cv = (h.get("capital") or {}).get("validation") or {}
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                h.get("id"),
                h.get("family"),
                _pct(pv.get("MEAN_FORWARD_RETURN")),
                _pct(cr.get("total")),
                _pct(cv.get("total")),
                _pct(cv.get("CAGR")),
                h.get("fdr_discovery"),
                h.get("level1"),
            )
        )
    table = "\n".join(lines) if hyps else "(no financial alpha run)"
    _md(
        "A_SHARE_FINANCIAL_PIT_V16.md",
        "\n".join(
            [
                "# A-share Financial PIT V16",
                "",
                "Knowledge time = `announcement_date`. report_period is not knowledge time.",
                "RESTATEMENT_RISK = TRUE. Complete PIT is not claimed.",
                "",
                "PIT test: %s. Coverage: %s. 2023 annual hidden on 2024-01-01: %s. 2022 visible: %s."
                % (fin_pit.get("pit_test_ok"), fin_pit.get("coverage_ok"), fin_pit.get("2023_annual_must_be_hidden"), fin_pit.get("2022_annual_visible")),
                "",
                "Rows: %s. Symbols: %s. Announcement rate: %s."
                % (cat.get("n_rows"), cat.get("n_symbols"), cat.get("announcement_rate")),
                "",
                "ROA = UNAVAILABLE. debt_ratio = UNAVAILABLE unless balance downloaded. EPS = vendor TTM, not period EPS.",
                "",
            ]
        ),
    )
    _md(
        "A_SHARE_INDUSTRY_PIT_V16.md",
        "\n".join(
            [
                "# A-share Industry PIT V16",
                "",
                "Status: **%s**." % (ind_pit.get("status") or "UNKNOWN"),
                "",
                "BaoStock `query_stock_industry` is CURRENT_ONLY. No effective_date. Do not backfill 2026 industry to 2010.",
                "HS300 date membership is not industry classification.",
                "INDUSTRY_ALPHA_READY = FALSE. No industry dataset freeze.",
                "",
            ]
        ),
    )
    _md(
        "A_SHARE_FINANCIAL_ALPHA_V16.md",
        "\n".join(
            [
                "# A-share Financial Alpha V16",
                "",
                table,
                "",
                "MEAN_FORWARD_RETURN is not CAGR.",
                "Candidates: %s" % (cand.get("ids"),),
                "",
            ]
        ),
    )
    _md(
        "A_SHARE_INDUSTRY_ALPHA_V16.md",
        "\n".join(
            [
                "# A-share Industry Alpha V16",
                "",
                "Not run. INDUSTRY_PIT_BLOCKED.",
                "",
            ]
        ),
    )
    _md(
        "A_SHARE_INFORMATION_VALUE_V16.md",
        "\n".join(
            [
                "# A-share Information Value V16",
                "",
                "Free BaoStock financials have announcement dates and can be joined PIT.",
                "Industry cannot. Event layer still BLOCKED.",
                "Purchase = FALSE. Databento / options / Tushare unused.",
                "",
                "Audit verdict: %s" % ((audit.get("verdict") if audit else None),),
                "",
            ]
        ),
    )
    qs = [
        "A. Financial truly PIT? Knowledge-time yes. Values RESTATEMENT_RISK. Complete PIT no.",
        "B. Financial RESEARCH_READY? %s" % ready.get("FINANCIAL_ALPHA_READY"),
        "C. Industry PIT? **NO** (CURRENT_ONLY).",
        "D. Industry RESEARCH_READY? **NO**.",
        "E. Free data enough? Financial: %s. Industry: no." % ready.get("FINANCIAL_ALPHA_READY"),
        "F. If not: industry needs historical effective dates. Event still blocked. Do not buy.",
        "G. Financial Candidate? %s" % (cand.get("n") or 0),
        "H. Industry Candidate? 0",
        "I. Independent of H11/H12? %s" % d.get("independent_ids"),
        "J–O. See FINANCIAL_RESULTS.json. CAGR only from capital.",
        "P. Buy data? **NO**.",
        "Q. Next: `%s`" % d.get("NEXT"),
    ]
    _md(
        "V16_DECISION.md",
        "\n".join(
            [
                "# V16 Decision",
                "",
                "**%s**" % d.get("OVERALL"),
                "",
                "NEXT = `%s`. STOP = `%s`." % (d.get("NEXT"), d.get("STOP")),
                "",
                "```",
                "LEVEL = %s" % d.get("LEVEL"),
                "CANDIDATE = %s" % d.get("CANDIDATE"),
                "NEW_CANDIDATE = %s" % d.get("NEW_CANDIDATE"),
                "STRATEGY = %s" % d.get("STRATEGY"),
                "PORTFOLIO = %s" % d.get("PORTFOLIO"),
                "```",
                "",
                "H11/H12 KEEP_LOW_PRIORITY. No purchase. Final OOS DENIED.",
                "",
                "## Questions",
                "",
                "\n".join(qs),
                "",
                "FDR: %s" % fdr,
                "",
                "Failures n=%s" % fail.get("n"),
                "",
            ]
        ),
    )
    # keep expansion doc; append status
    print("COMPILE_V16", d.get("OVERALL"), d.get("NEXT"), flush=True)
    return d


if __name__ == "__main__":
    compile_v16()
