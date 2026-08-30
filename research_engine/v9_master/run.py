"""V9 replay orchestrator. Local only. No purchase. No Final OOS."""
from __future__ import print_function

import json
import os
import time

from research_engine.profit.rank import classify_row, rank_program
from research_engine.v9_master.classify import MECHANISMS
from research_engine.v9_master.contract import build_contract
from research_engine.v9_master.paths import OUT, ensure_dir
from research_engine.v9_master.paths import LEDGERS
from research_engine.v9_master.replay_families import replay_all_families
from research_engine.v9_master.replay_special import replay_cross_asset, replay_predictive_only, replay_residual
from research_engine.v9_master.replay_v06 import replay_v06


def rows_from_ledgers():
    rows = []
    if not os.path.isdir(LEDGERS):
        return rows
    for name in sorted(os.listdir(LEDGERS)):
        path = os.path.join(LEDGERS, name, "metrics.json")
        if not os.path.isfile(path):
            continue
        try:
            metrics = json.load(open(path, "r"))
        except Exception:
            continue
        parts = name.split("__")
        strategy_id = metrics.get("strategy_id") or (parts[0] if parts else name)
        dataset_id = parts[1] if len(parts) > 1 else metrics.get("dataset_id")
        role = parts[2] if len(parts) > 2 else "research"
        scenario = parts[3] if len(parts) > 3 else metrics.get("scenario") or "base"
        rows.append(
            {
                "strategy_id": strategy_id,
                "family": metrics.get("family"),
                "information_set": metrics.get("information_set"),
                "replay_kind": metrics.get("replay_kind") or "STRATEGY_REPLAY",
                "target": dataset_id,
                "dataset_id": dataset_id,
                "timeframe": metrics.get("timeframe"),
                "role": role,
                "scenario": scenario,
                "metrics": metrics,
                "live_external_dependency": metrics.get("live_external_dependency") or "NO",
                "data_cost": 0.0,
            }
        )
    return rows


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
    v06_rows = []
    for row in rows:
        if row.get("family") != "PROFIT_DISCOVERY_V0.6":
            continue
        if row.get("scenario") not in (None, "base"):
            continue
        if row.get("role") != "research":
            continue
        mate = None
        for other in rows:
            if (
                other.get("strategy_id") == row.get("strategy_id")
                and (other.get("dataset_id") or other.get("target")) == (row.get("dataset_id") or row.get("target"))
                and other.get("role") == "validation"
                and other.get("scenario") in (None, "base")
            ):
                mate = other
                break
        v06_rows.append(
            {
                "dataset_id": row.get("dataset_id"),
                "timeframe": row.get("timeframe"),
                "strategy_id": row.get("strategy_id"),
                "family": row.get("family"),
                "research": row.get("metrics") or {},
                "validation": (mate or {}).get("metrics") or {},
            }
        )
    if v06_rows:
        ranked = rank_program(v06_rows)
        program = ranked.get("program") or ranked
        outcome = None
        if isinstance(ranked, dict):
            outcome = ranked.get("outcome") or ranked.get("program_outcome")
            if ranked.get("strategies"):
                for item in ranked.get("strategies") or []:
                    if item.get("status") == "CANDIDATE":
                        flagged = True
        if outcome == "STRATEGY_CANDIDATE_FOUND":
            flagged = True
    return flagged


def run_replay(include_v06_sensitivity=True, family_iters=1, resume=False):
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
    existing = rows_from_ledgers() if resume else []
    have_v06 = any((r.get("family") == "PROFIT_DISCOVERY_V0.6") for r in existing)
    have_xa = any((r.get("family") == "CROSS_ASSET_V0.8") for r in existing)
    have_xr = any((r.get("family") == "CROSS_RESIDUAL_V0.91") for r in existing)
    if have_v06:
        rows.extend([r for r in existing if r.get("family") == "PROFIT_DISCOVERY_V0.6"])
    else:
        rows.extend(replay_v06(include_sensitivity=include_v06_sensitivity))
    if have_xa:
        rows.extend([r for r in existing if r.get("family") == "CROSS_ASSET_V0.8"])
    else:
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
    if have_xr:
        rows.extend([r for r in existing if r.get("family") == "CROSS_RESIDUAL_V0.91"])
    else:
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
    try:
        rows.extend(replay_all_families(iters_boot=family_iters, iters_perm=family_iters))
    except Exception as exc:
        rows.append(
            {
                "strategy_id": "FAMILY_REPLAY_BATCH",
                "family": "FAMILY_REPLAY_BATCH",
                "replay_kind": "STRATEGY_REPLAY",
                "status": "NON_TRADEABLE",
                "error": str(exc),
            }
        )
    _dump(os.path.join(OUT, "REPLAY_ROWS_PARTIAL_V9.json"), {"n_rows": len(rows), "rows": rows})
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
