"""Write V20 human reports."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share.paths import DOCS
from research_engine.cn_a_share_index_v20.paths import OUT

REQUIRED = (
    "V20_INDEX_CONTRACT.md",
    "V20_INDEX_RUN.md",
    "V20_INDEX_AUDIT.md",
    "V20_INDEX_RESULT.md",
    "V20_INDEX_DECISION.md",
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
    return load_json(path) if os.path.isfile(path) else {}


def _pct(x):
    return "n/a" if x is None else "%.2f%%" % (100.0 * float(x))


def _num(x):
    return "n/a" if x is None else "%.4f" % float(x)


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


def compile_v20():
    d = _load("DECISION.json")
    res = _load("RESULTS.json")
    fdr = _load("FDR.json")
    contract = _load("CONTRACT.json")
    fail = _load("FAILURES.json")
    pit = _load("INDEX_PIT.json")
    hyps = res.get("hypotheses") or []
    table = _table(hyps)
    _md(
        "V20_INDEX_CONTRACT.md",
        "# V20 Index Membership Contract\n\nWrite-once. Hash: `%s`.\n\nHS300/ZZ500 monthly as-of. Portfolio = MEMBERSHIP_SET, not quintile-of-binary. MEAN_FORWARD_RETURN is not CAGR.\n"
        % contract.get("contract_hash"),
    )
    _md("V20_INDEX_RUN.md", "# V20 Index Run\n\nWindows local. Xavier not used.\n\nOVERALL = **%s**. STOP = `%s`.\n" % (d.get("OVERALL"), d.get("STOP")))
    _md(
        "V20_INDEX_AUDIT.md",
        "# V20 Index Audit\n\n- PIT: index effective_date <= signal. pit_test_ok=%s n_asof=%s mutation_ok=%s\n- Portfolio = set of members / add / drop. Not quintile.\n- FDR q=0.05 m=%s discoveries=%s\n- Failures: %s\n- Denied unused. Cost not lowered. H11/H12 not reopened.\n"
        % (pit.get("pit_test_ok"), pit.get("n_asof"), pit.get("future_snapshot_mutation_ok"), fdr.get("m"), fdr.get("discoveries"), fail.get("n")),
    )
    _md("V20_INDEX_RESULT.md", "# V20 Index Result\n\n%s\n\nNEW_CANDIDATE=%s NEW_INDEPENDENT=%s\n" % (table, d.get("NEW_CANDIDATE"), d.get("NEW_INDEPENDENT_CANDIDATE")))
    _md(
        "V20_INDEX_DECISION.md",
        "\n".join(
            [
                "# V20 Decision",
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
                "Question: do CSI 300 / CSI 500 membership or 252-session add/delete sets contain a costed independent A-share CS edge?",
                "Data: frozen price panel + BaoStock monthly index as-of.",
                "PIT: effective_date <= signal. pit_test_ok=%s." % pit.get("pit_test_ok"),
                "FDR m=%s discoveries=%s." % (fdr.get("m"), fdr.get("discoveries")),
                "Candidate: L1=%s independent=%s." % (d.get("NEW_CANDIDATE"), d.get("NEW_INDEPENDENT_CANDIDATE")),
                "Next: %s." % d.get("NEXT"),
                "",
                table,
            ]
        ),
    )
    print("V20_COMPILE", "ok", flush=True)
    return list(REQUIRED)
