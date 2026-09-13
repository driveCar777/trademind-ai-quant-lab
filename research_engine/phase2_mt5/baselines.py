"""Unified GOLD baselines. No ML. Write-once READ. RESEARCH window only for official numbers."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from research_engine.hot_mt5_products.features import _atr, _sma, load_d1
from research_engine.hot_mt5_gold_h1.data import load_h1
from research_engine.phase2_mt5 import (
    BROKER_SYMBOL,
    FINAL_OOS_START,
    RESEARCH_END,
    SEED,
    SLIP_ASSUMED,
)
from research_engine.phase2_mt5.costs import breakdown, cost_mult_of, load_meta, notes
from research_engine.phase2_mt5.hashes import code_hash, sha256_file, sha256_files
from research_engine.phase2_mt5.labels import summarize
from research_engine.phase2_mt5.ledger import write_once
from research_engine.phase2_mt5.metrics import from_returns, monthly_from_equity, path_mfe_mae
from research_engine.phase2_mt5.paths import LIVE_HIST, RES, ensure

COST_NAMES = ("base", "2x", "3x", "stress")


def _force() -> bool:
    return os.environ.get("TRADEMIND_PHASE2_FORCE") == "1"


def load_bars(timeframe: str, path: Optional[Path] = None) -> Dict[str, np.ndarray]:
    if timeframe == "D1":
        p = path or (LIVE_HIST / "GOLD_D1.csv")
        bar = load_d1(p)
        bar["ts"] = [d + "T00:00:00Z" for d in bar["dates"]]
        return bar
    if timeframe == "H1":
        p = path or (LIVE_HIST / "GOLD_H1.csv")
        return load_h1(p)
    raise ValueError("timeframe %s not implemented in this run" % timeframe)


def _side_arrays(bar: Dict[str, np.ndarray], look_m: int, look_bo: int, vol_w: int, sma_w: int) -> Dict[str, np.ndarray]:
    c, h, l = bar["close"], bar["high"], bar["low"]
    n = len(c)
    r = np.full(n, np.nan)
    r[look_m:] = c[look_m:] / c[:-look_m] - 1.0
    mom = np.sign(r)
    mom[r == 0] = 0.0
    mr = -mom
    bo = np.zeros(n)
    for i in range(look_bo, n):
        mx = np.max(h[i - look_bo:i])
        mn = np.min(l[i - look_bo:i])
        if c[i] > mx:
            bo[i] = 1.0
        elif c[i] < mn:
            bo[i] = -1.0
    atr = _atr(h, l, c, 14)
    atrp = atr / np.maximum(1e-12, c)
    vol_ok = np.zeros(n, dtype=bool)
    for i in range(vol_w, n):
        med = np.nanmedian(atrp[i - vol_w + 1:i + 1])
        vol_ok[i] = bool(np.isfinite(atrp[i]) and np.isfinite(med) and atrp[i] > med)
    sma = _sma(c, sma_w)
    trend_ok = c > sma
    vol_f = np.where(vol_ok, mom, 0.0)
    trend_f = np.where(trend_ok, mom, 0.0)
    return {
        "MOMENTUM": mom,
        "MEAN_REVERSION": mr,
        "BREAKOUT": bo,
        "VOL_FILTER": vol_f,
        "TREND_FILTER": trend_f,
    }


def _random_sides(n: int, seed: int = SEED) -> np.ndarray:
    rng = np.random.RandomState(seed)
    return rng.choice(np.array([-1.0, 0.0, 1.0]), size=n)


def _slice_i(dates: List[str], end: str) -> int:
    last = -1
    for i, d in enumerate(dates):
        if d[:10] <= end:
            last = i
    return last


def book_sides(
    bar: Dict[str, np.ndarray],
    meta: Dict[str, Any],
    sides: np.ndarray,
    hold: int,
    start_i: int,
    end_i: int,
    cost_name: str = "base",
    slip: float = SLIP_ASSUMED,
) -> Tuple[List[Dict[str, Any]], List[float]]:
    dates = bar["dates"]
    o, h, l = bar["open"], bar["high"], bar["low"]
    n = len(dates)
    mult, extra = cost_mult_of(cost_name)
    trades = []
    t = start_i
    while t + hold + 1 < n and t <= end_i:
        side = float(sides[t]) if t < len(sides) else 0.0
        if not np.isfinite(side) or side == 0:
            t += 1
            continue
        if not np.isfinite(o[t + 1]) or not np.isfinite(o[t + 1 + hold]) or o[t + 1] <= 0:
            t += 1
            continue
        side_i = 1 if side > 0 else -1
        t_in, t_out = t + 1, t + 1 + hold
        raw = (o[t_out] / o[t_in] - 1.0) * side_i
        bd = breakdown(bar, meta, t_in, t_out, side_i, dates, slip=slip, cost_mult=mult, stress_extra=extra)
        net = float(raw - bd["cost"])
        path = path_mfe_mae(h, l, float(o[t_in]), t_in, t_out, side_i)
        trades.append({
            "signal": dates[t],
            "entry": dates[t_in],
            "exit": dates[t_out],
            "side": "LONG" if side_i > 0 else "SHORT",
            "gross": float(raw),
            "net": net,
            "cost": bd["cost"],
            "spread_cost": bd["spread_cost"],
            "slip_cost": bd["slip_cost"],
            "commission": bd["commission"],
            "swap": bd["swap"],
            "mfe": path["mfe"],
            "mae": path["mae"],
            "max_dd_during_trade": path["max_dd_during_trade"],
        })
        t = t_out
    return trades, [tr["net"] for tr in trades]


def buy_hold_trade(
    bar: Dict[str, np.ndarray],
    meta: Dict[str, Any],
    start_i: int,
    end_i: int,
    cost_name: str = "base",
) -> List[Dict[str, Any]]:
    dates, o, h, l = bar["dates"], bar["open"], bar["high"], bar["low"]
    t_in = start_i + 1
    t_out = end_i
    if t_out <= t_in or o[t_in] <= 0:
        return []
    raw = float(o[t_out] / o[t_in] - 1.0)
    mult, extra = cost_mult_of(cost_name)
    bd = breakdown(bar, meta, t_in, t_out, 1, dates, cost_mult=mult, stress_extra=extra)
    path = path_mfe_mae(h, l, float(o[t_in]), t_in, t_out, 1)
    return [{
        "signal": dates[start_i],
        "entry": dates[t_in],
        "exit": dates[t_out],
        "side": "LONG",
        "gross": raw,
        "net": float(raw - bd["cost"]),
        "cost": bd["cost"],
        "spread_cost": bd["spread_cost"],
        "slip_cost": bd["slip_cost"],
        "commission": bd["commission"],
        "swap": bd["swap"],
        "mfe": path["mfe"],
        "mae": path["mae"],
        "max_dd_during_trade": path["max_dd_during_trade"],
    }]


def daily_equity(bar: Dict[str, np.ndarray], start_i: int, end_i: int) -> Tuple[List[str], np.ndarray]:
    """Buy-hold daily mark from close, research window only. Market fact, not a searched family."""
    c = bar["close"]
    dates = bar["dates"]
    a = max(0, start_i)
    b = min(len(c) - 1, end_i)
    px = c[a:b + 1]
    eq = px / px[0]
    return dates[a:b + 1], eq


def trade_equity(trades: List[Dict[str, Any]]) -> Tuple[List[str], np.ndarray]:
    if not trades:
        return [], np.array([])
    eq = [1.0]
    days = [trades[0]["entry"]]
    cur = 1.0
    for tr in trades:
        cur *= 1.0 + float(tr["net"])
        eq.append(cur)
        days.append(tr["exit"])
    return days, np.array(eq, dtype=np.float64)


def exposure_and_turnover(trades: List[Dict[str, Any]], n_bars: int, hold: int) -> Dict[str, float]:
    held = sum(hold for _ in trades)
    return {
        "n_trades": float(len(trades)),
        "turnover": float(len(trades)),
        "exposure": float(held) / float(max(1, n_bars)),
    }


def _spec_for_tf(timeframe: str) -> Dict[str, Any]:
    if timeframe == "D1":
        return {
            "experiment_id": "EXP-001",
            "hold": 20,
            "look_m": 20,
            "look_bo": 20,
            "vol_w": 60,
            "sma_w": 50,
            "bars_year": 252.0,
            "warmup": 60,
            "contract": "docs/research_engine/EXP001_GOLD_D1_OWNPRICE_CONTRACT.md",
        }
    return {
        "experiment_id": "EXP-002",
        "hold": 24,
        "look_m": 24,
        "look_bo": 24,
        "vol_w": 72,
        "sma_w": 120,
        "bars_year": 252.0 * 24.0,
        "warmup": 120,
        "contract": "docs/research_engine/EXP002_GOLD_H1_PIT_CONTRACT.md",
    }


def run_timeframe(timeframe: str, bar: Optional[Dict[str, np.ndarray]] = None, out_dir: Optional[Path] = None) -> Dict[str, Any]:
    ensure()
    spec = _spec_for_tf(timeframe)
    hold = spec["hold"]
    if bar is None:
        bar = load_bars(timeframe)
    meta = load_meta()
    dates = bar["dates"]
    end_i = _slice_i(dates, RESEARCH_END)
    if end_i < spec["warmup"] + hold + 2:
        raise RuntimeError("RESEARCH window too short")
    start_i = spec["warmup"]
    n_res = end_i - start_i + 1
    val_cut = start_i + int(0.70 * n_res)
    sides = _side_arrays(bar, spec["look_m"], spec["look_bo"], spec["vol_w"], spec["sma_w"])
    always_long = np.ones(len(dates))
    always_short = -np.ones(len(dates))
    rnd = _random_sides(len(dates))
    books = {
        "ALWAYS_LONG": always_long,
        "ALWAYS_SHORT": always_short,
        "RANDOM": rnd,
        **sides,
    }
    families = {}
    for name, arr in books.items():
        trades, nets = book_sides(bar, meta, arr, hold, start_i, end_i, "base")
        res_tr = [t for t in trades if t["signal"][:10] <= dates[val_cut][:10]]
        oos_tr = [t for t in trades if t["signal"][:10] > dates[val_cut][:10]]
        days, eq = trade_equity(trades)
        monthly = monthly_from_equity(days, eq) if len(eq) else {"n": 0}
        expo = exposure_and_turnover(trades, n_res, hold)
        families[name] = {
            "research": from_returns(nets, hold, spec["bars_year"]),
            "research_70": from_returns([t["net"] for t in res_tr], hold, spec["bars_year"]),
            "research_30": from_returns([t["net"] for t in oos_tr], hold, spec["bars_year"]),
            "monthly": {k: monthly[k] for k in monthly if k != "returns"},
            "monthly_returns": monthly.get("returns") or [],
            "economic": summarize(trades, cost_buffer=0.0020),
            "exposure": expo,
            "n_long": sum(1 for t in trades if t["side"] == "LONG"),
            "n_short": sum(1 for t in trades if t["side"] == "SHORT"),
            "n_flat_decisions": int(np.sum(arr[start_i:end_i + 1] == 0)) if name != "ALWAYS_LONG" else 0,
            "stress": {},
        }
        for cn in COST_NAMES:
            if cn == "base":
                continue
            _, nets_s = book_sides(bar, meta, arr, hold, start_i, end_i, cn)
            families[name]["stress"][cn] = from_returns(nets_s, hold, spec["bars_year"])
        # keep trade list only for MOMENTUM / BUY_HOLD later
        if name == "MOMENTUM":
            families[name]["trades_head"] = trades[:3]
            families[name]["trades_tail"] = trades[-3:]

    bh = buy_hold_trade(bar, meta, start_i, end_i, "base")
    bh_days, bh_eq = daily_equity(bar, start_i + 1, end_i)
    bh_month = monthly_from_equity(bh_days, bh_eq)
    bh_hold = max(1, end_i - (start_i + 1))
    families["BUY_HOLD"] = {
        "research": from_returns([t["net"] for t in bh], bh_hold, spec["bars_year"]),
        "research_70": None,
        "research_30": None,
        "monthly": {k: bh_month[k] for k in bh_month if k != "returns"},
        "monthly_returns": bh_month.get("returns") or [],
        "economic": summarize(bh, cost_buffer=0.0020),
        "exposure": {"n_trades": 1.0, "turnover": 1.0, "exposure": 1.0},
        "n_long": 1,
        "n_short": 0,
        "gross_open_to_open": bh[0]["gross"] if bh else None,
        "net_open_to_open": bh[0]["net"] if bh else None,
        "daily_mark_total": float(bh_eq[-1] - 1.0) if len(bh_eq) else None,
        "stress": {},
    }
    for cn in COST_NAMES:
        if cn == "base":
            continue
        extra = buy_hold_trade(bar, meta, start_i, end_i, cn)
        families["BUY_HOLD"]["stress"][cn] = from_returns([t["net"] for t in extra], bh_hold, spec["bars_year"])

    csv_path = LIVE_HIST / ("GOLD_%s.csv" % timeframe)
    meta_path = LIVE_HIST / "GOLD_META.json"
    used = [p for p in (csv_path, meta_path) if p.is_file()]
    data_h = sha256_files(used) if used else ""
    code_h = code_hash()
    report = {
        "experiment_id": spec["experiment_id"],
        "profile": "PHASE2_UNIFIED_BASELINES",
        "candidate": False,
        "level1": False,
        "order_send": False,
        "writes_9000": False,
        "grok_is_strategy": False,
        "timeframe": timeframe,
        "symbol": BROKER_SYMBOL,
        "research_end": RESEARCH_END,
        "final_oos_start": FINAL_OOS_START,
        "final_oos_evaluated": False,
        "n_bars_full": len(dates),
        "first": dates[0],
        "last": dates[-1],
        "research_first": dates[start_i],
        "research_last": dates[end_i],
        "n_research_bars": n_res,
        "hold": hold,
        "seed": SEED,
        "slip_assumed": SLIP_ASSUMED,
        "cost_notes": notes(meta),
        "broker_meta": {k: meta.get(k) for k in (
            "broker", "point", "spread_points_now", "swap_mode", "swap_long",
            "swap_short", "contract_size", "volume_min", "assumed", "source",
        )},
        "contract": spec["contract"],
        "data_hash": data_h,
        "code_hash": code_h,
        "families": families,
        "verdict": "BASELINES_ONLY_NOT_CANDIDATE",
        "note": (
            "Official numbers use RESEARCH through %s. FINAL OOS from %s is locked "
            "and was not used to select or rank families."
            % (RESEARCH_END, FINAL_OOS_START)
        ),
    }
    dest_dir = out_dir or (RES / ("%s_baselines" % timeframe.lower()))
    dest_dir.mkdir(parents=True, exist_ok=True)
    read_path = dest_dir / "READ.json"
    if read_path.is_file() and not _force():
        existing = json.loads(read_path.read_text(encoding="utf-8"))
        existing["write_once_refused"] = True
        return existing
    body = json.dumps(report, ensure_ascii=False, indent=2)
    write_once(report, read_path)
    from research_engine.phase2_mt5.hashes import sha256_bytes
    report["result_hash"] = sha256_bytes(body.encode("utf-8"))
    read_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    # compact trades for momentum only
    mom_tr, _ = book_sides(bar, meta, sides["MOMENTUM"], hold, start_i, end_i, "base")
    (dest_dir / "MOMENTUM_trades.json").write_text(json.dumps(mom_tr, ensure_ascii=False), encoding="utf-8")
    (dest_dir / "BUY_HOLD_trades.json").write_text(json.dumps(bh, ensure_ascii=False), encoding="utf-8")
    return report


def run_all(out_dir: Optional[Path] = None) -> Dict[str, Any]:
    d1 = run_timeframe("D1", out_dir=out_dir)
    h1 = run_timeframe("H1", out_dir=out_dir)
    return {"D1": d1, "H1": h1}


if __name__ == "__main__":
    ensure()
    print("running D1 baselines…")
    d1 = run_timeframe("D1")
    print("D1 BUY_HOLD net", (d1.get("families") or {}).get("BUY_HOLD", {}).get("net_open_to_open"))
    print("running H1 baselines…")
    h1 = run_timeframe("H1")
    print("H1 BUY_HOLD net", (h1.get("families") or {}).get("BUY_HOLD", {}).get("net_open_to_open"))
