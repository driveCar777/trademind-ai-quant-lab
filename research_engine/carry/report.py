"""IV report and decision. No hash rewrite. No 10% claim."""
from __future__ import print_function

import os

from research_engine.carry import CARRY_ID
from research_engine.carry.space import canonical_search_space_hash
from research_engine.io_util import dump_json


def decide(ranking):
    outcome = ranking.get("outcome")
    if outcome == "CANDIDATE":
        nxt = "CANDIDATE_DEEP_VALIDATION"
    else:
        nxt = "KILL_FAMILY_THEN_NEXT_SOURCE"
    return {
        "discovery_id": CARRY_ID,
        "outcome": outcome,
        "candidate_count": 1 if outcome == "CANDIDATE" else 0,
        "next_action": nxt,
        "optimize_forbidden": True,
        "zcut_change_forbidden": True,
        "strategy_layer_allowed": outcome == "CANDIDATE",
        "note": "Do not retune z_cut or flip sign. Do not read Final OOS.",
    }


def render_markdown(ranking, decision, hashes=None):
    hyps = ranking.get("hypotheses") or []
    lines = [
        "# Carry V1A Report",
        "",
        "Executed. Hash lock `%s`." % canonical_search_space_hash(),
        "",
        "## Decision",
        "",
        "- Program: **%s**" % ranking.get("outcome"),
        "- Next: `%s`" % decision.get("next_action"),
        "- Strategy layer allowed: %s" % decision.get("strategy_layer_allowed"),
        "- FDR discoveries: %s" % (ranking.get("fdr") or {}).get("discoveries"),
        "- EURUSD pass: %s" % ranking.get("eurusd_pass"),
        "- USDJPY pass: %s" % ranking.get("usdjpy_pass"),
        "",
        "## Hypotheses",
        "",
    ]
    for row in hyps:
        r = row.get("research") or {}
        v = row.get("validation") or {}
        lines.append("### %s" % row.get("hypothesis_id"))
        lines.append("")
        lines.append("- label: %s" % row.get("label"))
        lines.append("- target: %s event: %s" % (row.get("target_asset"), row.get("event")))
        lines.append(
            "- RESEARCH n_trade=%s occupancy=%s TR=%s delta=%s p=%s"
            % (r.get("n_trade"), r.get("occupancy"), r.get("total_return"), r.get("delta"), r.get("raw_p"))
        )
        lines.append("- VALIDATION n_trade=%s TR=%s" % (v.get("n_trade"), v.get("total_return")))
        lines.append("- why: %s" % ", ".join(row.get("dataset_why") or []))
        lines.append("")
    if hashes:
        lines.append("## Hashes")
        lines.append("")
        for key in sorted(hashes.keys()):
            lines.append("- %s: `%s`" % (key, hashes[key]))
        lines.append("")
    lines.append("CAGR >= 10% is not a gate. Not V0.8 FX price. Not RATES 10y on gold. Not a z_cut search.")
    lines.append("")
    return "\n".join(lines)


def write_outputs(out_dir, ranking, decision, hashes=None):
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    dump_json(os.path.join(out_dir, "CARRY_RANKING_V1A.json"), ranking)
    dump_json(os.path.join(out_dir, "CARRY_DECISION_V1A.json"), decision)
    md = render_markdown(ranking, decision, hashes=hashes)
    path = os.path.join(out_dir, "CARRY_REPORT_V1A.md")
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write(md)
        if not md.endswith("\n"):
            handle.write("\n")
    finally:
        handle.close()
    return path
