"""Walk-forward 3-class model. Cash is first-class. Hurdle = 2 x META expected cost."""
from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research_engine.hot_mt5_cost_aware.paths import HIST, RES


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES
from research_engine.hot_mt5_products.features import build_matrix, load_d1
from research_engine.hot_mt5_products.products import (
    EMBARGO_EXTRA,
    FIRST_PRED_BARS,
    MIN_HIST,
    PRODUCTS,
    REFIT_EVERY,
    SLIP,
    SPECIAL,
    VAL_FRAC,
)

LAMBDA = 2.0
MIN_COVERAGE = 0.15
MIN_VAL_TRADES = 8
CASH, LONG, SHORT = 0, 1, 2

LGBM_CLF = {
    "objective": "multiclass",
    "num_leaves": 15,
    "learning_rate": 0.03,
    "n_estimators": 200,
    "min_child_samples": 40,
    "colsample_bytree": 0.8,
    "subsample": 0.8,
    "subsample_freq": 1,
    "reg_lambda": 1.0,
    "num_threads": 4,
    "random_state": 25,
    "verbosity": -1,
}


def _meta(pid: str) -> Dict[str, Any]:
    p = HIST / ("%s_META.json" % pid)
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"point": 0.01, "swap_mode": 1, "swap_long": 0.0, "swap_short": 0.0,
            "swap_rollover3days": 3, "spread_points_now": 20, "bid": 1.0}


def expected_cost(meta: Dict[str, Any], side: int, hold: int, px: float) -> float:
    """A priori round-trip cost from META only. Not the 20bp forensics cut."""
    nights = float(hold) + 2.0 * (float(hold) / 5.0)
    pt = float(meta.get("point") or 0.01)
    bid = max(1e-12, float(meta.get("bid") or px or 1.0))
    spread = float(meta.get("spread_points_now") or 0) * pt / bid
    sw = float(meta["swap_long"] if side > 0 else meta["swap_short"])
    mode = int(meta.get("swap_mode") or 1)
    if mode == 1:
        swap_frac = sw * pt / max(1e-12, px if px else bid) * nights
    elif mode == 5:
        swap_frac = sw / 100.0 * nights / 365.0
    else:
        swap_frac = 0.0
    return max(0.0, spread + 2.0 * SLIP - swap_frac)


def hurdle_pair(meta: Dict[str, Any], hold: int, px: float) -> Tuple[float, float]:
    return LAMBDA * expected_cost(meta, 1, hold, px), LAMBDA * expected_cost(meta, -1, hold, px)


def make_labels(y_raw: np.ndarray, px: np.ndarray, meta: Dict[str, Any], hold: int) -> np.ndarray:
    lab = np.full(len(y_raw), np.nan)
    for i, y in enumerate(y_raw):
        if not np.isfinite(y) or not np.isfinite(px[i]) or px[i] <= 0:
            continue
        h_long, h_short = hurdle_pair(meta, hold, float(px[i]))
        if y > h_long:
            lab[i] = LONG
        elif y < -h_short:
            lab[i] = SHORT
        else:
            lab[i] = CASH
    return lab


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


def _fill_cost(bar, meta, dates, t_in, t_out, side) -> float:
    sp = _spread_pct(bar, meta, t_in)
    return sp + 2 * SLIP - _swap_frac(meta, side, dates, t_in, t_out, float(bar["open"][t_in]))


def walk_classes(x: np.ndarray, y: np.ndarray, hold: int, names: Optional[List[str]] = None) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    import warnings
    import lightgbm as lgb
    warnings.filterwarnings("ignore", message="X does not have valid feature names")
    t_n = x.shape[0]
    cols = names or ["f%d" % i for i in range(x.shape[1])]
    pred = np.full(t_n, np.nan)
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
        yy = y[:cutoff][ok].astype(int)
        classes = sorted(set(int(v) for v in yy))
        if len(classes) < 2:
            t += 1
            continue
        remap = {c: i for i, c in enumerate(classes)}
        inv = {i: c for c, i in remap.items()}
        y_fit = np.array([remap[int(v)] for v in yy], dtype=np.int32)
        params = dict(LGBM_CLF)
        if len(classes) == 2:
            params.pop("objective", None)
        else:
            params["num_class"] = len(classes)
        model = lgb.LGBMClassifier(**params)
        model.fit(x[:cutoff][ok], y_fit, feature_name=cols)
        end = min(t_n, t + REFIT_EVERY)
        for u in range(t, end):
            if np.all(np.isfinite(x[u])):
                pred[u] = float(inv[int(model.predict(x[u].reshape(1, -1))[0])])
        refits.append({"fit_at_i": t, "rows": int(ok.sum()), "classes": classes,
                       "through_i": end - 1})
        t = end
    return pred, refits


