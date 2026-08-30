"""V9 replay orchestrator. Local only. No purchase. No Final OOS."""
from __future__ import print_function

import json
import os
import time

from research_engine.profit.rank import classify_row
from research_engine.v9_master.classify import MECHANISMS
from research_engine.v9_master.contract import build_contract
from research_engine.v9_master.paths import OUT, ensure_dir
from research_engine.v9_master.replay_families import replay_all_families
from research_engine.v9_master.replay_special import replay_cross_asset, replay_predictive_only, replay_residual
from research_engine.v9_master.replay_v06 import replay_v06


def _dump(path, payload):
    handle = open(path, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    finally:
        handle.close()


def _level1_flag(row):
    if row.get("replay_kind") != "STRATEGY_REPLAY":
        return False
    if row.get("scenario") not in (None, "base"):
        return False
    if row.get("role") != "research":
        return False
    mate = None
    return mate


def attach_level1(rows):
    pairs = {}
    for row in rows:
        if row.get("scenario") not in (None, "base"):
            continue
        if row.get("replay_kind") != "STRATEGY_REPLAY":
            continue
        key = (row.get("strategy_id"), row.get("dataset_id") or row.get("target"), row.get("family"))
        bucket = pairs.get(key)
        if bucket is None:
            bucket = {}
            pairs[key] = bucket
        bucket[row.get("role")] = (row.get("metrics") or {})
    flagged = False
    for key, bucket in pairs.items():
        status, why = classify_row(bucket.get("research"), bucket.get("validation"))
        for row in rows:
            same = (
                row.get("strategy_id") == key[0]
                and (row.get("dataset_id") or row.get("target")) == key[1]
                and row.get("family") == key[2]
            )
            if same:
                row["level1_dataset_status"] = status
                row["level1_dataset_why"] = why
                if status == "CANDIDATE":
                    flagged = True
                    row["STOP_A"] = True
    return flagged


def run_replay(include_v06_sensitivity=True, family_iters=1):
    ensure_dir(OUT)
    started = time.time()
    contract = build_contract()
    _dump(os.path.join(OUT, "MASTER_BACKTEST_CONTRACT_V9.json"), contract)
    _dump(
        os.path.join(OUT, "MECHANISM_CLASSIFICATION_V9.json"),
        {"n": len(MECHANISMS), "mechanisms": MECHANISMS},
    )
    rows = []
    rows.extend(replay_predictive_only())
    rows.extend(replay_v06(include_sensitivity=include_v06_sensitivity))
    try:
        rows.extend(replay_cross_asset())
    except Exception as exc:
        rows.append(
            {
                "strategy_id": "CROSS_ASSET_V0.8",
                "family": "CROSS_ASSET_V0.8",
                "information_set": "IS-A",
                "replay_kind": "STRATEGY_REPLAY",
                "status": "NON_TRADEABLE",
                "error": str(exc),
            }
        )
    try:
        rows.extend(replay_residual())
    except Exception as exc:
        rows.append(
            {
                "strategy_id": "CROSS_RESIDUAL_V0.91",
                "family": "CROSS_RESIDUAL_V0.91",
                "information_set": "IS-A",
                "replay_kind": "STRATEGY_REPLAY",
                "status": "NON_TRADEABLE",
                "error": str(exc),
            }
        )
    rows.extend(replay_all_families(iters_boot=family_iters, iters_perm=family_iters))
    stop_a = attach_level1(rows)
    payload = {
        "replay_id": "V9_MASTER_REPLAY",
        "elapsed_seconds": time.time() - started,
        "n_rows": len(rows),
        "STOP_A": stop_a,
        "NEW_DATA_PURCHASE": False,
        "rows": rows,
    }
    _dump(os.path.join(OUT, "REPLAY_ROWS_V9.json"), payload)
    return payload
