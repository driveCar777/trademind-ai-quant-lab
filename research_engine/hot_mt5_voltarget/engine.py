"""V4 signal + Barroso 10% inverse-vol size, cap 1.0, no leverage."""
from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research_engine.hot_mt5_cost_aware.engine import (
    CASH,
    LONG,
    MIN_COVERAGE,
    MIN_VAL_TRADES,
    SHORT,
    _fill_cost,
    _meta,
    _summ,
)
from research_engine.hot_mt5_products.features import load_d1
from research_engine.hot_mt5_products.products import PRODUCTS, SPECIAL, VAL_FRAC
from research_engine.hot_mt5_tsmom.engine import HOLD, LOOKBACK, mom_pred
from research_engine.hot_mt5_voltarget.paths import HIST, RES

TARGET_ANN = 0.10
VOL_WIN = 20
W_CAP = 1.0
PROFILE = "HOT_MT5_VOLTARGET_V5"


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES


def vol_weights(close: np.ndarray) -> np.ndarray:
    n = len(close)
    ret = np.full(n, np.nan)
    ret[1:] = close[1:] / close[:-1] - 1.0
    w = np.zeros(n, dtype=np.float64)
    for t in range(VOL_WIN, n):
        sl = ret[t - VOL_WIN + 1: t + 1]
        if int(np.isfinite(sl).sum()) < VOL_WIN - 2:
            continue
        sig = float(np.nanstd(sl, ddof=1)) * np.sqrt(252.0)
        w[t] = min(W_CAP, TARGET_ANN / max(sig, 1e-8))
    return w


def book_sized(bar, meta, pred, weights, hold: int, start_i: int, end_i: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    dates, o = bar["dates"], bar["open"]
    n = len(dates)
    trades = []
    n_cash = 0
    t = start_i
    last = min(end_i, n - hold - 2)
    while t <= last:
        s = pred[t]
        ww = float(weights[t]) if t < len(weights) else 0.0
        if (not np.isfinite(s)) or int(s) == CASH or (not np.isfinite(ww)) or ww <= 0:
            n_cash += 1
            t += 1
            continue
        if not np.isfinite(o[t + 1]) or not np.isfinite(o[t + 1 + hold]) or o[t + 1] <= 0:
            t += 1
            continue
        side = 1 if int(s) == LONG else -1
        t_in, t_out = t + 1, t + 1 + hold
        raw = (o[t_out] / o[t_in] - 1.0) * side
        cost = _fill_cost(bar, meta, dates, t_in, t_out, side)
        net = float(ww * (raw - cost))
        trades.append({
            "signal": dates[t], "entry": dates[t_in], "exit": dates[t_out],
            "side": "LONG" if side > 0 else "SHORT", "cls": int(s),
            "weight": ww, "raw": float(raw), "cost": float(cost), "net": net,
        })
        t = t_out
    span = max(1, last - start_i + 1)
    coverage = float(len(trades) * hold) / float(span)
    try:
        d0 = dt.date.fromisoformat(dates[start_i])
        d1 = dt.date.fromisoformat(dates[min(last + hold, n - 1)])
        cal_yrs = max(1e-9, (d1 - d0).days / 365.25)
    except Exception:
        cal_yrs = None
    stats = _summ([tr["net"] for tr in trades], hold, cal_yrs)
    stats["coverage"] = coverage
    stats["n_cash"] = n_cash
    stats["mean_weight"] = float(np.mean([tr["weight"] for tr in trades])) if trades else None
    return stats, trades


def run_product(pid: str) -> Dict[str, Any]:
    print("V5 voltarget", pid, flush=True)
    ensure()
    spec = PRODUCTS[pid]
    path = HIST / ("%s_D1.csv" % pid)
    if not path.is_file():
        return {"id": pid, "ok": False, "error": "NO_D1"}
    bar = load_d1(path)
    pred = mom_pred(bar["close"])
    weights = vol_weights(bar["close"])
    meta = _meta(pid)
    n = len(bar["dates"])
    first = LOOKBACK
    val_i = int(first + (1.0 - VAL_FRAC) * (n - first))
    long_s, long_tr = book_sized(bar, meta, pred, weights, HOLD, first, n)
    res_s, _ = book_sized(bar, meta, pred, weights, HOLD, first, val_i - 1)
    val_s, _ = book_sized(bar, meta, pred, weights, HOLD, val_i, n)
    years = {}
    for tr in long_tr:
        years.setdefault(tr["signal"][:4], []).append(tr["net"])
    year_tab = {k: _summ(v, HOLD) for k, v in sorted(years.items())}
    from research_engine.hot_mt5_cost_aware.engine import _slice_summ
    special = {}
    for tag, a, b in SPECIAL:
        special[tag] = _slice_summ(long_tr, HOLD, a, min(b, bar["dates"][-1]))
    cover_fail = bool((val_s.get("n_periods") or 0) < MIN_VAL_TRADES or (val_s.get("coverage") or 0) < MIN_COVERAGE)
    viable = bool(not cover_fail and (val_s.get("twr") or 0) > 0 and (val_s.get("t") or 0) > 1.0)
    if cover_fail:
        verdict, deny = "NO_CANDIDATE", "VALIDATION_COVERAGE"
    elif viable:
        verdict, deny = "VIABLE_HISTORICAL", None
    else:
        verdict, deny = "NO_CANDIDATE", "VALIDATION_GATE"
    report = {
        "id": pid, "label": spec["label"], "ok": True, "candidate": False, "level1": False, "promise": False,
        "writes_9000": False, "us_shares": False, "profile": PROFILE,
        "lookback": LOOKBACK, "hold": HOLD, "target_ann": TARGET_ANN, "vol_win": VOL_WIN, "w_cap": W_CAP,
        "no_ml": True, "no_leverage": True, "not_sma200": True, "not_v4_patch": True,
        "shell": "TSMOM12_VOLTARGET", "n_bars": n, "first": bar["dates"][0], "last": bar["dates"][-1],
        "long_sample": long_s, "research_70": res_s, "validation_30": val_s,
        "year_by_year": year_tab, "special_diagnostic": special,
        "viable_historical": viable, "coverage_fail": cover_fail, "deny": deny, "verdict": verdict,
        "strategy": {
            "deploy": bool(viable),
            "rule": "12月动量符号 + 10%年化波动倒数仓位，封顶 1.0。不改 252/20。",
            "do_not": "不要改目标波动/封顶；不要只留黄金；不要写 Grok。",
        },
        "n_trades_long": len(long_tr),
        "note": "外壳清点最后一刀。不是 Candidate。",
    }
    (RES / ("%s.json" % pid)).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / ("%s_trades.json" % pid)).write_text(json.dumps(long_tr, ensure_ascii=False), encoding="utf-8")
    return report


def run_all(ids: Optional[List[str]] = None) -> Dict[str, Any]:
    ensure()
    ids = ids or list(PRODUCTS)
    items = [run_product(pid) for pid in ids]
    summary = {
        "profile": PROFILE, "candidate": False, "writes_9000": False, "us_shares": False,
        "target_ann": TARGET_ANN, "no_leverage": True,
        "n_ok": sum(1 for r in items if r.get("ok")),
        "n_viable": sum(1 for r in items if r.get("viable_historical")),
        "items": items,
        "note": "Inverse-vol TSMOM. Not a V4 patch. Not Candidate.",
    }
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
