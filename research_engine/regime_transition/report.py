"""Write V0.9 report and decision payload. No marketing. No hash rewrite."""
from __future__ import print_function

import os

from research_engine.io_util import dump_json
from research_engine.regime_transition import LOCKED_HASH, RT_ID


def decide(ranking):
    outcome = ranking.get("outcome")
    if outcome == "CANDIDATE":
        nxt = "STRATEGY_MINING"
    elif outcome == "WEAK_EDGE":
        nxt = "SECOND_MECHANISM_RESIDUAL_V0.91"
    else:
        nxt = "FAILED_ALPHA_THEN_RESIDUAL_V0.91"
    return {
        "discovery_id": RT_ID,
        "outcome": outcome,
        "candidate_count": 1 if outcome == "CANDIDATE" else 0,
        "next_action": nxt,
        "optimize_forbidden": outcome != "CANDIDATE",
        "strategy_layer_allowed": outcome == "CANDIDATE",
        "note": "Do not retune hold/ADX/VOL. Do not read Final OOS.",
    }


def render_markdown(ranking, decision, benchmarks=None, hashes=None):
    hyps = ranking.get("hypotheses") or []
    lines = []
    lines.append("# Regime Transition V0.9 Report")
    lines.append("")
    lines.append("Executed. Hash lock `%s`." % LOCKED_HASH)
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("- Program: **%s**" % ranking.get("outcome"))
    lines.append("- Next: `%s`" % decision.get("next_action"))
    lines.append("- Strategy layer allowed: %s" % decision.get("strategy_layer_allowed"))
    lines.append("- FDR discoveries: %s" % (ranking.get("fdr") or {}).get("discoveries"))
    lines.append("- GOLD pass: %s" % ranking.get("gold_pass"))
    lines.append("- OIL pass: %s" % ranking.get("oil_pass"))
    lines.append("")
    lines.append("## Hypotheses")
    lines.append("")
    for row in hyps:
        r = row.get("research") or {}
        v = row.get("validation") or {}
        lines.append("### %s" % row.get("hypothesis_id"))
        lines.append("")
        lines.append("- label: %s" % row.get("label"))
        lines.append("- target: %s" % row.get("target_asset"))
        lines.append("- RESEARCH n_trade=%s occupancy=%s TR=%s CAGR=%s delta=%s p=%s" % (
            r.get("n_trade"), r.get("occupancy"), r.get("total_return"), r.get("cagr"), r.get("delta"), r.get("raw_p"),
        ))
        lines.append("- VALIDATION n_trade=%s TR=%s CAGR=%s" % (
            v.get("n_trade"), v.get("total_return"), v.get("cagr"),
        ))
        lines.append("- why: %s" % ", ".join(row.get("dataset_why") or []))
        lines.append("")
    if benchmarks:
        lines.append("## Path benchmark (not a hypothesis)")
        lines.append("")
        lines.append("```")
        lines.append(str(benchmarks))
        lines.append("```")
        lines.append("")
    if hashes:
        lines.append("## Hashes")
        lines.append("")
        for key in sorted(hashes.keys()):
            lines.append("- %s: `%s`" % (key, hashes[key]))
        lines.append("")
    lines.append("CAGR >= 10% is not a gate. This file does not certify annualized 10%.")
    lines.append("")
    return "\n".join(lines)


def write_outputs(out_dir, ranking, decision, benchmarks=None, hashes=None):
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    dump_json(os.path.join(out_dir, "REGIME_RANKING_V0.9.json"), ranking)
    dump_json(os.path.join(out_dir, "REGIME_DECISION_V0.9.json"), decision)
    if benchmarks is not None:
        dump_json(os.path.join(out_dir, "PATH_BENCHMARK_V0.9.json"), benchmarks)
    body = render_markdown(ranking, decision, benchmarks=benchmarks, hashes=hashes)
    handle = open(os.path.join(out_dir, "REGIME_TRANSITION_V0.9_REPORT.md"), "w")
    try:
        handle.write(body)
        if not body.endswith("\n"):
            handle.write("\n")
    finally:
        handle.close()
    return body
