"""Rebuild MT5 alpha coverage from frozen V9/V10 artifacts. Do not rewrite history."""
from __future__ import print_function

import json
import os
from collections import Counter

from research_engine.v11_alloc import FINAL_OOS_ACCESS, NEW_DOWNLOAD, NEW_PURCHASE, V11_ID
from research_engine.v11_alloc.paths import RE
from research_engine.v9_master.classify import MECHANISMS


def _load(rel):
    path = os.path.join(RE, rel)
    if not os.path.isfile(path):
        return None
    handle = open(path, "r", encoding="utf-8")
    try:
        return json.load(handle)
    finally:
        handle.close()


def _failed_map():
    raw = _load("FAILED_ALPHA_DATABASE_V2.json")
    if raw is None:
        raw = _load("forensics/FAILED_ALPHA_DATABASE_V2.json")
    out = {}
    for rec in (raw or {}).get("records") or []:
        out[rec.get("family")] = rec
    return out, raw


def build_coverage():
    failed, failed_raw = _failed_map()
    v9 = _load("master_backtest/MECHANISM_CLASSIFICATION_V9.json")
    v10 = _load("model_discovery/PROGRAM_V10.json")
    v9_prog = _load("master_backtest/MASTER_METRICS.json")
    rows = []
    for mech in MECHANISMS:
        fam = mech["family"]
        rec = failed.get(fam) or {}
        rows.append(
            {
                "family": fam,
                "class": mech.get("class"),
                "information_set": mech.get("information_set"),
                "replay_kind": mech.get("replay_kind"),
                "live_external": mech.get("live_external"),
                "status": rec.get("status") or "REPLAYED_V9",
                "what_failed": rec.get("what_failed"),
                "do_not_reopen": rec.get("forbidden_reopen_pattern") or True,
                "v10_note": None,
            }
        )
    rows.append(
        {
            "family": "MODEL_DISCOVERY_V10",
            "class": "ML",
            "information_set": "IS-D",
            "replay_kind": "MODEL_ONLY",
            "live_external": "NO",
            "status": "KILLED",
            "what_failed": "MODEL_REPRESENTATION_EXHAUSTED FDR 0/62",
            "do_not_reopen": "retune depth/threshold/target; AutoML on same set",
            "v10_note": v10,
        }
    )
    by_class = Counter(r["class"] for r in rows)
    killed = sum(1 for r in rows if r.get("status") == "KILLED")
    return {
        "index_id": "MT5_ALPHA_COVERAGE_V11",
        "discovery_id": V11_ID,
        "NEW_PURCHASE": NEW_PURCHASE,
        "NEW_DOWNLOAD": NEW_DOWNLOAD,
        "FINAL_OOS_ACCESS": FINAL_OOS_ACCESS,
        "n_families": len(rows),
        "n_killed": killed,
        "n_v9_mechanisms": len(v9.get("mechanisms") or []) if v9 else len(MECHANISMS),
        "n_failed_alpha_v2": None if failed_raw is None else failed_raw.get("n"),
        "by_class": dict(by_class),
        "qualified_execution_universe": ["GOLD", "EURUSD", "USDJPY", "OIL"],
        "mt5_cfd_inventory": 841,
        "v9": {
            "stop": "STOP_B",
            "positive_reproducible": 0,
            "candidate": 0,
            "mt5_only": "RESEARCH_POSITIVE_NOT_CANDIDATE",
            "mt5_public": "RESEARCH_POSITIVE_NOT_CANDIDATE",
            "mt5_futures": "RESEARCH_POSITIVE_NOT_CANDIDATE",
            "all_owned": "RESEARCH_POSITIVE_NOT_CANDIDATE",
            "master_metrics_present": v9_prog is not None,
        },
        "v10": v10
        or {
            "stop": "STOP_B_MODEL_REPRESENTATION_EXHAUSTED",
            "n_experiments": 62,
            "n_fdr_discoveries": 0,
            "CANDIDATE": 0,
        },
        "remaining_mt5_information_holes": [
            {
                "hole": "option_surface_IV_skew_term",
                "status": "QUOTED_NOT_OWNED",
                "bytes": 0,
                "can_answer_without_buy": False,
            },
            {
                "hole": "macro_consensus_surprise",
                "status": "NOT_OWNED",
                "note": "owned EIA/COT/rates are actual-only. actual != surprise",
            },
            {
                "hole": "structured_event_timestamp_consensus",
                "status": "NOT_OWNED",
                "note": "FOMC/CPI/NFP/OPEC cannot be studied without release time + consensus",
            },
        ],
        "exhaustion": "MT5_ALPHA_MARGINAL_VALUE_LOW",
        "families": rows,
        "note": "Coverage is replay of frozen evidence. Do not modify V0.1-V10 artifacts.",
    }
