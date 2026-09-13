"""Remaining London-NY session return on GOLD H1. Not 24h sign, not V2 ORB."""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research_engine.hot_mt5_gold_h1.data import load_h1
from research_engine.hot_mt5_gold_h1.train_val_regime import (
    _buy_hold,
    _fit_lgbm,
    _fit_metrics,
    _verdict,
)
from research_engine.hot_mt5_gold_h1_v5.engine import NATIVE, build_native
from research_engine.hot_mt5_gold_h1_v7.paths import HIST, RES
from research_engine.hot_mt5_products.products import LGBM_PARAMS, SLIP, VAL_FRAC

PROFILE = "HOT_MT5_GOLD_H1_V7_SESSION_REMAIN"
SIGNAL_H0 = 7
SIGNAL_H1 = 15
EXIT_HOUR = 20
LAMBDA = 1.0
FIRST_PRED = 2000
REFIT_EVERY = 1000
MIN_HIST = 1500
MIN_TRAIN = 200
EMBARGO_FLOOR = 20
MIN_COVERAGE = 0.15
MIN_VAL_TRADES = 8
REGIMES = (
    ("COVID_2020", "2020-02-01", "2020-06-30"),
    ("HIKING_2022", "2022-01-01", "2022-12-31"),
    ("CHOP_2023", "2023-01-01", "2023-12-31"),
    ("GOLD_BULL_2024_26", "2024-05-01", None),
)


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES


def _meta() -> Dict[str, Any]:
    p = HIST / "GOLD_META.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"point": 0.01, "spread_points_now": 34, "bid": 4300.0}


def _hour_ok(h: int) -> bool:
    return SIGNAL_H0 <= h <= SIGNAL_H1


