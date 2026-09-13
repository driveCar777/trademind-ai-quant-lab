"""GOLD H1: one ML book + one 120h TSMOM book. Swap counts midnights, not each hour."""
from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research_engine.hot_mt5_gold_h1.data import build_h1_matrix, load_h1
from research_engine.hot_mt5_gold_h1.paths import HIST, RES
from research_engine.hot_mt5_products.products import LGBM_PARAMS, SLIP, VAL_FRAC

HOLD = 24
MOM_LB = 120
FIRST_PRED = 2000
REFIT_EVERY = 1000
MIN_HIST = 1500
EMBARGO = HOLD + 1
MIN_COVERAGE = 0.15
MIN_VAL_TRADES = 8
PROFILE = "HOT_MT5_GOLD_H1_V1"


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES


def _meta() -> Dict[str, Any]:
    p = HIST / "GOLD_META.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"point": 0.01, "swap_mode": 1, "swap_long": -1.54, "swap_short": 0.64,
            "swap_rollover3days": 5, "spread_points_now": 34, "bid": 4300.0}


def _nights(ts: List[str], t_in: int, t_out: int, roll: int) -> float:
    nights = 0.0
    prev = ts[t_in][:10]
    last = min(t_out, len(ts) - 1)
    for u in range(t_in + 1, last + 1):
        d = ts[u][:10]
        if d != prev:
            wd = dt.date.fromisoformat(prev).isoweekday()
            nights += 3.0 if wd == roll else 1.0
            prev = d
    return nights


def _fill_cost(bar, meta, t_in, t_out, side) -> float:
    ts, o = bar["ts"], bar["open"]
    px = float(o[t_in])
    pt = float(meta.get("point") or 0.01)
    raw = float(bar["spread"][t_in]) * pt / max(1e-12, float(bar["close"][t_in]))
    now = float(meta.get("spread_points_now") or 0) * pt / max(1e-12, float(meta.get("bid") or px))
    spread = max(0.0, now) if (not np.isfinite(raw) or raw <= 0) else max(raw, now * 0.25)
    nights = _nights(ts, t_in, t_out, int(meta.get("swap_rollover3days") or 5))
    sw = float(meta["swap_long"] if side > 0 else meta["swap_short"])
    mode = int(meta.get("swap_mode") or 1)
    if mode == 1:
        swap_frac = sw * pt / max(1e-12, px) * nights
    elif mode == 5:
        swap_frac = sw / 100.0 * nights / 365.0
    else:
        swap_frac = 0.0
    return spread + 2 * SLIP - swap_frac


def _summ(rets: List[float], hold: int, cal_yrs: Optional[float] = None) -> Dict[str, Any]:
    x = np.array(rets, dtype=np.float64)
    empty = {"n_periods": 0, "twr": None, "cagr": None, "mean": None, "t": None,
             "hit": None, "maxdd": None, "payoff": None}
    if len(x) == 0:
        return empty
    eq = np.cumprod(1.0 + x)
    yrs = cal_yrs if cal_yrs and cal_yrs > 0 else max(1e-9, len(x) * hold / (252.0 * 24))
    peak = np.maximum.accumulate(eq)
    dd = float(np.min(eq / peak - 1.0))
    t = float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else None
    wins, loss = x[x > 0], x[x <= 0]
    payoff = float(wins.mean() / (-loss.mean())) if len(wins) and len(loss) and loss.mean() < 0 else None
    return {
        "n_periods": int(len(x)), "twr": float(eq[-1] - 1.0),
        "cagr": float(eq[-1] ** (1.0 / max(1e-9, yrs)) - 1.0),
        "mean": float(x.mean()), "t": t, "hit": float((x > 0).mean()),
        "maxdd": dd, "payoff": payoff,
    }


def walk_scores(x: np.ndarray, y: np.ndarray, names: List[str]) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    import warnings
    import lightgbm as lgb
    warnings.filterwarnings("ignore", message="X does not have valid feature names")
    t_n = x.shape[0]
    scores = np.full(t_n, np.nan)
    t = FIRST_PRED
    refits = []
    while t < t_n:
        cutoff = t - EMBARGO
        if cutoff < MIN_HIST:
            t += 1
            continue
        ok = np.all(np.isfinite(x[:cutoff]), axis=1) & np.isfinite(y[:cutoff])
        if int(ok.sum()) < 200:
            t += 1
            continue
        model = lgb.LGBMRegressor(**LGBM_PARAMS)
        model.fit(x[:cutoff][ok], np.clip(y[:cutoff][ok], -5, 5), feature_name=names)
        end = min(t_n, t + REFIT_EVERY)
        for u in range(t, end):
            if np.all(np.isfinite(x[u])):
                scores[u] = float(model.predict(x[u].reshape(1, -1))[0])
        refits.append({"fit_at_i": t, "rows": int(ok.sum()), "through_i": end - 1})
        t = end
    return scores, refits


