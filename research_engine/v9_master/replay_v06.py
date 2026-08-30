"""Replay locked V0.6 strategies. Does not edit frozen result JSON."""
from __future__ import print_function

import os

from research_engine.io_util import load_json
from research_engine.profit.backtest.engine import run_backtest
from research_engine.profit.contract import assert_search_space, strategy_map
from research_engine.profit.cost.model import fill_price
from research_engine.profit.market_state.labels import state_series
from research_engine.profit.risk.sizing import stop_distance
from research_engine.v9_master import START_EQUITY
from research_engine.v9_master.cost_overlay import CostOverlay
from research_engine.v9_master.enrich import enrich_path_trade
from research_engine.v9_master.metrics_v9 import economic_status, extend_metrics
from research_engine.v9_master.paths import IMMUTABLE, RESEARCH
from research_engine.v9_master.persist import persist_book
from research_protocol.bars import load_dataset
from research_protocol.windows import candidate_window

CORE_DATASETS = [
    "tm-market-GOLD-M15-20260825-000001",
    "tm-market-GOLD-H1-20260825-000001",
    "tm-market-GOLD-H4-20260825-000001",
    "tm-market-GOLD-D1-20260825-000001",
    "tm-market-EURUSD-M15-20260825-000001",
    "tm-market-EURUSD-H1-20260825-000001",
    "tm-market-EURUSD-H4-20260825-000001",
    "tm-market-EURUSD-D1-20260825-000001",
    "tm-market-USDJPY-M15-20260825-000001",
    "tm-market-USDJPY-H1-20260825-000001",
    "tm-market-USDJPY-H4-20260825-000001",
    "tm-market-USDJPY-D1-20260825-000001",
    "tm-market-OIL-M15-20260825-000001",
    "tm-market-OIL-H1-20260825-000001",
    "tm-market-OIL-H4-20260825-000001",
    "tm-market-OIL-D1-20260825-000001",
]

LOGICAL = {
    "GOLD": "GOLD",
    "EURUSD": "FX",
    "USDJPY": "FX",
    "OIL": "OIL",
}

PRIMARY = [{"id": "base", "cost_mult": 1.0, "slip_bp": 10.0}]
SENSITIVITY = [
    {"id": "cost_1p5x", "cost_mult": 1.5, "slip_bp": 10.0},
    {"id": "cost_2x", "cost_mult": 2.0, "slip_bp": 10.0},
    {"id": "slip_0bp", "cost_mult": 1.0, "slip_bp": 0.0},
    {"id": "slip_20bp", "cost_mult": 1.0, "slip_bp": 20.0},
]


def _space():
    path = os.path.join(RESEARCH, "profit_discovery", "PROFIT_SEARCH_SPACE_V0.6.json")
    space = load_json(path)
    assert_search_space(space)
    return space


def _logical(dataset_id):
    if "GOLD" in dataset_id:
        return "GOLD"
    if "OIL" in dataset_id:
        return "OIL"
    if "EURUSD" in dataset_id:
        return "EURUSD"
    if "USDJPY" in dataset_id:
        return "USDJPY"
    return None


def _tf(dataset_id):
    for tf in ("M15", "H1", "H4", "D1"):
        if "-%s-" % tf in dataset_id:
            return tf
    return "D1"


def _enrich_trades(bars, trades):
    out = []
    for tr in trades or []:
        side = tr.get("side")
        entry_i = tr.get("entry_index")
        if tr.get("reason") == "STOP" and entry_i is not None and side:
            entry_bar = bars[entry_i] if entry_i < len(bars) else None
            entry = fill_price(entry_bar, side, False) if entry_bar else None
            dist = stop_distance(bars, tr.get("signal_t") or 0, entry)
            if entry is not None and dist is not None:
                tr = dict(tr)
                tr["entry"] = entry
                tr["exit"] = entry - dist if side > 0 else entry + dist
        out.append(enrich_path_trade(bars, tr, side))
    return out


def _run_one(bars, window, role, states, strat, timeframe, scenario):
    with CostOverlay(scenario["cost_mult"], scenario["slip_bp"]):
        raw = run_backtest(bars, window, role, states, strat, timeframe, start_equity=START_EQUITY)
    trades = _enrich_trades(bars, raw.get("trades") or [])
    curve = raw.get("equity_curve") or [START_EQUITY]
    metrics = extend_metrics(curve, timeframe, START_EQUITY, trades, bars)
    metrics["scenario"] = scenario["id"]
    metrics["cost_mult"] = scenario["cost_mult"]
    metrics["slippage_bp"] = scenario["slip_bp"]
    metrics["strategy_id"] = strat["strategy_id"]
    metrics["family"] = "PROFIT_DISCOVERY_V0.6"
    metrics["information_set"] = "IS-A"
    metrics["replay_kind"] = "STRATEGY_REPLAY"
    metrics["execution_model"] = "EXECUTION_APPROXIMATION"
    metrics["live_external_dependency"] = "NO"
    persist_book(strat["strategy_id"], window.get("dataset_id") or timeframe, role, scenario["id"], curve, trades, metrics, bars)
    return {"metrics": metrics, "curve": curve, "trades": trades}


def replay_v06(include_sensitivity=True):
    space = _space()
    smap = strategy_map(space)
    scenarios = list(PRIMARY)
    if include_sensitivity:
        scenarios.extend(SENSITIVITY)
    rows = []
    for dataset_id in CORE_DATASETS:
        path = os.path.join(IMMUTABLE, dataset_id)
        if not os.path.isdir(path):
            continue
        manifest, bars, _sha = load_dataset(path)
        window = candidate_window(manifest, bars)
        window["dataset_id"] = dataset_id
        states, _cuts = state_series(bars, window)
        tf = manifest.get("timeframe") or _tf(dataset_id)
        logical = manifest.get("logical_symbol") or _logical(dataset_id)
        for sid, strat in smap.items():
            by_role = {}
            for role in ("research", "validation"):
                for scenario in scenarios:
                    out = _run_one(bars, window, role, states, strat, tf, scenario)
                    if scenario["id"] == "base":
                        by_role[role] = out["metrics"]
                    rows.append(
                        {
                            "strategy_id": sid,
                            "family": "PROFIT_DISCOVERY_V0.6",
                            "information_set": "IS-A",
                            "replay_kind": "STRATEGY_REPLAY",
                            "target": logical,
                            "target_group": LOGICAL.get(logical) or logical,
                            "dataset_id": dataset_id,
                            "timeframe": tf,
                            "role": role,
                            "scenario": scenario["id"],
                            "metrics": out["metrics"],
                            "live_external_dependency": "NO",
                            "data_cost": 0.0,
                        }
                    )
            status = economic_status(by_role.get("research"), by_role.get("validation"))
            for row in rows:
                if row["strategy_id"] == sid and row["dataset_id"] == dataset_id and row.get("economic_status") is None:
                    if row["scenario"] == "base":
                        row["economic_status"] = status
    return rows
