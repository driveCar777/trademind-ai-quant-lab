"""Readiness gates. READY is not a Candidate."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_information_v16.paths import OUT, ensure_v16


def financial_ready(pit, quality, catalog):
    checks = {
        "announcement_date": (catalog.get("announcement_rate") or 0) >= 0.90,
        "pit_test": bool(pit.get("pit_test_ok")),
        "future_mutation": bool(pit.get("future_value_mutation_ok") and pit.get("future_announcement_mutation_ok")),
        "coverage": bool(pit.get("coverage_ok")),
        "determinism": bool(catalog.get("csv_sha256")),
        "no_obvious_restatement_join_leak": bool(pit.get("pit_test_ok")),
        "duplicates": bool(quality.get("duplicate_ok")),
    }
    ready = all(checks.values())
    return {
        "FINANCIAL_ALPHA_READY": ready,
        "FINANCIAL_ALPHA_STATUS": "READY" if ready else "BLOCKED",
        "RESTATEMENT_RISK": True,
        "COMPLETE_PIT": False,
        "checks": checks,
    }


def industry_ready(ind_pit):
    checks = {
        "effective_dating": bool(ind_pit.get("effective_dating")),
        "historical_membership": bool(ind_pit.get("historical_membership")),
        "not_current_only": not bool(ind_pit.get("current_only")),
        "pit_available": bool(ind_pit.get("pit_available")),
        "pit_test": bool(ind_pit.get("pit_test_ok")),
        "mutation": bool(ind_pit.get("future_snapshot_mutation_ok")),
    }
    ready = all(checks.values())
    return {
        "INDUSTRY_ALPHA_READY": ready,
        "INDUSTRY_ALPHA_STATUS": "READY" if ready else "INDUSTRY_PIT_BLOCKED",
        "label": ind_pit.get("label") or "CURRENT_ONLY",
        "checks": checks,
    }


def write_readiness(fin, ind):
    ensure_v16()
    payload = dict(fin)
    payload.update(ind)
    dump_json(os.path.join(OUT, "READINESS.json"), payload)
    print("V16_READY", payload.get("FINANCIAL_ALPHA_STATUS"), payload.get("INDUSTRY_ALPHA_STATUS"), flush=True)
    return payload
