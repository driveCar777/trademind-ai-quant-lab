"""V0.8 / V0.91 / predictive-only replay. Existing rules only."""
from __future__ import print_function

import os

from research_engine.cross_asset import PARENTS as XA_PARENTS
from research_engine.cross_asset.align import build_alignment, load_parents_from_dirs
from research_engine.cross_asset.evaluate import evaluate_hypothesis as xa_evaluate
from research_engine.cross_asset.space import hypothesis_map as xa_map
from research_engine.cross_residual.align import align_gold_oil
from research_engine.cross_residual.evaluate import two_leg_return
from research_engine.cross_residual.residual import build_residual, freeze_residual_cuts, signal_at
from research_engine.cross_residual.space import HYPOTHESIS_SPECS
from research_engine.io_util import load_json
from research_engine.v9_master import START_EQUITY
from research_engine.v9_master.capture import BookCapture
from research_engine.v9_master.enrich import enrich_family_trade
from research_engine.v9_master.metrics_v9 import economic_status, extend_metrics
from research_engine.v9_master.paths import IMMUTABLE, RESEARCH
from research_engine.v9_master.persist import persist_book


def replay_cross_asset():
    rows = []
    space = load_json(os.path.join(RESEARCH, "cross_asset", "CROSS_ASSET_SEARCH_SPACE_V0.8.json"))
    dir_map = {}
    for dataset_id in XA_PARENTS:
        dir_map[dataset_id] = os.path.join(IMMUTABLE, dataset_id)
    loaded, hashes = load_parents_from_dirs(dir_map)
    pack = build_alignment(loaded, hashes)
    hmap = xa_map(space)
    for hid, spec in hmap.items():
        cap = BookCapture()
        cap.start()
        try:
            result = xa_evaluate(pack, spec, iters_boot=1, iters_perm=1)
        finally:
            cap.stop()
        target = spec.get("target_asset")
        research_m = result.get("research") or {}
        validation_m = result.get("validation") or {}
        status = economic_status(research_m, validation_m)
        for i, role in enumerate(("research", "validation")):
            if i < len(cap.calls):
                call = cap.calls[i]
                trades = [enrich_family_trade(tr) for tr in call.get("trades") or []]
                curve = call.get("curve") or [START_EQUITY]
                metrics = extend_metrics(curve, "D1", START_EQUITY, trades, None)
            else:
                trades = []
                curve = [START_EQUITY]
                metrics = dict(research_m if role == "research" else validation_m)
            metrics["family"] = "CROSS_ASSET_V0.8"
            metrics["strategy_id"] = hid
            metrics["information_set"] = "IS-A"
            persist_book(hid, target or "XA", role, "base", curve, trades, metrics, None)
            rows.append(
                {
                    "strategy_id": hid,
                    "family": "CROSS_ASSET_V0.8",
                    "information_set": "IS-A",
                    "replay_kind": "STRATEGY_REPLAY",
                    "target": target,
                    "timeframe": "D1",
                    "role": role,
                    "scenario": "base",
                    "metrics": metrics,
                    "economic_status": status,
                    "live_external_dependency": "NO",
                    "data_cost": 0.0,
                }
            )
    return rows


def replay_residual():
    aligned = align_gold_oil(IMMUTABLE)
    rows_in = build_residual(aligned["rows"])
    cuts = freeze_residual_cuts(rows_in)
    out = []
    for hid, spec in HYPOTHESIS_SPECS.items():
        by_role = {}
        for role in ("research", "validation"):
            cash = float(START_EQUITY)
            curve = []
            trades = []
            next_free = 0
            i = 0
            while i < len(rows_in):
                row = rows_in[i]
                if row.get("role") == role:
                    side = signal_at(row, spec, cuts)
                    if side != 0 and i >= next_free:
                        step = two_leg_return(rows_in, i, side)
                        if step is not None:
                            pnl = cash * float(step["step_return"])
                            cash = cash + pnl
                            if cash < 0:
                                cash = 0.0
                            trades.append(
                                enrich_family_trade(
                                    {
                                        "date": row.get("date") or row.get("timestamp_utc"),
                                        "entry_index": step.get("entry_index"),
                                        "exit_index": step.get("exit_index"),
                                        "side": side,
                                        "pnl": pnl,
                                        "net_pnl": pnl,
                                        "step_return": step.get("step_return"),
                                    }
                                )
                            )
                            next_free = step.get("exit_index") or (i + 5)
                    curve.append(cash)
                i += 1
            metrics = extend_metrics(curve if curve else [START_EQUITY], "D1", START_EQUITY, trades, rows_in)
            metrics["family"] = "CROSS_RESIDUAL_V0.91"
            metrics["strategy_id"] = hid
            metrics["information_set"] = "IS-A"
            persist_book(hid, "GOLD_OIL", role, "base", curve if curve else [START_EQUITY], trades, metrics, rows_in)
            by_role[role] = metrics
            out.append(
                {
                    "strategy_id": hid,
                    "family": "CROSS_RESIDUAL_V0.91",
                    "information_set": "IS-A",
                    "replay_kind": "STRATEGY_REPLAY",
                    "target": "GOLD_OIL",
                    "timeframe": "D1",
                    "role": role,
                    "scenario": "base",
                    "metrics": metrics,
                    "live_external_dependency": "NO",
                    "data_cost": 0.0,
                }
            )
        status = economic_status(by_role.get("research"), by_role.get("validation"))
        for row in out:
            if row["strategy_id"] == hid:
                row["economic_status"] = status
    return out


def _safe_load(*parts):
    path = os.path.join(*parts)
    if not os.path.isfile(path):
        return None
    return load_json(path)


def replay_predictive_only():
    rows = []
    hyp = _safe_load(RESEARCH, "FAILED_ALPHA_DATABASE_V2.json")
    rows.append(
        {
            "strategy_id": "HYP-0001",
            "family": "HYP-0001",
            "information_set": "IS-A",
            "replay_kind": "PREDICTIVE_ONLY",
            "status": "NON_TRADEABLE",
            "economic_status": "LOSS",
            "note": "PREDICTIVE_ONLY. Frozen 14:11. Not a strategy. No CAGR computed.",
            "live_external_dependency": "NO",
            "data_cost": 0.0,
        }
    )
    fd = _safe_load(RESEARCH, "factor_discovery", "FACTOR_RANKING_V0.1.json")
    rows.append(
        {
            "strategy_id": "FACTOR_DISCOVERY_V0.1",
            "family": "FACTOR_DISCOVERY_V0.1",
            "information_set": "IS-A",
            "replay_kind": "FACTOR_ONLY",
            "status": "NON_TRADEABLE",
            "note": "Factor performance only. No strategy CAGR.",
            "frozen": None if fd is None else {"outcome": fd.get("outcome") or fd.get("program_outcome")},
            "live_external_dependency": "NO",
            "data_cost": 0.0,
        }
    )
    v05 = _safe_load(RESEARCH, "strategy_discovery", "STRATEGY_RANKING_V0.5.json")
    rows.append(
        {
            "strategy_id": "STRATEGY_DISCOVERY_V0.5",
            "family": "STRATEGY_DISCOVERY_V0.5",
            "information_set": "IS-A",
            "replay_kind": "PREDICTIVE_ONLY",
            "status": "NON_TRADEABLE",
            "note": "NEXT_CLOSED_BAR close-to-close screen. Not a trade book. No strategy CAGR.",
            "frozen": None if v05 is None else {"outcome": v05.get("outcome") or v05.get("program_outcome")},
            "live_external_dependency": "NO",
            "data_cost": 0.0,
        }
    )
    return rows
