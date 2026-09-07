"""Write V21 human reports."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share.paths import DOCS
from research_engine.cn_a_share_div_v21.paths import OUT

REQUIRED = ("V21_DIVIDEND_CONTRACT.md", "V21_DIVIDEND_RUN.md", "V21_DIVIDEND_AUDIT.md", "V21_DIVIDEND_RESULT.md", "V21_DIVIDEND_DECISION.md")


def _md(name, body):
    path = os.path.join(DOCS, name)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write(body if body.endswith("\n") else body + "\n")
    finally:
        handle.close()


def _load(name):
    path = os.path.join(OUT, name)
    return load_json(path) if os.path.isfile(path) else {}


def _pct(x):
    return "n/a" if x is None else "%.2f%%" % (100.0 * float(x))


def _num(x):
    return "n/a" if x is None else "%.4f" % float(x)


def _table(hyps):
    lines = ["| ID | Family | Val MEAN_FORWARD | Res cap | Val cap | Val CAGR | Rank IC val | FDR | L1 | Cluster |", "|---|---|---|---|---|---|---|---|---|---|"]
    for h in hyps:
        pv = (h.get("predictive") or {}).get("validation") or {}
        cr = (h.get("capital") or {}).get("research") or {}
        cv = (h.get("capital") or {}).get("validation") or {}
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (h.get("id"), h.get("family"), _pct(pv.get("MEAN_FORWARD_RETURN")), _pct(cr.get("total")), _pct(cv.get("total")), _pct(cv.get("CAGR")), _num(pv.get("rank_ic")), h.get("fdr_discovery"), h.get("level1"), h.get("cluster_tag")))
    return "\n".join(lines)


def compile_v21():
    d = _load("DECISION.json")
    res = _load("RESULTS.json")
    fdr = _load("FDR.json")
    contract = _load("CONTRACT.json")
    fail = _load("FAILURES.json")
    pit = _load("DIVIDEND_PIT.json")
    hyps = res.get("hypotheses") or []
    table = _table(hyps)
    _md("V21_DIVIDEND_CONTRACT.md", "# V21 Dividend Event Contract\n\nWrite-once. Hash: `%s`.\n\nCash / stock announcement windows. Not yield quintile. announce_date < signal. MEAN_FORWARD_RETURN is not CAGR.\n" % contract.get("contract_hash"))
    _md("V21_DIVIDEND_RUN.md", "# V21 Dividend Run\n\nWindows local. Xavier not used.\n\nOVERALL = **%s**. STOP = `%s`.\n" % (d.get("OVERALL"), d.get("STOP")))
    _md("V21_DIVIDEND_AUDIT.md", "# V21 Dividend Audit\n\n- PIT: announce_date < signal. operate date is not knowledge time. pit_test_ok=%s\n- FDR m=%s discoveries=%s\n- Failures: %s\n- Denied unused. Cost not lowered.\n" % (pit.get("pit_test_ok"), fdr.get("m"), fdr.get("discoveries"), fail.get("n")))
    _md("V21_DIVIDEND_RESULT.md", "# V21 Dividend Result\n\n%s\n\nNEW_CANDIDATE=%s NEW_INDEPENDENT=%s\n" % (table, d.get("NEW_CANDIDATE"), d.get("NEW_INDEPENDENT_CANDIDATE")))
    _md(
        "V21_DIVIDEND_DECISION.md",
        "\n".join(
            [
                "# V21 Decision",
                "",
                "**%s**" % d.get("OVERALL"),
                "",
                "NEXT = `%s`. STOP = `%s`." % (d.get("NEXT"), d.get("STOP")),
                "",
                "```",
                "LEVEL = %s" % d.get("LEVEL"),
                "CANDIDATE = %s" % d.get("CANDIDATE"),
                "NEW_CANDIDATE = %s" % d.get("NEW_CANDIDATE"),
                "NEW_INDEPENDENT_CANDIDATE = %s" % d.get("NEW_INDEPENDENT_CANDIDATE"),
                "STRATEGY = 2",
                "PORTFOLIO = 0",
                "```",
                "",
                "Question: do cash or stock dividend *announcement windows* contain a costed independent A-share CS edge?",
                "Not a high-yield quintile. Not V16 ROE.",
                "PIT: announce_date < signal. pit_test_ok=%s." % pit.get("pit_test_ok"),
                "FDR m=%s discoveries=%s." % (fdr.get("m"), fdr.get("discoveries")),
                "Candidate: L1=%s independent=%s." % (d.get("NEW_CANDIDATE"), d.get("NEW_INDEPENDENT_CANDIDATE")),
                "",
                table,
            ]
        ),
    )
    print("V21_COMPILE", "ok", flush=True)
    return list(REQUIRED)
