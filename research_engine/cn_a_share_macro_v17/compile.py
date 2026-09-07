"""Write V17 human reports from machine JSON."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share.paths import DOCS
from research_engine.cn_a_share_macro_v17.paths import OUT


REQUIRED = (
    "V17_MACRO_CONTRACT.md",
    "V17_MACRO_RUN.md",
    "V17_MACRO_AUDIT.md",
    "V17_MACRO_RESULT.md",
    "V17_MACRO_DECISION.md",
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
        "| ID | Family | L | Val MEAN_FORWARD | Res cap | Val cap | Val CAGR | Rank IC val | FDR | L1 | Cluster |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for h in hyps:
        pv = (h.get("predictive") or {}).get("validation") or {}
        cr = (h.get("capital") or {}).get("research") or {}
        cv = (h.get("capital") or {}).get("validation") or {}
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                h.get("id"),
                h.get("family"),
                h.get("lookback"),
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


def compile_v17():
    d = _load("DECISION.json")
    res = _load("RESULTS.json")
    fdr = _load("FDR.json")
    contract = _load("CONTRACT.json")
    fail = _load("FAILURES.json")
    hyps = res.get("hypotheses") or []
    table = _table(hyps)
    _md(
        "V17_MACRO_CONTRACT.md",
        "\n".join(
            [
                "# V17 Macro Contract",
                "",
                "Write-once before ranking. Hash: `%s`." % contract.get("contract_hash"),
                "",
                "- Price: `%s` / `%s`" % (contract.get("dataset_id"), contract.get("dataset_hash")),
                "- PIT: `%s`" % contract.get("pit_rule"),
                "- 6 pre-registered. No opposite-sign twin. No H11/H12/V16 reopen.",
                "- MEAN_FORWARD_RETURN is not CAGR. Cost `A_SHARE_STRATEGY_COST_MODEL_V1`.",
                "- Final OOS DENIED. Purchase = FALSE.",
            ]
        ),
    )
    _md(
        "V17_MACRO_RUN.md",
        "\n".join(
            [
                "# V17 Macro Run",
                "",
                "Windows local. Xavier not used. Frozen EURUSD / US500 / GVZ only.",
                "Resume via `RESULTS_PARTIAL.json`. Denied window not read.",
                "",
                "OVERALL = **%s**. STOP = `%s`." % (d.get("OVERALL"), d.get("STOP")),
            ]
        ),
    )
    _md(
        "V17_MACRO_AUDIT.md",
        "\n".join(
            [
                "# V17 Macro Audit",
                "",
                "- PIT rule: macro calendar date strictly before A-share signal date.",
                "- US500 starts 2011-01-17; early 2010 research days are NaN, not interpolated.",
                "- DXY / UST10 / GOLD 2018+ series were not used.",
                "- Cost not lowered. Sign not flipped. Denied window unused.",
                "- FDR q=0.05 m=%s discoveries=%s" % (fdr.get("m"), fdr.get("discoveries")),
                "- Failures: %s" % (fail.get("n")),
            ]
        ),
    )
    _md(
        "V17_MACRO_RESULT.md",
        "\n".join(
            [
                "# V17 Macro Result",
                "",
                table,
                "",
                "NEW_CANDIDATE (Level-1 hits) = %s. NEW_INDEPENDENT = %s."
                % (d.get("NEW_CANDIDATE"), d.get("NEW_INDEPENDENT_CANDIDATE")),
            ]
        ),
    )
    q = [
        "Question: does frozen public macro contain a costed, FDR-valid, H11-independent A-share CS edge?",
        "Hypothesis: 6 pre-registered beta×shock mappings.",
        "Data: frozen price 000002 + EURUSD + US500 + GVZ.",
        "PIT: macro_date < signal_date.",
        "Sample: 70/15/15 locked. Denied unused.",
        "Costs: A_SHARE_STRATEGY_COST_MODEL_V1.",
        "Multiple testing: BH q=0.05 m=%s." % fdr.get("m"),
        "FDR discoveries: %s." % (fdr.get("discoveries"),),
        "Capital validation: see table. CAGR only from non-overlapping book.",
        "Candidate status: L1=%s independent=%s." % (d.get("NEW_CANDIDATE"), d.get("NEW_INDEPENDENT_CANDIDATE")),
        "Decision: %s / %s." % (d.get("OVERALL"), d.get("STOP")),
        "Next action: %s." % d.get("NEXT"),
    ]
    _md(
        "V17_MACRO_DECISION.md",
        "\n".join(
            [
                "# V17 Decision",
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
                "STRATEGY = %s" % d.get("STRATEGY"),
                "PORTFOLIO = 0",
                "PAPER = 0",
                "LIVE = 0",
                "```",
                "",
                "H11/H12 KEEP_LOW_PRIORITY. No purchase. Final OOS DENIED.",
                "",
                "## Versus long-term CAGR >= 10%",
                "",
                "10% is not a gate. Do not retune toward it.",
                "",
                "## Answers",
                "",
                "\n".join("- %s" % line for line in q),
                "",
                table,
            ]
        ),
    )
    print("V17_COMPILE", "ok", flush=True)
    return list(REQUIRED)
