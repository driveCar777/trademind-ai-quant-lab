#!/usr/bin/env python3
"""Freeze the slim GLBX curve panel. Raw zst stays gitignored."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.io_util import dump_json
from research_engine.local_fs import force_project_temp
from research_engine.v6_external.build_panel import (
    DATASET_ID,
    build_curve_rows,
    immutable_dir,
    sha256_file,
    write_curve_csv,
)
from research_engine.v6_external.qualify import qualify_pack


STATE = os.path.join(
    ROOT, "data", "market", "research_engine", "external", "V61_ACQUIRE_STATE.json"
)
LEDGER = os.path.join(
    ROOT, "data", "market", "research_engine", "external", "DATA_COST_LEDGER_V6.1.json"
)
CURVE_JSON = os.path.join(
    ROOT, "data", "market", "research_engine", "external", "FUTURES_CURVE_V1.json"
)


def _load(path):
    handle = open(path, encoding="utf-8")
    try:
        return json.load(handle)
    finally:
        handle.close()


def main():
    force_project_temp()
    state = _load(STATE)
    report, loaded = qualify_pack(state)
    if report.get("gate") != "READY_FOR_RESEARCH":
        print("NOT_READY", report.get("gate"), report.get("fail_reasons"))
        return 2
    features, raw_rows = build_curve_rows(loaded)
    target = immutable_dir()
    if os.path.exists(target):
        print("IMMUTABLE_EXISTS", DATASET_ID)
        return 2
    os.makedirs(target)
    csv_path = os.path.join(target, "curve.csv")
    write_curve_csv(csv_path, features)
    digest = sha256_file(csv_path)
    billed = 0.0
    for job in (state.get("jobs") or {}).values():
        if job.get("cost_usd") not in (None,):
            billed += float(job["cost_usd"])
    manifest = {
        "dataset_id": DATASET_ID,
        "source": "databento",
        "dataset": "GLBX.MDP3",
        "schema": "curve_panel_d1",
        "parents": ["GC.FUT", "CL.FUT"],
        "timeframe": "D1",
        "row_count": len(features),
        "raw_outright_rows": len(raw_rows),
        "sha256": digest,
        "FINAL_OOS_LOCKED": False,
        "broker_cfd": False,
        "continuous_only": False,
        "retrieved_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    quality = {
        "validation_status": "PASS",
        "gate": report.get("gate"),
        "lookahead_ok": True,
        "n_curve_rows": len(features),
        "roots": report.get("roots"),
        "note": "Front/second from listed outrights. Official settlement. Not Ava GOLD/OIL.",
    }
    dump_json(os.path.join(target, "manifest.json"), manifest)
    dump_json(os.path.join(target, "DATA_QUALITY.json"), quality)
    dump_json(os.path.join(ROOT, "data", "market", "manifests", DATASET_ID + ".json"), manifest)
    dump_json(
        CURVE_JSON,
        {
            "dataset_id": DATASET_ID,
            "sha256": digest,
            "n": len(features),
            "first": features[0]["session_date"] if features else None,
            "last": features[-1]["session_date"] if features else None,
        },
    )
    dump_json(
        LEDGER,
        {
            "pack": "E",
            "quoted_usd": 31.815091,
            "billed_usd": billed,
            "jobs": dict(
                (k, {"id": v.get("id"), "cost_usd": v.get("cost_usd"), "state": v.get("state")})
                for k, v in (state.get("jobs") or {}).items()
            ),
            "open_standard": False,
            "KEY_PRESENT": True,
            "FINAL_OOS_TOUCHED": False,
        },
    )
    print("DATASET", DATASET_ID)
    print("ROWS", len(features))
    print("SHA256", digest)
    print("BILLED", billed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
