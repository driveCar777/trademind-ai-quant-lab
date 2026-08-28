"""Alpha Recovery Program V1.0. Forensics + inventory + map + score + one contract. No Xavier."""
from __future__ import print_function

import os

from research_engine.forensics.alpha_gap_report import build_report
from research_engine.forensics.calendar_events import count_all
from research_engine.forensics.failure_analyzer import analyze
from research_engine.forensics.inventory import build_capability, inventory_disk, probe_mt5
from research_engine.forensics.reports import (
    render_contract_md,
    render_data_md,
    render_decision_md,
    render_recovery_report,
)
from research_engine.forensics.scan import scan_index
from research_engine.forensics.search_space_coverage import coverage_table
from research_engine.holdout import final_oos_access
from research_engine.information_map.build import build_map
from research_engine.io_util import dump_json
from research_engine.opportunity.catalog import all_opportunities
from research_engine.opportunity.contract_it import LOCKED_HASH, build_search_space
from research_engine.opportunity.select import select_one
from research_protocol.hashing import canonical_hash


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_FORENSICS = os.path.join(ROOT, "data", "market", "research_engine", "forensics")
OUT_MAP = os.path.join(ROOT, "data", "market", "research_engine", "information_map")
OUT_OPP = os.path.join(ROOT, "data", "market", "research_engine", "opportunity")
OUT_IT = os.path.join(ROOT, "data", "market", "research_engine", "institutional_time")
DOCS = os.path.join(ROOT, "docs", "research_engine")


def _deny_oos():
    try:
        final_oos_access(reason="alpha_recovery_pipeline")
    except Exception as exc:
        if type(exc).__name__ != "FinalOosAccessDenied":
            raise
        return True
    raise RuntimeError("FINAL_OOS_WAS_NOT_DENIED")


def run(write=False, probe=True):
    _deny_oos()
    index = scan_index()
    families = analyze()
    gap = build_report()
    coverage = coverage_table()
    info_map = build_map()
    disk = inventory_disk()
    probed = probe_mt5() if probe else {"ok": False, "status": "SKIPPED", "rows": [], "reason": "probe_disabled"}
    capability = build_capability(disk, probed)
    calendar = count_all()
    selection = select_one(all_opportunities())
    space = build_search_space()
    if selection.get("chosen") != "OPP-IT-ME":
        raise RuntimeError("SELECTION_DRIFT:%s" % selection.get("chosen"))
    if space.get("search_space_hash") != LOCKED_HASH:
        raise RuntimeError("IT_HASH_DRIFT")
    payload = {
        "program_id": "ALPHA_RECOVERY_PROGRAM_V1",
        "FINAL_OOS_TOUCHED": False,
        "executed_new_family": False,
        "index": {
            "n_rankings": len(index.get("rankings") or []),
            "n_datasets": len(index.get("datasets") or []),
            "n_contracts": len(index.get("contracts") or []),
            "hyp0001_n_files": (index.get("hyp0001_results") or {}).get("n_files"),
        },
        "gap": gap,
        "coverage_pct": dict((k, v.get("covered_pct")) for k, v in coverage.items()),
        "information_map": info_map,
        "capability_overall": capability.get("overall"),
        "calendar": calendar,
        "selection": {
            "chosen": selection.get("chosen"),
            "eligible": selection.get("eligible"),
            "top10": [
                {
                    "id": r.get("id"),
                    "score": r.get("score"),
                    "status": r.get("status"),
                    "why_not_tested": r.get("why_not_tested"),
                    "mechanism_text": r.get("mechanism_text"),
                }
                for r in selection.get("top10") or []
            ],
        },
        "contract": {
            "discovery_id": space.get("discovery_id"),
            "family_id": space.get("family_id"),
            "search_space_hash": space.get("search_space_hash"),
            "executed": False,
        },
    }
    payload["content_hash"] = canonical_hash(
        {
            "coverage": payload["coverage_pct"],
            "chosen": payload["selection"]["chosen"],
            "it_hash": space.get("search_space_hash"),
            "families": [r.get("family") for r in families],
        }
    )
    docs = {
        "ALPHA_RECOVERY_REPORT.md": render_recovery_report(gap, coverage, selection, calendar, capability),
        "DATA_CAPABILITY_REAL.md": render_data_md(capability),
        "NEXT_ALPHA_DECISION.md": render_decision_md(selection, space, calendar, capability),
        "INSTITUTIONAL_TIME_V1.0_CONTRACT.md": render_contract_md(space, calendar),
    }
    written = []
    if write:
        dump_json(os.path.join(OUT_FORENSICS, "SCAN_INDEX.json"), index)
        dump_json(os.path.join(OUT_FORENSICS, "FAILURE_ANALYSIS.json"), {"families": families})
        dump_json(os.path.join(OUT_FORENSICS, "SEARCH_SPACE_COVERAGE.json"), coverage)
        dump_json(os.path.join(OUT_FORENSICS, "ALPHA_GAP_REPORT.json"), gap)
        dump_json(os.path.join(OUT_FORENSICS, "DATA_CAPABILITY_REAL.json"), capability)
        dump_json(os.path.join(OUT_MAP, "ALPHA_INFORMATION_MAP_V1.json"), info_map)
        dump_json(os.path.join(OUT_OPP, "ALPHA_OPPORTUNITY_V2.json"), selection)
        dump_json(os.path.join(OUT_IT, "IT_SEARCH_SPACE_V1.0.json"), space)
        dump_json(os.path.join(OUT_FORENSICS, "ALPHA_RECOVERY_PROGRAM_V1.json"), payload)
        for name, text in docs.items():
            path = os.path.join(DOCS, name)
            parent = os.path.dirname(path)
            if not os.path.isdir(parent):
                os.makedirs(parent)
            handle = open(path, "w", encoding="utf-8")
            try:
                handle.write(text)
                if not text.endswith("\n"):
                    handle.write("\n")
            finally:
                handle.close()
            written.append(os.path.relpath(path, ROOT).replace("\\", "/"))
        cap_copy = os.path.join(DOCS, "DATA_CAPABILITY_REAL.json")
        dump_json(cap_copy, capability)
        written.append("docs/research_engine/DATA_CAPABILITY_REAL.json")
    return payload, {
        "docs": docs,
        "written": written,
        "capability": capability,
        "space": space,
        "selection": selection,
        "calendar": calendar,
        "gap": gap,
    }