def _summ(rets: List[float], hold: int, calendar_years: Optional[float] = None) -> Dict[str, Any]:
    x = np.array(rets, dtype=np.float64)
    empty = {"n_periods": 0, "twr": None, "cagr": None, "mean": None, "t": None,
             "hit": None, "maxdd": None, "payoff": None, "profit_factor": None}
    if len(x) == 0:
        return empty
    eq = np.cumprod(1.0 + x)
    if calendar_years and calendar_years > 0:
        yrs = calendar_years
    else:
        yrs = max(1e-9, len(x) * hold / 252.0)
    peak = np.maximum.accumulate(eq)
    dd = float(np.min(eq / peak - 1.0))
    t = float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else None
    wins, loss = x[x > 0], x[x <= 0]
    payoff = float(wins.mean() / (-loss.mean())) if len(wins) and len(loss) and loss.mean() < 0 else None
    pf = float(wins.sum() / (-loss.sum())) if len(loss) and loss.sum() < 0 else None
    return {
        "n_periods": int(len(x)),
        "twr": float(eq[-1] - 1.0),
        "cagr": float(eq[-1] ** (1.0 / max(1e-9, yrs)) - 1.0),
        "mean": float(x.mean()),
        "t": t,
        "hit": float((x > 0).mean()),
        "maxdd": dd,
        "payoff": payoff,
        "profit_factor": pf,
    }


