from __future__ import print_function

import os

from research_engine.io_util import dump_json
from research_engine.alt_market_structure import AMS_ID
from research_engine.alt_market_structure.space import canonical_search_space_hash


def decide(ranking):
    outcome = ranking.get("outcome")
    return {
        "discovery_id": AMS_ID,
        "outcome": outcome,
        "candidate_count": 1 if outcome == "CANDIDATE" else 0,
        "next_action": "CANDIDATE_DEEP_VALIDATION" if outcome == "CANDIDATE" else "KILL_FAMILY_THEN_NEXT_ALPHA",
        "optimize_forbidden": True,
        "z_cut_change_forbidden": True,
        "strategy_layer_allowed": outcome == "CANDIDATE",
        "note": "Do not retune z_cut or lookback. Do not read Final OOS.",
    }


def write_outputs(out_dir, ranking, decision, hashes=None):
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    dump_json(os.path.join(out_dir, "AMS_RANKING_V1.json"), ranking)
    dump_json(os.path.join(out_dir, "AMS_DECISION_V1.json"), decision)
    lines = [
        "# Microstructure Surprise V1 Report",
        "",
        "Executed. Hash lock `%s`." % canonical_search_space_hash(),
        "",
        "- Program: **%s**" % ranking.get("outcome"),
        "- Next: `%s`" % decision.get("next_action"),
        "- FDR: %s" % (ranking.get("fdr") or {}).get("discoveries"),
        "- GOLD pass: %s OIL pass: %s" % (ranking.get("gold_pass"), ranking.get("oil_pass")),
        "",
    ]
    for row in ranking.get("hypotheses") or []:
        r = row.get("research") or {}
        v = row.get("validation") or {}
        lines.append("### %s" % row.get("hypothesis_id"))
        lines.append("- label %s target %s event %s" % (row.get("label"), row.get("target_asset"), row.get("event")))
        lines.append("- RESEARCH n=%s occ=%s TR=%s p=%s" % (r.get("n_trade"), r.get("occupancy"), r.get("total_return"), r.get("raw_p")))
        lines.append("- VALIDATION n=%s TR=%s why=%s" % (v.get("n_trade"), v.get("total_return"), ",".join(row.get("dataset_why") or [])))
        lines.append("")
    lines.append("Not FD tickvol level. Not 10%.")
    lines.append("")
    path = os.path.join(out_dir, "AMS_REPORT_V1.md")
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write("\n".join(lines))
    finally:
        handle.close()
    return path
