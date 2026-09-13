"""Which ±1.0 ATR barrier is touched first in the next 24 H1 bars."""
from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research_engine.hot_mt5_cost_aware.engine import LGBM_CLF
from research_engine.hot_mt5_gold_h1.data import load_h1
from research_engine.hot_mt5_gold_h1.engine import _fill_cost, _summ
from research_engine.hot_mt5_gold_h1_v5.engine import NATIVE, build_native
from research_engine.hot_mt5_gold_h1_v8.paths import HIST, RES
from research_engine.hot_mt5_products.features import _atr
from research_engine.hot_mt5_products.products import VAL_FRAC

PROFILE = "HOT_MT5_GOLD_H1_V8_TRIPLE_BARRIER"
K = 1.0
HORIZON = 24
FIRST_PRED = 2000
REFIT_EVERY = 1000
EMBARGO = 25
MIN_HIST = 1500
MIN_TRAIN = 80
MIN_COVERAGE = 0.15
MIN_VAL_TRADES = 8
CASH, LONG, SHORT = 0, 1, 2
COVERAGE_DEF = "sum(t_out - t_in) / window_bars"
REGIMES = (
    ("COVID_2020", "2020-02-01", "2020-06-30"),
    ("HIKING_2022", "2022-01-01", "2022-12-31"),
    ("CHOP_2023", "2023-01-01", "2023-12-31"),
    ("GOLD_BULL_2024_26", "2024-05-01", None),
)
STUCK_STD = 1e-12


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES


def _meta() -> Dict[str, Any]:
    p = HIST / "GOLD_META.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"point": 0.01, "swap_mode": 1, "swap_long": -1.54, "swap_short": 0.64,
            "swap_rollover3days": 5, "spread_points_now": 34, "bid": 4300.0}


def atr_price(bar: Dict[str, np.ndarray]) -> np.ndarray:
    return _atr(bar["high"], bar["low"], bar["close"], 14)


def signed_from_y(y: np.ndarray) -> np.ndarray:
    s = np.full(len(y), np.nan)
    ok = np.isfinite(y)
    s[ok] = 0.0
    s[y == LONG] = 1.0
    s[y == SHORT] = -1.0
    return s


def _pearson(a: np.ndarray, b: np.ndarray) -> Optional[float]:
    m = np.isfinite(a) & np.isfinite(b)
    if int(m.sum()) < 10:
        return None
    aa, bb = a[m], b[m]
    if float(aa.std()) < STUCK_STD or float(bb.std()) < STUCK_STD:
        return 0.0
    return float(np.corrcoef(aa, bb)[0, 1])


def _acc(y: np.ndarray, p: np.ndarray) -> Optional[float]:
    m = np.isfinite(y) & np.isfinite(p)
    if int(m.sum()) < 1:
        return None
    return float(np.mean(y[m] == p[m]))


def label_mix(y: np.ndarray) -> Dict[str, Any]:
    m = np.isfinite(y)
    n = int(m.sum())
    if n == 0:
        return {"n": 0, "cash": 0, "long": 0, "short": 0, "cash_rate": None}
    yy = y[m]
    n_c = int((yy == CASH).sum())
    n_l = int((yy == LONG).sum())
    n_s = int((yy == SHORT).sum())
    return {"n": n, "cash": n_c, "long": n_l, "short": n_s, "cash_rate": n_c / float(n)}


