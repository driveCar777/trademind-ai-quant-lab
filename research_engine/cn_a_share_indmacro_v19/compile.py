"""Write V19 reports."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share.paths import DOCS
from research_engine.cn_a_share_indmacro_v19.paths import OUT


REQUIRED = ("V19_INDMACRO_CONTRACT.md", "V19_INDMACRO_RUN.md", "V19_INDMACRO_AUDIT.md", "V19_INDMACRO_RESULT.md", "V19_INDMACRO_DECISION.md")


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


def compile_v19():
    d = _load("DECISION.json")
    res = _load("RESULTS.json")
    fdr = _load("FDR.json")
    contract = _load("CONTRACT.json")
    hyps = res.get("hypotheses") or []
    lines = ["| ID | Family | Val MEAN_FORWARD | Res cap | Val cap | Val CAGR | Rank IC | FDR | L1 |", "|---|---|---|---|---|---|---|---|---|"]
    for h in hyps:
        pv = (h.get("predictive") or {}).get("validation") or {}
        cr = (h.get("capital") or {}).get("research") or {}
        cv = (h.get("capital") or {}).get("validation") or {}
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (h.get("id"), h.get("family"), _pct(pv.get("MEAN_FORWARD_RETURN")), _pct(cr.get("total")), _pct(cv.get("total")), _pct(cv.get("CAGR")), _num(pv.get("rank_ic")), h.get("fdr_discovery"), h.get("level1")))
    table = "\n".join(lines)
    _md("V19_INDMACRO_CONTRACT.md", "# V19 Industry×Macro Contract\n\nHash: `%s`.\n\nIndustry PIT × frozen EURUSD/US500/GVZ. Not V16 RS. Not V17 stock beta.\n" % contract.get("contract_hash"))
    _md("V19_INDMACRO_RUN.md", "# V19 Run\n\nOVERALL=**%s** STOP=`%s`\n" % (d.get("OVERALL"), d.get("STOP")))
    _md("V19_INDMACRO_AUDIT.md", "# V19 Audit\n\nPIT: industry effective_date <= signal; macro date < signal.\nFDR m=%s discoveries=%s\n" % (fdr.get("m"), fdr.get("discoveries")))
    _md("V19_INDMACRO_RESULT.md", "# V19 Result\n\n%s\n" % table)
    _md("V19_INDMACRO_DECISION.md", "# V19 Decision\n\n**%s**\n\nNEXT=`%s` STOP=`%s`\nNEW_CANDIDATE=%s NEW_INDEPENDENT=%s\n\n%s\n" % (d.get("OVERALL"), d.get("NEXT"), d.get("STOP"), d.get("NEW_CANDIDATE"), d.get("NEW_INDEPENDENT_CANDIDATE"), table))
    print("V19_COMPILE", "ok", flush=True)
    return list(REQUIRED)
