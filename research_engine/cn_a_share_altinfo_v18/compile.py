"""Write V18 human reports."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share.paths import DOCS
from research_engine.cn_a_share_altinfo_v18.paths import OUT


REQUIRED = (
    "V18_ALTINFO_CONTRACT.md",
    "V18_ALTINFO_RUN.md",
    "V18_ALTINFO_AUDIT.md",
    "V18_ALTINFO_RESULT.md",
    "V18_ALTINFO_DECISION.md",
)


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


def _num(x):
    if x is None:
        return "n/a"
    return "%.4f" % float(x)


def _table(hyps):
    lines = [
        "| ID | Family | Val MEAN_FORWARD | Res cap | Val cap | Val CAGR | Rank IC val | FDR | L1 | Cluster |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for h in hyps:
        pv = (h.get("predictive") or {}).get("validation") or {}
        cr = (h.get("capital") or {}).get("research") or {}
        cv = (h.get("capital") or {}).get("validation") or {}
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                h.get("id"),
                h.get("family"),
                _pct(pv.get("MEAN_FORWARD_RETURN")),
                _pct(cr.get("total")),
                _pct(cv.get("total")),
                _pct(cv.get("CAGR")),
                _num(pv.get("rank_ic")),
                h.get("fdr_discovery"),
                h.get("level1"),
                h.get("cluster_tag"),
            )
        )
    return "\n".join(lines)


def compile_v18():
    d = _load("DECISION.json")
    res = _load("RESULTS.json")
    fdr = _load("FDR.json")
    contract = _load("CONTRACT.json")
    fail = _load("FAILURES.json")
    hyps = res.get("hypotheses") or []
    table = _table(hyps)
    _md("V18_ALTINFO_CONTRACT.md", "# V18 AltInfo Contract\n\nWrite-once. Hash: `%s`.\n\nFrozen basics / isST / tradestatus / CN calendar. No purchase. MEAN_FORWARD_RETURN is not CAGR.\n" % contract.get("contract_hash"))
    _md("V18_ALTINFO_RUN.md", "# V18 AltInfo Run\n\nWindows local. Xavier not used.\n\nOVERALL = **%s**. STOP = `%s`.\n" % (d.get("OVERALL"), d.get("STOP")))
    _md("V18_ALTINFO_AUDIT.md", "# V18 AltInfo Audit\n\n- PIT: listing_date and flags through signal date only.\n- FDR q=0.05 m=%s discoveries=%s\n- Failures: %s\n- Denied unused. Cost not lowered.\n" % (fdr.get("m"), fdr.get("discoveries"), fail.get("n")))
    _md("V18_ALTINFO_RESULT.md", "# V18 AltInfo Result\n\n%s\n\nNEW_CANDIDATE=%s NEW_INDEPENDENT=%s\n" % (table, d.get("NEW_CANDIDATE"), d.get("NEW_INDEPENDENT_CANDIDATE")))
    _md(
        "V18_ALTINFO_DECISION.md",
        "\n".join(
            [
                "# V18 Decision",
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
                "Question: do listing age / ST streak / resume / calendar windows contain a costed independent A-share CS edge?",
                "Data: frozen basics + pack isST/tradestatus + CN calendar.",
                "PIT: dates and flags through signal date.",
                "FDR m=%s discoveries=%s." % (fdr.get("m"), fdr.get("discoveries")),
                "Candidate: L1=%s independent=%s." % (d.get("NEW_CANDIDATE"), d.get("NEW_INDEPENDENT_CANDIDATE")),
                "Next: %s." % d.get("NEXT"),
                "",
                table,
            ]
        ),
    )
    print("V18_COMPILE", "ok", flush=True)
    return list(REQUIRED)