def book(bar, meta, side_fn, start_i: int, end_i: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    ts, o = bar["ts"], bar["open"]
    n = len(ts)
    trades = []
    t = start_i
    last = min(end_i, n - HOLD - 2)
    while t <= last:
        side = side_fn(t)
        if side == 0:
            t += 1
            continue
        t_in, t_out = t + 1, t + 1 + HOLD
        if t_out >= n or o[t_in] <= 0 or not np.isfinite(o[t_in]) or not np.isfinite(o[t_out]):
            t += 1
            continue
        raw = (o[t_out] / o[t_in] - 1.0) * side
        cost = _fill_cost(bar, meta, t_in, t_out, side)
        trades.append({
            "signal": ts[t], "entry": ts[t_in], "exit": ts[t_out],
            "side": "LONG" if side > 0 else "SHORT",
            "raw": float(raw), "cost": float(cost), "net": float(raw - cost),
        })
        t = t_out
    span = max(1, last - start_i + 1)
    try:
        d0 = dt.date.fromisoformat(ts[start_i][:10])
        d1 = dt.date.fromisoformat(ts[min(last + HOLD, n - 1)][:10])
        cal_yrs = max(1e-9, (d1 - d0).days / 365.25)
    except Exception:
        cal_yrs = None
    stats = _summ([tr["net"] for tr in trades], HOLD, cal_yrs)
    stats["coverage"] = float(len(trades) * HOLD) / float(span)
    return stats, trades


def _gate(val_s: Dict[str, Any]) -> Tuple[str, Optional[str], bool]:
    cover_fail = bool((val_s.get("n_periods") or 0) < MIN_VAL_TRADES or (val_s.get("coverage") or 0) < MIN_COVERAGE)
    viable = bool(not cover_fail and (val_s.get("twr") or 0) > 0 and (val_s.get("t") or 0) > 1.0)
    if cover_fail:
        return "NO_CANDIDATE", "VALIDATION_COVERAGE", False
    if viable:
        return "VIABLE_HISTORICAL", None, True
    return "NO_CANDIDATE", "VALIDATION_GATE", False


def _window_reports(bar, meta, side_fn, first, val_i, n):
    long_s, long_tr = book(bar, meta, side_fn, first, n)
    res_s, _ = book(bar, meta, side_fn, first, val_i - 1)
    val_s, _ = book(bar, meta, side_fn, val_i, n)
    verdict, deny, viable = _gate(val_s)
    month = [tr for tr in long_tr if tr["signal"][:10] >= "2026-08-11"]
    return {
        "long_sample": long_s, "research_70": res_s, "validation_30": val_s,
        "last_month_diagnostic": _summ([tr["net"] for tr in month], HOLD),
        "verdict": verdict, "deny": deny, "viable_historical": viable,
        "n_trades_long": len(long_tr), "trades": long_tr,
    }


def run() -> Dict[str, Any]:
    print("GOLD H1 train", flush=True)
    ensure()
    path = HIST / "GOLD_H1.csv"
    if not path.is_file():
        return {"ok": False, "error": "NO_H1"}
    bar = load_h1(path)
    names, x = build_h1_matrix(bar)
    o = bar["open"]
    n = len(o)
    y = np.full(n, np.nan)
    y[: -(HOLD + 1)] = o[HOLD + 1:] / o[1:-HOLD] - 1.0
    scores, refits = walk_scores(x, y, names)
    close = bar["close"]
    mom = np.full(n, np.nan)
    mom[MOM_LB:] = close[MOM_LB:] / close[:-MOM_LB] - 1.0

    def ml_side(t):
        s = scores[t]
        if not np.isfinite(s):
            return 0
        return 1 if s > 0 else -1

    def mom_side(t):
        m = mom[t]
        if not np.isfinite(m) or m == 0:
            return 0
        return 1 if m > 0 else -1

    meta = _meta()
    first = FIRST_PRED
    val_i = int(first + (1.0 - VAL_FRAC) * (n - first))
    ml = _window_reports(bar, meta, ml_side, first, val_i, n)
    tsm = _window_reports(bar, meta, mom_side, MOM_LB, int(MOM_LB + (1.0 - VAL_FRAC) * (n - MOM_LB)), n)
    ml_tr, tsm_tr = ml.pop("trades"), tsm.pop("trades")
    summary = {
        "profile": PROFILE, "ok": True, "candidate": False, "level1": False, "promise": False,
        "writes_9000": False, "us_shares": False, "timeframe": "H1", "hold": HOLD,
        "n_bars": n, "first": bar["ts"][0], "last": bar["ts"][-1],
        "n_refits": len(refits), "features": names,
        "books": {
            "H1_ML": {**ml, "rule": "LightGBM 回归 + sign(score)，持有 24 根 H1"},
            "H1_TSMOM": {**tsm, "rule": "sign(120 小时动量)，持有 24 根 H1"},
        },
        "n_viable": int(ml["viable_historical"]) + int(tsm["viable_historical"]),
        "note": "第一份黄金小时合同。不是日线补丁。不是 Candidate。15/30 分钟另开。",
    }
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / "ML_trades.json").write_text(json.dumps(ml_tr, ensure_ascii=False), encoding="utf-8")
    (RES / "TSMOM_trades.json").write_text(json.dumps(tsm_tr, ensure_ascii=False), encoding="utf-8")
    return summary