def book(bar, meta, pred, hold: int, start_i: int, end_i: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
    dates, o = bar["dates"], bar["open"]
    n = len(dates)
    trades = []
    n_cash = 0
    t = start_i
    last = min(end_i, n - hold - 2)
    while t <= last:
        s = pred[t]
        if (not np.isfinite(s)) or int(s) == CASH:
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
        net = float(raw - cost)
        trades.append({
            "signal": dates[t], "entry": dates[t_in], "exit": dates[t_out],
            "side": "LONG" if side > 0 else "SHORT", "cls": int(s),
            "raw": float(raw), "cost": float(cost), "net": net,
        })
        t = t_out
    span = max(1, last - start_i + 1)
    in_mkt = len(trades) * hold
    coverage = float(in_mkt) / float(span)
    try:
        d0 = dt.date.fromisoformat(dates[start_i])
        d1 = dt.date.fromisoformat(dates[min(last + hold, n - 1)])
        cal_yrs = max(1e-9, (d1 - d0).days / 365.25)
    except Exception:
        cal_yrs = None
    stats = _summ([tr["net"] for tr in trades], hold, cal_yrs)
    stats["coverage"] = coverage
    stats["n_cash"] = n_cash
    stats["n_decisions"] = n_cash + len(trades)
    extra = {"coverage": coverage, "n_cash": n_cash, "span_bars": span}
    return stats, trades, extra


def _slice_summ(trades: List[Dict[str, Any]], hold: int, a: str, b: str) -> Dict[str, Any]:
    xs = [tr["net"] for tr in trades if a <= tr["signal"] <= b]
    out = _summ(xs, hold)
    out["from"] = a
    out["to"] = b
    return out


def run_product(pid: str) -> Dict[str, Any]:
    print("V2 train", pid, flush=True)
    ensure()
    spec = PRODUCTS[pid]
    path = HIST / ("%s_D1.csv" % pid)
    if not path.is_file():
        return {"id": pid, "ok": False, "error": "NO_D1"}
    bar = load_d1(path)
    names, x = build_matrix(pid, bar)
    hold = int(spec["hold"])
    o = bar["open"]
    y_raw = np.full(len(o), np.nan)
    y_raw[: -(hold + 1)] = o[hold + 1:] / o[1:-hold] - 1.0
    meta = _meta(pid)
    px = np.array(bar["close"], dtype=np.float64)
    y = make_labels(y_raw, px, meta, hold)
    pred, refits = walk_classes(x, y, hold, names)
    n = len(bar["dates"])
    first = FIRST_PRED_BARS
    val_i = int(first + (1.0 - VAL_FRAC) * (n - first))
    long_s, long_tr, _ = book(bar, meta, pred, hold, first, n)
    res_s, _, _ = book(bar, meta, pred, hold, first, val_i - 1)
    val_s, val_tr, _ = book(bar, meta, pred, hold, val_i, n)
    years = {}
    for tr in long_tr:
        years.setdefault(tr["signal"][:4], []).append(tr["net"])
    year_tab = {k: _summ(v, hold) for k, v in sorted(years.items())}
    special = {}
    for tag, a, b in SPECIAL:
        special[tag] = _slice_summ(long_tr, hold, a, min(b, bar["dates"][-1]))
    h_l, h_s = hurdle_pair(meta, hold, float(meta.get("bid") or px[-1]))
    n_lab = int(np.isfinite(y).sum())
    lab_share = {
        "cash": float(np.nansum(y == CASH) / max(1, n_lab)),
        "long": float(np.nansum(y == LONG) / max(1, n_lab)),
        "short": float(np.nansum(y == SHORT) / max(1, n_lab)),
    }
    cover_fail = bool((val_s.get("n_periods") or 0) < MIN_VAL_TRADES or (val_s.get("coverage") or 0) < MIN_COVERAGE)
    viable = bool(
        not cover_fail
        and (val_s.get("twr") or 0) > 0
        and (val_s.get("t") or 0) > 1.0
    )
    if cover_fail:
        verdict = "NO_CANDIDATE"
        deny = "VALIDATION_COVERAGE"
    elif viable:
        verdict = "VIABLE_HISTORICAL"
        deny = None
    else:
        verdict = "NO_CANDIDATE"
        deny = "VALIDATION_GATE"
    report = {
        "id": pid, "label": spec["label"], "ok": True, "candidate": False, "level1": False, "promise": False,
        "writes_9000": False, "us_shares": False, "profile": "HOT_MT5_COST_AWARE_V2",
        "hurdle_lambda": LAMBDA, "hurdle_not_20bp": True,
        "hurdle_long": h_l, "hurdle_short": h_s,
        "label_share": lab_share,
        "broker_meta": {k: meta.get(k) for k in ("broker", "swap_mode", "swap_long", "swap_short", "point", "bid")},
        "shell": "COST_AWARE_3WAY", "hold": hold, "features": names,
        "lgbm": LGBM_CLF, "n_bars": n, "first": bar["dates"][0], "last": bar["dates"][-1],
        "n_refits": len(refits),
        "long_sample": long_s,
        "research_70": res_s,
        "validation_30": val_s,
        "year_by_year": year_tab,
        "special_diagnostic": special,
        "viable_historical": viable,
        "coverage_fail": cover_fail,
        "deny": deny,
        "verdict": verdict,
        "strategy": {
            "deploy": bool(viable),
            "rule": "三分类 argmax。CASH 空仓次日再看；多空下一开盘进、持有 %d 根。门槛=2×META成本，不是 20bp。" % hold,
            "do_not": "不要改 λ/特征/hold；不要和 A 股对冲；不要把 TWR 写成承诺。",
        },
        "n_trades_long": len(long_tr),
        "note": "空仓是一等公民。覆盖率过低直接否。不是 Candidate。",
    }
    (RES / ("%s.json" % pid)).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / ("%s_trades.json" % pid)).write_text(json.dumps(long_tr, ensure_ascii=False), encoding="utf-8")
    return report


def run_all(ids: Optional[List[str]] = None) -> Dict[str, Any]:
    ensure()
    ids = ids or list(PRODUCTS)
    items = [run_product(pid) for pid in ids]
    summary = {
        "profile": "HOT_MT5_COST_AWARE_V2",
        "candidate": False,
        "writes_9000": False,
        "us_shares": False,
        "hurdle_lambda": LAMBDA,
        "hurdle_not_20bp": True,
        "n_ok": sum(1 for r in items if r.get("ok")),
        "n_viable": sum(1 for r in items if r.get("viable_historical")),
        "items": items,
        "note": "三分类 + 2×META 成本门槛。验证覆盖<15%或成交<8直接否。不是 Candidate。",
    }
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