def build_exits(bar: Dict[str, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    ts = bar["ts"]
    hours = bar["hour"].astype(int)
    n = len(ts)
    t_exit = np.full(n, -1, dtype=np.int64)
    hours_to_exit = np.full(n, np.nan)
    by_date: Dict[str, List[int]] = defaultdict(list)
    for i, d in enumerate(bar["dates"]):
        by_date[d].append(i)
    for t in range(n):
        entry = t + 1
        if entry >= n:
            continue
        d = bar["dates"][t]
        for u in by_date[d]:
            if u > entry and int(hours[u]) >= EXIT_HOUR:
                t_exit[t] = u
                hours_to_exit[t] = float(u - entry)
                break
    return t_exit, hours_to_exit


def build_y(bar: Dict[str, np.ndarray], t_exit: np.ndarray) -> np.ndarray:
    o = bar["open"]
    hours = bar["hour"].astype(int)
    n = len(o)
    y = np.full(n, np.nan)
    for t in range(n):
        if not _hour_ok(int(hours[t])):
            continue
        ex = int(t_exit[t])
        if ex < 0:
            continue
        entry = t + 1
        if entry >= n:
            continue
        if o[entry] <= 0 or not np.isfinite(o[entry]) or not np.isfinite(o[ex]):
            continue
        y[t] = float(o[ex] / o[entry] - 1.0)
    return y


def embargo_bars(hours_to_exit: np.ndarray) -> int:
    mx = float(np.nanmax(hours_to_exit)) if np.isfinite(hours_to_exit).any() else float(EMBARGO_FLOOR)
    if not np.isfinite(mx):
        mx = float(EMBARGO_FLOOR)
    return max(EMBARGO_FLOOR, int(mx)) + 1


def eligible_days(bar: Dict[str, np.ndarray], t_exit: np.ndarray) -> List[str]:
    hours = bar["hour"].astype(int)
    seen = []
    have = set()
    for t, d in enumerate(bar["dates"]):
        if d in have:
            continue
        if _hour_ok(int(hours[t])) and int(t_exit[t]) >= 0:
            have.add(d)
            seen.append(d)
    return seen


def _fill_cost(bar, meta, t_in: int) -> float:
    px = float(bar["open"][t_in])
    pt = float(meta.get("point") or 0.01)
    raw = float(bar["spread"][t_in]) * pt / max(1e-12, float(bar["close"][t_in]))
    now = float(meta.get("spread_points_now") or 0) * pt / max(1e-12, float(meta.get("bid") or px))
    spread = max(0.0, now) if (not np.isfinite(raw) or raw <= 0) else max(raw, now * 0.25)
    return spread + 2 * SLIP


def _summ(rets: List[float], cal_yrs: Optional[float] = None) -> Dict[str, Any]:
    x = np.array(rets, dtype=np.float64)
    empty = {"n_periods": 0, "twr": None, "cagr": None, "mean": None, "t": None,
             "hit": None, "maxdd": None, "payoff": None}
    if len(x) == 0:
        return empty
    eq = np.cumprod(1.0 + x)
    yrs = cal_yrs if cal_yrs and cal_yrs > 0 else max(1e-9, len(x) / 252.0)
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


def walk_scores(
    x: np.ndarray,
    y: np.ndarray,
    names: List[str],
    t_exit: np.ndarray,
    embargo: int,
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    import warnings
    warnings.filterwarnings("ignore", message="X does not have valid feature names")
    t_n = x.shape[0]
    scores = np.full(t_n, np.nan)
    folds: List[Dict[str, Any]] = []
    t = FIRST_PRED
    fold = 0
    while t < t_n:
        cutoff = t - embargo
        if cutoff < MIN_HIST:
            t += 1
            continue
        finite = np.all(np.isfinite(x[:cutoff]), axis=1) & np.isfinite(y[:cutoff])
        realized = (t_exit[:cutoff] >= 0) & (t_exit[:cutoff] < t)
        ok = finite & realized
        n_tr = int(ok.sum())
        if n_tr < MIN_TRAIN:
            t += 1
            continue
        model = _fit_lgbm(x[:cutoff][ok], y[:cutoff][ok], names)
        tr_pred = model.predict(x[:cutoff][ok])
        tr = _fit_metrics(y[:cutoff][ok], tr_pred)
        end = min(t_n, t + REFIT_EVERY)
        sl = slice(t, end)
        row_ok = np.all(np.isfinite(x[sl]), axis=1)
        pred = np.full(end - t, np.nan)
        if row_ok.any():
            pred[row_ok] = model.predict(x[sl][row_ok])
        scores[sl] = pred
        te_mask = row_ok & np.isfinite(y[sl])
        te_idx = np.arange(t, end)[te_mask]
        te = _fit_metrics(y[te_idx], scores[te_idx]) if len(te_idx) else _fit_metrics(np.array([]), np.array([]))
        folds.append({
            "fold": fold, "fit_at_i": t, "through_i": end - 1,
            "n_train": n_tr, "n_test": int(len(te_idx)),
            "train_ic": tr["ic"], "test_ic": te["ic"],
            "train_r2": tr["r2"], "test_r2": te["r2"],
            "train_hit": tr["hit"], "test_hit": te["hit"],
            "score_min": te["score_min"], "score_max": te["score_max"],
            "score_std": te["score_std"], "n_unique": te["n_unique"],
            "stuck_constant": te["stuck_constant"],
            "train_score_std": tr["score_std"],
            "train_stuck_constant": tr["stuck_constant"],
        })
        print("  fold %d train_ic=%s test_ic=%s n_tr=%d n_te=%d" % (
            fold,
            None if tr["ic"] is None else round(tr["ic"], 4),
            None if te["ic"] is None else round(te["ic"], 4),
            n_tr, len(te_idx),
        ), flush=True)
        fold += 1
        t = end
    return scores, folds


def sides_from_scores(scores: np.ndarray, atr_frac: np.ndarray, hours: np.ndarray) -> np.ndarray:
    n = len(scores)
    side = np.zeros(n, dtype=np.int64)
    for t in range(n):
        if not _hour_ok(int(hours[t])):
            continue
        s, a = scores[t], atr_frac[t]
        if not np.isfinite(s) or not np.isfinite(a):
            continue
        if abs(float(s)) > LAMBDA * float(a):
            side[t] = 1 if s > 0 else -1
    return side


def fills(bar, meta, side: np.ndarray, t_exit: np.ndarray) -> List[Dict[str, Any]]:
    ts, o, hours = bar["ts"], bar["open"], bar["hour"].astype(int)
    n = len(ts)
    trades: List[Dict[str, Any]] = []
    used_day = set()
    for t in range(n):
        d = bar["dates"][t]
        if d in used_day:
            continue
        if not _hour_ok(int(hours[t])):
            continue
        if int(side[t]) == 0:
            continue
        ex = int(t_exit[t])
        t_in = t + 1
        if ex < 0 or t_in >= n:
            continue
        if bar["dates"][t_in] != d or bar["dates"][ex] != d:
            continue
        if o[t_in] <= 0 or not np.isfinite(o[t_in]) or not np.isfinite(o[ex]):
            continue
        sgn = int(side[t])
        raw = (float(o[ex]) / float(o[t_in]) - 1.0) * sgn
        cost = _fill_cost(bar, meta, t_in)
        trades.append({
            "signal": ts[t], "entry": ts[t_in], "exit": ts[ex],
            "side": "LONG" if sgn > 0 else "SHORT",
            "hours": int(ex - t_in),
            "raw": float(raw), "cost": float(cost), "net": float(raw - cost),
            "score": None,
        })
        used_day.add(d)
    return trades


def _cal_yrs(trades: List[Dict[str, Any]]) -> Optional[float]:
    if not trades:
        return None
    try:
        d0 = dt.date.fromisoformat(trades[0]["signal"][:10])
        d1 = dt.date.fromisoformat(trades[-1]["exit"][:10])
        return max(1e-9, (d1 - d0).days / 365.25)
    except Exception:
        return None


def _slice(trades: List[Dict[str, Any]], start_d: Optional[str], end_d: Optional[str]) -> List[Dict[str, Any]]:
    out = []
    for tr in trades:
        d = tr["signal"][:10]
        if start_d and d < start_d:
            continue
        if end_d and d > end_d:
            continue
        out.append(tr)
    return out


def _gate(val_s: Dict[str, Any]) -> Tuple[str, Optional[str], bool]:
    cover_fail = bool((val_s.get("n_periods") or 0) < MIN_VAL_TRADES or (val_s.get("coverage") or 0) < MIN_COVERAGE)
    viable = bool(not cover_fail and (val_s.get("twr") or 0) > 0 and (val_s.get("t") or 0) > 1.0)
    if cover_fail:
        return "NO_CANDIDATE", "VALIDATION_COVERAGE", False
    if viable:
        return "VIABLE_HISTORICAL", None, True
    return "NO_CANDIDATE", "VALIDATION_GATE", False


def _report(trades, elig: List[str], start_d: str, end_d: Optional[str]) -> Dict[str, Any]:
    days = [d for d in elig if d >= start_d and (end_d is None or d <= end_d)]
    sub = _slice(trades, start_d, end_d)
    stats = _summ([t["net"] for t in sub], _cal_yrs(sub))
    stats["coverage"] = (len(sub) / float(len(days))) if days else 0.0
    stats["n_eligible_days"] = len(days)
    stats["n_cash_days"] = max(0, len(days) - len(sub))
    return stats


def _book(trades, elig: List[str]) -> Dict[str, Any]:
    if not elig:
        empty = _summ([])
        empty.update({"coverage": 0.0, "n_eligible_days": 0, "n_cash_days": 0})
        return {
            "long_sample": empty, "research_70": empty, "validation_30": empty,
            "last_month_diagnostic": _summ([]),
            "verdict": "NO_CANDIDATE", "deny": "VALIDATION_COVERAGE",
            "viable_historical": False, "n_trades_long": 0,
        }
    cut = int((1.0 - VAL_FRAC) * len(elig))
    if cut < 1:
        cut = 1
    if cut >= len(elig):
        cut = len(elig) - 1
    res_end = elig[cut - 1]
    val_start = elig[cut]
    long_s = _report(trades, elig, elig[0], None)
    res_s = _report(trades, elig, elig[0], res_end)
    val_s = _report(trades, elig, val_start, None)
    verdict, deny, viable = _gate(val_s)
    month = [t for t in trades if t["signal"][:10] >= "2026-08-11"]
    return {
        "long_sample": long_s, "research_70": res_s, "validation_30": val_s,
        "last_month_diagnostic": _summ([t["net"] for t in month]),
        "verdict": verdict, "deny": deny, "viable_historical": viable,
        "n_trades_long": len(trades),
        "val_start": val_start, "research_end": res_end,
    }


def _regime_table(bar, trades, last: str) -> List[Dict[str, Any]]:
    rows = []
    for rid, a, b in REGIMES:
        end = last if b is None else b
        sub = _slice(trades, a, end)
        stats = _summ([t["net"] for t in sub], _cal_yrs(sub))
        bh = _buy_hold(bar, a, end)
        twr = stats.get("twr")
        rows.append({
            "id": rid, "start": a, "end": end,
            "n_trades": len(sub),
            "twr": twr, "hit": stats.get("hit"), "t": stats.get("t"),
            "buy_hold": bh,
            "vs_buy_hold": None if twr is None or bh is None else float(twr - bh),
        })
    return rows


def run() -> Dict[str, Any]:
    print("GOLD H1 V7 session remain", flush=True)
    ensure()
    path = HIST / "GOLD_H1.csv"
    if not path.is_file():
        return {"ok": False, "error": "NO_H1"}
    bar = load_h1(path)
    names, x = build_native(bar)
    t_exit, hours_to_exit = build_exits(bar)
    y = build_y(bar, t_exit)
    embargo = embargo_bars(hours_to_exit)
    elig = eligible_days(bar, t_exit)
    n = len(y)
    if not elig:
        return {"ok": False, "error": "NO_ELIGIBLE_DAYS"}
    cut = int((1.0 - VAL_FRAC) * len(elig))
    if cut < 1:
        cut = 1
    if cut >= len(elig):
        cut = len(elig) - 1
    research_end = elig[cut - 1]
    dates = np.array(bar["dates"])
    research = (dates <= research_end) & np.all(np.isfinite(x), axis=1) & np.isfinite(y)
    print("V7 true in-sample rows=%d embargo=%d elig=%d" % (int(research.sum()), embargo, len(elig)), flush=True)
    if int(research.sum()) < MIN_TRAIN:
        isin = {"ok": False, "error": "TOO_FEW_ROWS", "n_train": int(research.sum())}
    else:
        model_is = _fit_lgbm(x[research], y[research], names)
        pred_is = model_is.predict(x[research])
        isin = _fit_metrics(y[research], pred_is)
        isin["ok"] = True
        isin["n_train"] = int(research.sum())
    print("V7 in-sample ic=%s r2=%s hit=%s stuck=%s" % (
        isin.get("ic"), isin.get("r2"), isin.get("hit"), isin.get("stuck_constant"),
    ), flush=True)
    print("V7 walk-forward folds", flush=True)
    scores, folds = walk_scores(x, y, names, t_exit, embargo)
    atr_idx = names.index("ATR14")
    atr_frac = x[:, atr_idx]
    side = sides_from_scores(scores, atr_frac, bar["hour"])
    meta = _meta()
    trades = fills(bar, meta, side, t_exit)
    for tr in trades:
        # attach walk-forward score of the signal bar
        try:
            i = bar["ts"].index(tr["signal"])
            tr["score"] = None if not np.isfinite(scores[i]) else float(scores[i])
        except ValueError:
            tr["score"] = None
    book = _book(trades, elig)
    tr_ics = [f["train_ic"] for f in folds if f.get("train_ic") is not None]
    te_ics = [f["test_ic"] for f in folds if f.get("test_ic") is not None]
    last = bar["ts"][-1][:10]
    regimes = _regime_table(bar, trades, last)
    oos = np.isfinite(scores) & np.isfinite(y)
    fit_v = _verdict(isin, folds) if folds else {"kind": "NO_FOLDS"}
    summary = {
        "profile": PROFILE, "ok": True, "candidate": False, "level1": False, "promise": False,
        "writes_9000": False, "us_shares": False, "timeframe": "H1",
        "overnight": False, "lambda": LAMBDA,
        "signal_hours_utc": [SIGNAL_H0, SIGNAL_H1], "exit_hour_utc": EXIT_HOUR,
        "n_bars": n, "first": bar["ts"][0], "last": bar["ts"][-1],
        "n_eligible_days": len(elig),
        "n_refits": len(folds), "embargo": embargo, "features": names,
        "lgbm_params": dict(LGBM_PARAMS),
        "true_in_sample": isin,
        "fold_ic": {
            "n_folds": len(folds),
            "mean_train_ic": None if not tr_ics else float(np.mean(tr_ics)),
            "mean_test_ic": None if not te_ics else float(np.mean(te_ics)),
            "median_train_ic": None if not tr_ics else float(np.median(tr_ics)),
            "median_test_ic": None if not te_ics else float(np.median(te_ics)),
            "n_test_ic_pos": int(sum(1 for v in te_ics if v > 0)),
        },
        "fit_verdict": fit_v,
        "oos_score_vs_y": _fit_metrics(y[oos], scores[oos]) if int(oos.sum()) else {},
        "regimes": regimes,
        "books": {
            "H1_SESSION_REMAIN": {
                **book,
                "rule": "小时钟 13 列 LightGBM 预测场次剩余；|score|>1×ATR 才做；每日一笔，当日 ≥20:00 出",
            },
        },
        "n_viable": int(book["viable_historical"]),
        "note": "场次剩余收益。不是 24h 符号。不是 Candidate。不晋升状态窗。",
    }
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / "REMAIN_trades.json").write_text(json.dumps(trades, ensure_ascii=False), encoding="utf-8")
    (RES / "FOLDS.json").write_text(json.dumps(folds, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
