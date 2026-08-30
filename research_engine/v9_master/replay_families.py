"""Replay locked family books via existing evaluate. No new rules."""
from __future__ import print_function

import importlib
import os
import traceback

from research_engine.io_util import load_json
from research_engine.v9_master import START_EQUITY
from research_engine.v9_master.capture import BookCapture
from research_engine.v9_master.classify import strategy_families
from research_engine.v9_master.enrich import enrich_family_trade
from research_engine.v9_master.metrics_v9 import economic_status, extend_metrics
from research_engine.v9_master.paths import IMMUTABLE, RESEARCH, TMP, ensure_dir
from research_engine.v9_master.persist import persist_book


def _import(name):
    return importlib.import_module("research_engine." + name)


def _hyps(space_mod, space):
    hmap = space_mod.hypothesis_map(space)
    return list(hmap.values())


def _target_of(spec, packed):
    target = spec.get("target") or spec.get("target_asset")
    if target and packed and target in packed:
        return target
    keys = [k for k in (packed or {}) if not str(k).startswith("_")]
    return keys[0] if keys else target


def _bars_of(packed, target):
    if not packed:
        return []
    row = packed.get(target) or {}
    return row.get("bars") or []


def replay_generic(mech, iters_boot=1, iters_perm=1):
    rows = []
    module_name = mech.get("module")
    if not module_name or mech.get("special"):
        return rows
    space_rel = mech.get("space_file")
    space_path = os.path.join(RESEARCH, space_rel.replace("/", os.sep))
    if not os.path.isfile(space_path):
        rows.append(
            {
                "strategy_id": mech["family"],
                "family": mech["family"],
                "information_set": mech["information_set"],
                "replay_kind": "STRATEGY_REPLAY",
                "status": "NON_TRADEABLE",
                "error": "SPACE_FILE_MISSING",
            }
        )
        return rows
    space = load_json(space_path)
    out_dir = ensure_dir(os.path.join(TMP, "family", mech["family"]))
    try:
        mod = _import(module_name)
        prepare = _import(module_name + ".prepare")
        runner = _import(module_name + ".hypothesis_runner")
        space_mod = _import(module_name + ".space")
        packed, _space = prepare.prepare_pack(IMMUTABLE, out_dir, space=space)
        specs = _hyps(space_mod, space)
    except Exception as exc:
        rows.append(
            {
                "strategy_id": mech["family"],
                "family": mech["family"],
                "information_set": mech["information_set"],
                "replay_kind": "STRATEGY_REPLAY",
                "status": "NON_TRADEABLE",
                "error": "%s: %s" % (type(exc).__name__, exc),
                "trace": traceback.format_exc()[-1500:],
            }
        )
        return rows
    for spec in specs:
        hid = spec.get("hypothesis_id") or mech["family"]
        target = _target_of(spec, packed)
        bars = _bars_of(packed, target)
        try:
            cap = BookCapture()
            cap.start()
            try:
                result = runner.run_hypothesis(
                    spec,
                    packed,
                    iters_boot=iters_boot,
                    iters_perm=iters_perm,
                )
            finally:
                cap.stop()
        except Exception as exc:
            rows.append(
                {
                    "strategy_id": hid,
                    "family": mech["family"],
                    "information_set": mech["information_set"],
                    "replay_kind": "STRATEGY_REPLAY",
                    "target": target,
                    "status": "NON_TRADEABLE",
                    "error": "%s: %s" % (type(exc).__name__, exc),
                }
            )
            continue
        calls = cap.calls
        research_m = (result or {}).get("research") or {}
        validation_m = (result or {}).get("validation") or {}
        role_metrics = {"research": research_m, "validation": validation_m}
        if len(calls) >= 2:
            for i, role in enumerate(("research", "validation")):
                call = calls[i]
                trades = [enrich_family_trade(tr) for tr in call.get("trades") or []]
                curve = call.get("curve") or [START_EQUITY]
                metrics = extend_metrics(curve, call.get("timeframe") or "D1", START_EQUITY, trades, bars)
                metrics["family"] = mech["family"]
                metrics["strategy_id"] = hid
                metrics["information_set"] = mech["information_set"]
                metrics["replay_kind"] = "STRATEGY_REPLAY"
                metrics["execution_model"] = "EXECUTION_APPROXIMATION"
                metrics["live_external_dependency"] = mech.get("live_external") or "NO"
                metrics["frozen_total_return"] = role_metrics[role].get("total_return")
                persist_book(hid, target or mech["family"], role, "base", curve, trades, metrics, bars)
                rows.append(
                    {
                        "strategy_id": hid,
                        "family": mech["family"],
                        "information_set": mech["information_set"],
                        "replay_kind": "STRATEGY_REPLAY",
                        "target": target,
                        "target_group": target,
                        "dataset_id": (packed.get(target) or {}).get("dataset_id"),
                        "timeframe": "D1",
                        "role": role,
                        "scenario": "base",
                        "metrics": metrics,
                        "live_external_dependency": mech.get("live_external") or "NO",
                        "data_cost": 0.0,
                    }
                )
        else:
            for role, arm in (("research", research_m), ("validation", validation_m)):
                rows.append(
                    {
                        "strategy_id": hid,
                        "family": mech["family"],
                        "information_set": mech["information_set"],
                        "replay_kind": "ALPHA_TEST",
                        "target": target,
                        "role": role,
                        "scenario": "base",
                        "metrics": arm,
                        "status": "NON_TRADEABLE" if not arm.get("trade_count") else None,
                        "note": "Evaluator did not persist a cash curve; frozen arm metrics only.",
                        "live_external_dependency": mech.get("live_external") or "NO",
                        "data_cost": 0.0,
                    }
                )
        status = economic_status(research_m, validation_m)
        for row in rows:
            if row.get("strategy_id") == hid and row.get("economic_status") is None:
                row["economic_status"] = status
    return rows


def replay_all_families(iters_boot=1, iters_perm=1):
    all_rows = []
    for mech in strategy_families():
        if mech.get("module") in ("profit", "cross_asset", "cross_residual"):
            continue
        all_rows.extend(replay_generic(mech, iters_boot=iters_boot, iters_perm=iters_perm))
    return all_rows
