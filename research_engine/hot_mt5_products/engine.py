"""Walk-forward one product. Long-sample book is the main report. Special windows are diagnostic."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research_engine.hot_mt5_products.features import build_matrix, load_d1
from research_engine.hot_mt5_products.paths import HIST, RES, ensure
from research_engine.hot_mt5_products.products import (
    EMBARGO_EXTRA,
    FIRST_PRED_BARS,
    LGBM_PARAMS,
    MIN_HIST,
    PRODUCTS,
    REFIT_EVERY,
    SLIP,
    SPECIAL,
    VAL_FRAC,
)


def _meta(pid: str) -> Dict[str, Any]:
    p = HIST / ("%s_META.json" % pid)
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"point": 0.01, "swap_mode": 1, "swap_long": 0.0, "swap_short": 0.0,
            "swap_rollover3days": 3, "spread_points_now": 20, "bid": 1.0}


def _swap_frac(meta: Dict[str, Any], side: int, dates: List[str], t_in: int, t_out: int, px: float) -> float:
    nights = 0.0
    roll = int(meta.get("swap_rollover3days") or 3)
    for u in range(t_in, t_out):
        d = dt.date.fromisoformat(dates[u])
        nights += 3.0 if d.isoweekday() == roll else 1.0
    sw = float(meta["swap_long"] if side > 0 else meta["swap_short"])
    mode = int(meta.get("swap_mode") or 1)
    if mode == 1:
        return sw * float(meta.get("point") or 0.01) / max(1e-12, px) * nights
    if mode == 5:
        return sw / 100.0 * nights / 365.0
    return 0.0


def _spread_pct(bar: Dict[str, np.ndarray], meta: Dict[str, Any], t: int) -> float:
    px = float(bar["close"][t])
    pt = float(meta.get("point") or 0.01)
    raw = float(bar["spread"][t]) * pt / max(1e-12, px)
    now = float(meta.get("spread_points_now") or 0) * pt / max(1e-12, float(meta.get("bid") or px))
    if not np.isfinite(raw) or raw <= 0:
        return max(0.0, now)
    return max(raw, now * 0.25)


def _cost(bar, meta, dates, t_in, t_out, side) -> float:
    sp = _spread_pct(bar, meta, t_in)
    return sp + 2 * SLIP - _swap_frac(meta, side, dates, t_in, t_out, float(bar["open"][t_in]))


def walk_scores(x: np.ndarray, y: np.ndarray, hold: int, names: Optional[List[str]] = None) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    import warnings
    import lightgbm as lgb
    warnings.filterwarnings("ignore", message="X does not have valid feature names")
    t_n = x.shape[0]
    cols = names or ["f%d" % i for i in range(x.shape[1])]
    scores = np.full(t_n, np.nan)
    embargo = hold + EMBARGO_EXTRA
    t = FIRST_PRED_BARS
    refits = []
    while t < t_n:
        cutoff = t - embargo
        if cutoff < MIN_HIST:
            t += 1
            continue
        ok = np.all(np.isfinite(x[:cutoff]), axis=1) & np.isfinite(y[:cutoff])
        if int(ok.sum()) < 80:
            t += 1
            continue
        model = lgb.LGBMRegressor(**LGBM_PARAMS)
        model.fit(x[:cutoff][ok], np.clip(y[:cutoff][ok], -5, 5), feature_name=cols)
        end = min(t_n, t + REFIT_EVERY)
        for u in range(t, end):
            if np.all(np.isfinite(x[u])):
                scores[u] = float(model.predict(x[u].reshape(1, -1))[0])
        refits.append({"fit_at_i": t, "rows": int(ok.sum()), "through_i": end - 1})
        t = end
    return scores, refits


def _summ(rets: List[float], hold: int) -> Dict[str, Any]:
    x = np.array(rets, dtype=np.float64)
    if len(x) == 0:
        return {"n_periods": 0, "twr": None, "cagr": None, "mean": None, "t": None, "hit": None, "maxdd": None}
    eq = np.cumprod(1.0 + x)
    yrs = max(1e-9, len(x) * hold / 252.0)
    peak = np.maximum.accumulate(eq)
    dd = float(np.min(eq / peak - 1.0))
    t = float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else None
    return {
        "n_periods": int(len(x)),
        "twr": float(eq[-1] - 1.0),
        "cagr": float(eq[-1] ** (1.0 / yrs) - 1.0),
        "mean": float(x.mean()),
        "t": t,
        "hit": float((x > 0).mean()),
        "maxdd": dd,
    }


def book(bar, meta, scores, hold: int, start_i: int, end_i: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    dates, o = bar["dates"], bar["open"]
    n = len(dates)
    trades = []
    t = start_i
    while t + hold + 1 < n and t <= end_i:
        s = scores[t]
        if not np.isfinite(s) or not np.isfinite(o[t + 1]) or not np.isfinite(o[t + 1 + hold]) or o[t + 1] <= 0:
            t += 1
            continue
        side = 1 if s > 0 else -1
        t_in, t_out = t + 1, t + 1 + hold
        raw = (o[t_out] / o[t_in] - 1.0) * side
        cost = _cost(bar, meta, dates, t_in, t_out, side)
        net = float(raw - cost)
        trades.append({
            "signal": dates[t], "entry": dates[t_in], "exit": dates[t_out],
            "side": "LONG" if side > 0 else "SHORT", "score": float(s),
            "raw": float(raw), "cost": float(cost), "net": net,
        })
        t = t_out
    return _summ([tr["net"] for tr in trades], hold), trades


def _slice_summ(trades: List[Dict[str, Any]], hold: int, a: str, b: str) -> Dict[str, Any]:
    xs = [tr["net"] for tr in trades if a <= tr["signal"] <= b]
    out = _summ(xs, hold)
    out["from"] = a
    out["to"] = b
    return out


def run_product(pid: str) -> Dict[str, Any]:
    ensure()
    spec = PRODUCTS[pid]
    path = HIST / ("%s_D1.csv" % pid)
    if not path.is_file():
        return {"id": pid, "ok": False, "error": "NO_D1"}
    bar = load_d1(path)
    names, x = build_matrix(pid, bar)
    hold = int(spec["hold"])
    o = bar["open"]
    y = np.full(len(o), np.nan)
    y[: -(hold + 1)] = o[hold + 1:] / o[1:-hold] - 1.0
    scores, refits = walk_scores(x, y, hold, names)
    meta = _meta(pid)
    n = len(bar["dates"])
    first = FIRST_PRED_BARS
    val_i = int(first + (1.0 - VAL_FRAC) * (n - first))
    long_s, long_tr = book(bar, meta, scores, hold, first, n)
    res_s, res_tr = book(bar, meta, scores, hold, first, val_i - 1)
    val_s, val_tr = book(bar, meta, scores, hold, val_i, n)
    years = {}
    for tr in long_tr:
        years.setdefault(tr["signal"][:4], []).append(tr["net"])
    year_tab = {k: _summ(v, hold) for k, v in sorted(years.items())}
    special = {}
    for tag, a, b in SPECIAL:
        special[tag] = _slice_summ(long_tr, hold, a, min(b, bar["dates"][-1]))
    viable = bool(val_s.get("n_periods", 0) >= 8 and (val_s.get("twr") or 0) > 0 and (val_s.get("t") or 0) > 1.0)
    report = {
        "id": pid, "label": spec["label"], "ok": True, "candidate": False, "level1": False, "promise": False,
        "writes_9000": False, "us_shares": False,
        "broker_meta": {k: meta.get(k) for k in ("broker", "swap_mode", "swap_long", "swap_short", "point")},
        "shell": spec["shell"], "why": spec["why"], "hold": hold, "features": names,
        "lgbm": LGBM_PARAMS, "n_bars": n, "first": bar["dates"][0], "last": bar["dates"][-1],
        "n_refits": len(refits),
        "long_sample": long_s,  # first_pred → last bar; this is the main backtest
        "research_70": res_s,
        "validation_30": val_s,
        "year_by_year": year_tab,
        "special_diagnostic": special,
        "viable_historical": viable,
        "verdict": "VIABLE_HISTORICAL" if viable else "NO_CANDIDATE",
        "strategy": {
            "deploy": bool(viable),
            "rule": "收盘打分，下一根开盘按分数符号开仓，持有 %d 根 D1 后平。手数 0.01。只 demo。" % hold,
            "do_not": "不要用验证窗或特殊时段改特征/持有期；不要和 A 股对冲；不要把 TWR 写成承诺。",
        },
        "n_trades_long": len(long_tr),
        "note": "特殊时段只诊断。全样本是主报告。不是 Candidate。",
    }
    (RES / ("%s.json" % pid)).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / ("%s_trades.json" % pid)).write_text(json.dumps(long_tr, ensure_ascii=False), encoding="utf-8")
    return report


def run_all(ids: Optional[List[str]] = None) -> Dict[str, Any]:
    ensure()
    ids = ids or list(PRODUCTS)
    items = [run_product(pid) for pid in ids]
    summary = {
        "profile": "HOT_MT5_PER_PRODUCT_V1",
        "candidate": False,
        "writes_9000": False,
        "us_shares": False,
        "n_ok": sum(1 for r in items if r.get("ok")),
        "n_viable": sum(1 for r in items if r.get("viable_historical")),
        "items": items,
        "note": "各品种单独模型+外壳。全样本回测是主数字。验证 30% 只作报告。不是 Candidate。",
    }
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
