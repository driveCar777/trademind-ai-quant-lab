#!/usr/bin/env python3
"""Qualify Pack E bytes. Writes history map. Does not print the key."""
from __future__ import print_function

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.io_util import dump_json
from research_engine.local_fs import force_project_temp
from research_engine.v6_external.qualify import history_map, qualify_pack


STATE = os.path.join(
    ROOT, "data", "market", "research_engine", "external", "V61_ACQUIRE_STATE.json"
)
OUT_DIR = os.path.join(ROOT, "data", "market", "research_engine", "external")
DOC = os.path.join(ROOT, "docs", "research_engine", "FUTURES_DATASET_QUALIFICATION.md")


def _load(path):
    handle = open(path, encoding="utf-8")
    try:
        return json.load(handle)
    finally:
        handle.close()


def render_md(report, mapped):
    roots = report.get("roots") or {}
    lines = [
        "# FUTURES_DATASET_QUALIFICATION",
        "",
        "Gate: **%s**" % report.get("gate"),
        "Ava CFD used: **%s**" % report.get("ava_symbols_used"),
        "",
        "- definition rows: %s (outrights %s)"
        % (report.get("n_definition_rows"), report.get("n_outright")),
        "- ohlcv rows: %s (outrights %s)"
        % (report.get("n_ohlcv_rows"), report.get("n_ohlcv_outright")),
        "- statistics keep: %s (settle %s / OI %s / volume %s)"
        % (
            report.get("n_statistics_keep"),
            report.get("n_settlement"),
            report.get("n_open_interest"),
            report.get("n_cleared_volume"),
        ),
        "- billed USD (batch jobs): %s" % mapped.get("billed_usd"),
        "",
        "## Roots",
        "",
    ]
    for root, row in roots.items():
        lines.append("### %s" % root)
        lines.append("")
        lines.append("- outrights: %s" % row.get("n_outright_symbols"))
        lines.append("- expiries: %s" % row.get("n_expiries"))
        lines.append("- sessions: %s (%s → %s)" % (row.get("n_sessions"), row.get("first_session"), row.get("last_session")))
        lines.append("- settlement points: %s" % row.get("n_settlement"))
        lines.append("")
    if report.get("fail_reasons"):
        lines.append("## Fail reasons")
        lines.append("")
        for item in report["fail_reasons"]:
            lines.append("- `%s`" % item)
        lines.append("")
    lines.append("Spreads dropped. Official settlement required. Do not treat Ava GOLD/OIL as these parents.")
    lines.append("")
    return "\n".join(lines)


def main():
    force_project_temp()
    if not os.path.isfile(STATE):
        print("NO_ACQUIRE_STATE")
        return 2
    state = _load(STATE)
    report, _loaded = qualify_pack(state)
    mapped = history_map(report, state)
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    dump_json(os.path.join(OUT_DIR, "FUTURES_HISTORY_MAP.json"), mapped)
    dump_json(os.path.join(OUT_DIR, "DATABENTO_DATASETS_V1.json"), report)
    handle = open(DOC, "w", encoding="utf-8")
    try:
        handle.write(render_md(report, mapped))
    finally:
        handle.close()
    print("GATE", report.get("gate"))
    print("FAIL", ",".join(report.get("fail_reasons") or []) or "none")
    print("OUTRIGHTS", report.get("n_outright"))
    print("SETTLE", report.get("n_settlement"))
    return 0 if report.get("gate") == "READY_FOR_RESEARCH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