def label_triple_barrier(
    bar: Dict[str, np.ndarray],
    atr: Optional[np.ndarray] = None,
    k: float = K,
    horizon: int = HORIZON,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Scan t+1..t+24. Same-bar both hits → CASH. Need t+25 open to be tradeable."""
    c, h, l = bar["close"], bar["high"], bar["low"]
    if atr is None:
        atr = atr_price(bar)
    n = len(c)
    y = np.full(n, np.nan)
    touch = np.full(n, -1, dtype=np.int32)
    last = n - horizon - 2
    for t in range(max(0, last + 1)):
        a = float(atr[t])
        px = float(c[t])
        if not np.isfinite(a) or a <= 0 or not np.isfinite(px):
            continue
        up = px + k * a
        dn = px - k * a
        lab = CASH
        hit = -1
        for u in range(t + 1, t + horizon + 1):
            up_hit = float(h[u]) >= up
            dn_hit = float(l[u]) <= dn
            if up_hit and dn_hit:
                lab = CASH
                hit = u
                break
            if up_hit:
                lab = LONG
                hit = u
                break
            if dn_hit:
                lab = SHORT
                hit = u
                break
        y[t] = lab
        touch[t] = hit
    return y, signed_from_y(y), touch


def _first_touch(bar, t: int, atr_t: float, k: float, horizon: int) -> Optional[int]:
    c = float(bar["close"][t])
    up = c + k * atr_t
    dn = c - k * atr_t
    n = len(bar["high"])
    end = min(t + horizon, n - 1)
    for u in range(t + 1, end + 1):
        if float(bar["high"][u]) >= up or float(bar["low"][u]) <= dn:
            return u
    return None


def _p_long_minus_short(proba: np.ndarray, inv: Dict[int, int]) -> np.ndarray:
    n = proba.shape[0]
    pl = np.zeros(n)
    ps = np.zeros(n)
    for col, cls in inv.items():
        if cls == LONG:
            pl = proba[:, col]
        elif cls == SHORT:
            ps = proba[:, col]
    return pl - ps


def _fit_pack(y: np.ndarray, pred: np.ndarray, pdiff: np.ndarray, signed: np.ndarray) -> Dict[str, Any]:
    mix = label_mix(y)
    return {
        "n": mix["n"],
        "acc": _acc(y, pred),
        "ic": _pearson(pdiff, signed),
        "cash_rate": mix["cash_rate"],
        "pred_cash_rate": None if len(pred) == 0 or not np.isfinite(pred).any()
        else float(np.mean(pred[np.isfinite(pred)] == CASH)),
    }


def _fit_clf(x: np.ndarray, y: np.ndarray, names: List[str]):
    import warnings
    import lightgbm as lgb
    warnings.filterwarnings("ignore", message="X does not have valid feature names")
    yy = y.astype(int)
    classes = sorted(set(int(v) for v in yy))
    if len(classes) < 2:
        return None
    remap = {c: i for i, c in enumerate(classes)}
    inv = {i: c for c, i in remap.items()}
    y_fit = np.array([remap[int(v)] for v in yy], dtype=np.int32)
    params = dict(LGBM_CLF)
    if len(classes) == 2:
        params.pop("objective", None)
    else:
        params["num_class"] = len(classes)
    model = lgb.LGBMClassifier(**params)
    model.fit(x, y_fit, feature_name=names)
    return model, inv


def true_in_sample(x: np.ndarray, y: np.ndarray, signed: np.ndarray, names: List[str], mask: np.ndarray) -> Dict[str, Any]:
    if int(mask.sum()) < MIN_TRAIN:
        return {"ok": False, "error": "TOO_FEW_ROWS"}
    fitted = _fit_clf(x[mask], y[mask], names)
    if fitted is None:
        return {"ok": False, "error": "ONE_CLASS"}
    model, inv = fitted
    raw = model.predict(x[mask])
    pred = np.array([inv[int(v)] for v in raw], dtype=np.float64)
    proba = model.predict_proba(x[mask])
    pdiff = _p_long_minus_short(proba, inv)
    out = _fit_pack(y[mask], pred, pdiff, signed[mask])
    out["ok"] = True
    out["n_train"] = int(mask.sum())
    return out


def walk_classes(
    x: np.ndarray, y: np.ndarray, signed: np.ndarray, names: List[str],
) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]]]:
    t_n = x.shape[0]
    pred = np.full(t_n, np.nan)
    pdiff_all = np.full(t_n, np.nan)
    folds: List[Dict[str, Any]] = []
    t = FIRST_PRED
    fold = 0
    while t < t_n:
        cutoff = t - EMBARGO
        if cutoff < MIN_HIST:
            t += 1
            continue
        ok = np.all(np.isfinite(x[:cutoff]), axis=1) & np.isfinite(y[:cutoff])
        n_tr = int(ok.sum())
        if n_tr < MIN_TRAIN:
            t += 1
            continue
        fitted = _fit_clf(x[:cutoff][ok], y[:cutoff][ok], names)
        if fitted is None:
            t += 1
            continue
        model, inv = fitted
        end = min(t_n, t + REFIT_EVERY)
        tr_raw = model.predict(x[:cutoff][ok])
        tr_pred = np.array([inv[int(v)] for v in tr_raw], dtype=np.float64)
        tr_pdiff = _p_long_minus_short(model.predict_proba(x[:cutoff][ok]), inv)
        tr = _fit_pack(y[:cutoff][ok], tr_pred, tr_pdiff, signed[:cutoff][ok])
        sl = slice(t, end)
        finite = np.all(np.isfinite(x[sl]), axis=1)
        if finite.any():
            te_x = x[sl][finite]
            te_raw = model.predict(te_x)
            te_hat = np.array([inv[int(v)] for v in te_raw], dtype=np.float64)
            te_pd = _p_long_minus_short(model.predict_proba(te_x), inv)
            idx = np.arange(t, end)[finite]
            pred[idx] = te_hat
            pdiff_all[idx] = te_pd
            te = _fit_pack(y[idx], pred[idx], pdiff_all[idx], signed[idx])
        else:
            te = _fit_pack(np.array([]), np.array([]), np.array([]), np.array([]))
        folds.append({
            "fold": fold, "fit_at_i": t, "through_i": end - 1,
            "n_train": n_tr, "n_test": int(finite.sum()),
            "train_acc": tr["acc"], "test_acc": te["acc"],
            "train_ic": tr["ic"], "test_ic": te["ic"],
            "train_cash_rate": tr["cash_rate"], "test_cash_rate": te["cash_rate"],
            "train_pred_cash_rate": tr["pred_cash_rate"],
            "test_pred_cash_rate": te["pred_cash_rate"],
        })
        fold += 1
        t = end
    return pred, pdiff_all, folds


def _cal_years(ts: List[str], a: int, b: int) -> Optional[float]:
    try:
        d0 = dt.date.fromisoformat(ts[a][:10])
        d1 = dt.date.fromisoformat(ts[b][:10])
        return max(1e-9, (d1 - d0).days / 365.25)
    except Exception:
        return None


def resolve_exit(bar, t: int, atr_t: float, k: float = K, horizon: int = HORIZON) -> Optional[Tuple[int, str]]:
    n = len(bar["open"])
    t_in = t + 1
    t_time = t + 1 + horizon
    if t_time >= n:
        return None
    hit = _first_touch(bar, t, atr_t, k, horizon)
    if hit is None:
        return t_time, "TIME"
    t_out = hit + 1
    if t_out >= n:
        return None
    return t_out, "BARRIER"


def book(
    bar, meta, pred, atr, start_i: int, end_i: int,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    ts, o = bar["ts"], bar["open"]
    n = len(ts)
    trades: List[Dict[str, Any]] = []
    t = start_i
    last = min(end_i, n - HORIZON - 2)
    while t <= last:
        s = pred[t]
        if (not np.isfinite(s)) or int(s) == CASH:
            t += 1
            continue
        a = float(atr[t])
        if not np.isfinite(a) or a <= 0:
            t += 1
            continue
        resolved = resolve_exit(bar, t, a)
        if resolved is None:
            t += 1
            continue
        t_out, reason = resolved
        t_in = t + 1
        if o[t_in] <= 0 or not np.isfinite(o[t_in]) or not np.isfinite(o[t_out]):
            t += 1
            continue
        side = 1 if int(s) == LONG else -1
        raw = (o[t_out] / o[t_in] - 1.0) * side
        cost = _fill_cost(bar, meta, t_in, t_out, side)
        trades.append({
            "signal": ts[t], "entry": ts[t_in], "exit": ts[t_out],
            "side": "LONG" if side > 0 else "SHORT",
            "raw": float(raw), "cost": float(cost), "net": float(raw - cost),
            "hours": int(t_out - t_in),
            "exit_reason": reason,
        })
        t = t_out
    span = max(1, last - start_i + 1)
    hours = float(sum(tr["hours"] for tr in trades))
    cal = _cal_years(ts, start_i, min(last + HORIZON, n - 1))
    stats = _summ([tr["net"] for tr in trades], HORIZON, cal)
    stats["coverage"] = hours / float(span)
    stats["hours_held"] = hours
    stats["avg_hours"] = None if not trades else hours / float(len(trades))
    stats["coverage_def"] = COVERAGE_DEF
    return stats, trades


def _gate(val_s: Dict[str, Any]) -> Tuple[str, Optional[str], bool]:
    cover_fail = bool((val_s.get("n_periods") or 0) < MIN_VAL_TRADES or (val_s.get("coverage") or 0) < MIN_COVERAGE)
    viable = bool(not cover_fail and (val_s.get("twr") or 0) > 0 and (val_s.get("t") or 0) > 1.0)
    if cover_fail:
        return "NO_CANDIDATE", "VALIDATION_COVERAGE", False
    if viable:
        return "VIABLE_HISTORICAL", None, True
    return "NO_CANDIDATE", "VALIDATION_GATE", False


def _in_range(ts: str, start: str, end: str) -> bool:
    d = ts[:10]
    return start <= d <= end


def _buy_hold(bar, start: str, end: str) -> Optional[float]:
    c = bar["close"]
    idx = [i for i, t in enumerate(bar["ts"]) if _in_range(t, start, end)]
    if len(idx) < 2:
        return None
    a, b = float(c[idx[0]]), float(c[idx[-1]])
    if a <= 0:
        return None
    return b / a - 1.0


def _regime_rows(bar, trades, start: str, end: str) -> Dict[str, Any]:
    xs = [tr for tr in trades if _in_range(tr["signal"], start, end)]
    stats = _summ([tr["net"] for tr in xs], HORIZON)
    bh = _buy_hold(bar, start, end)
    twr = stats.get("twr")
    return {
        "start": start, "end": end, "n_trades": len(xs),
        "twr": twr, "hit": stats.get("hit"), "t": stats.get("t"),
        "buy_hold": bh,
        "vs_buy_hold": None if twr is None or bh is None else float(twr - bh),
    }


def run(force: bool = False) -> Dict[str, Any]:
    print("GOLD H1 V8 triple barrier", flush=True)
    ensure()
    if (RES / "READ.json").is_file() and not force:
        return {"ok": False, "error": "READ_EXISTS", "refuse_second_train": True}
    path = HIST / "GOLD_H1.csv"
    if not path.is_file():
        return {"ok": False, "error": "NO_H1"}
    bar = load_h1(path)
    names, x = build_native(bar)
    atr = atr_price(bar)
    y, signed, _touch = label_triple_barrier(bar, atr=atr, k=K, horizon=HORIZON)
    n = len(bar["open"])
    first = FIRST_PRED
    val_i = int(first + (1.0 - VAL_FRAC) * (n - first))
    research = np.zeros(n, dtype=bool)
    research[:val_i] = True
    research &= np.all(np.isfinite(x), axis=1) & np.isfinite(y)
    mix = label_mix(y)
    print("V8 labels n=%s cash_rate=%s long=%s short=%s" % (
        mix["n"], mix["cash_rate"], mix["long"], mix["short"]), flush=True)
    isin = true_in_sample(x, y, signed, names, research)
    print("V8 in-sample acc=%s ic=%s cash=%s" % (
        isin.get("acc"), isin.get("ic"), isin.get("cash_rate")), flush=True)
    pred, _pdiff, folds = walk_classes(x, y, signed, names)
    tr_acc = [f["train_acc"] for f in folds if f.get("train_acc") is not None]
    te_acc = [f["test_acc"] for f in folds if f.get("test_acc") is not None]
    tr_ics = [f["train_ic"] for f in folds if f.get("train_ic") is not None]
    te_ics = [f["test_ic"] for f in folds if f.get("test_ic") is not None]
    meta = _meta()
    long_s, long_tr = book(bar, meta, pred, atr, first, n)
    res_s, _ = book(bar, meta, pred, atr, first, val_i - 1)
    val_s, _ = book(bar, meta, pred, atr, val_i, n)
    verdict, deny, viable = _gate(val_s)
    month = [tr for tr in long_tr if tr["signal"][:10] >= "2026-08-11"]
    last_d = bar["ts"][-1][:10]
    regimes = []
    for rid, a, b in REGIMES:
        end = last_d if b is None else b
        rec = _regime_rows(bar, long_tr, a, end)
        rec["id"] = rid
        regimes.append(rec)
    ml = {
        "long_sample": long_s, "research_70": res_s, "validation_30": val_s,
        "last_month_diagnostic": _summ([tr["net"] for tr in month], HORIZON),
        "verdict": verdict, "deny": deny, "viable_historical": viable,
        "n_trades_long": len(long_tr),
        "rule": "三分类谁先碰 ±1.0 ATR；下一开盘进；触达下一开盘出或 24h 时间止",
    }
    fold_ic = {
        "n_folds": len(folds),
        "mean_train_acc": None if not tr_acc else float(np.mean(tr_acc)),
        "mean_test_acc": None if not te_acc else float(np.mean(te_acc)),
        "mean_train_ic": None if not tr_ics else float(np.mean(tr_ics)),
        "mean_test_ic": None if not te_ics else float(np.mean(te_ics)),
    }
    summary = {
        "profile": PROFILE, "ok": True, "candidate": False, "level1": False, "promise": False,
        "writes_9000": False, "us_shares": False, "timeframe": "H1",
        "k": K, "horizon": HORIZON, "coverage_def": COVERAGE_DEF,
        "n_bars": n, "first": bar["ts"][0], "last": bar["ts"][-1],
        "n_refits": len(folds), "features": names,
        "model": {"type": "LGBMClassifier", "params": dict(LGBM_CLF), "decision": "argmax"},
        "label_mix": mix,
        "true_in_sample": isin,
        "fold_ic": fold_ic,
        "regimes": regimes,
        "books": {"H1_TRIPLE": ml},
        "n_viable": int(viable),
        "note": "路径障碍，不是收盘符号。不是 Candidate。不覆盖 V1–V7。",
    }
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / "TRIPLE_trades.json").write_text(json.dumps(long_tr, ensure_ascii=False), encoding="utf-8")
    (RES / "FOLDS.json").write_text(json.dumps(folds, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
