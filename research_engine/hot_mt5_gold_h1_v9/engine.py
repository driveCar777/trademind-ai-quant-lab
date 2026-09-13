"""Same V1 24h sign shell; one tree on five a-priori clock+scale columns. One shot."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import numpy as np

from research_engine.hot_mt5_gold_h1.data import load_h1
from research_engine.hot_mt5_gold_h1 import engine as v1eng
from research_engine.hot_mt5_gold_h1.engine import HOLD, _meta, _window_reports
from research_engine.hot_mt5_gold_h1.train_val_regime import (
    _buy_hold,
    _fit_lgbm,
    _fit_metrics,
    _verdict,
)
from research_engine.hot_mt5_gold_h1_v9.paths import HIST, RES
from research_engine.hot_mt5_products.features import _sma
from research_engine.hot_mt5_products.products import LGBM_PARAMS, VAL_FRAC

PROFILE = "HOT_MT5_GOLD_H1_V9_SPARSE"
# Locked before any IC table. Clock + one-day scale. Not the best 5 from forensics.
SPARSE = ["R24", "VOL24", "DIST_SMA24", "HOUR_SIN", "HOUR_COS"]
REGIMES = (
    ("COVID_2020", "2020-02-01", "2020-06-30"),
    ("HIKING_2022", "2022-01-01", "2022-12-31"),
    ("CHOP_2023", "2023-01-01", "2023-12-31"),
    ("GOLD_BULL_2024_26", "2024-05-01", None),
)


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES


def build_sparse(bar: Dict[str, np.ndarray]) -> Tuple[List[str], np.ndarray]:
    c = bar["close"]
    n = len(c)
    r1 = np.full(n, np.nan)
    r1[1:] = c[1:] / c[:-1] - 1.0
    r24 = np.full(n, np.nan)
    r24[24:] = c[24:] / c[:-24] - 1.0
    vol24 = np.array([
        np.nanstd(r1[max(0, i - 23):i + 1]) if i >= 23 else np.nan for i in range(n)
    ])
    sma24 = _sma(c, 24)
    hour = bar["hour"]
    ang = 2.0 * math.pi * hour / 24.0
    pack = {
        "R24": r24,
        "VOL24": vol24,
        "DIST_SMA24": c / np.maximum(1e-12, sma24) - 1.0,
        "HOUR_SIN": np.sin(ang),
        "HOUR_COS": np.cos(ang),
    }
    x = np.column_stack([pack[k] for k in SPARSE]).astype(np.float64)
    return list(SPARSE), x


def walk_sparse(
    x: np.ndarray, y: np.ndarray, names: List[str],
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """Same protocol as train_val_regime.walk_fold_table; reads v1eng constants live."""
    import warnings
    warnings.filterwarnings("ignore", message="X does not have valid feature names")
    t_n = x.shape[0]
    scores = np.full(t_n, np.nan)
    folds: List[Dict[str, Any]] = []
    t = v1eng.FIRST_PRED
    fold = 0
    while t < t_n:
        cutoff = t - v1eng.EMBARGO
        if cutoff < v1eng.MIN_HIST:
            t += 1
            continue
        ok = np.all(np.isfinite(x[:cutoff]), axis=1) & np.isfinite(y[:cutoff])
        n_tr = int(ok.sum())
        if n_tr < 200:
            t += 1
            continue
        xtr = x[:cutoff][ok]
        ytr = y[:cutoff][ok]
        model = _fit_lgbm(xtr, ytr, names)
        tr = _fit_metrics(ytr, model.predict(xtr))
        end = min(t_n, t + v1eng.REFIT_EVERY)
        sl = slice(t, end)
        finite = np.all(np.isfinite(x[sl]), axis=1)
        pred = np.full(end - t, np.nan)
        if finite.any():
            pred[finite] = model.predict(x[sl][finite])
        scores[sl] = pred
        te_idx = np.arange(t, end)[finite]
        te = _fit_metrics(y[te_idx], scores[te_idx]) if len(te_idx) else _fit_metrics(
            np.array([]), np.array([]),
        )
        folds.append({
            "fold": fold,
            "fit_at_i": t,
            "through_i": end - 1,
            "n_train": n_tr,
            "n_test": int(len(te_idx)),
            "train_ic": tr["ic"], "test_ic": te["ic"],
            "train_r2": tr["r2"], "test_r2": te["r2"],
            "train_hit": tr["hit"], "test_hit": te["hit"],
            "score_min": te["score_min"], "score_max": te["score_max"],
            "score_std": te["score_std"], "n_unique": te["n_unique"],
            "stuck_constant": te["stuck_constant"],
            "train_score_std": tr["score_std"],
            "train_stuck_constant": tr["stuck_constant"],
        })
        print("  fold %d train_ic=%s test_ic=%s n_tr=%d n_te=%d stuck=%s" % (
            fold,
            None if tr["ic"] is None else round(tr["ic"], 4),
            None if te["ic"] is None else round(te["ic"], 4),
            n_tr, len(te_idx), te["stuck_constant"],
        ), flush=True)
        fold += 1
        t = end
    return scores, folds


def _slice_trades(trades: List[Dict[str, Any]], start: str, end: str) -> List[Dict[str, Any]]:
    out = []
    for tr in trades:
        d = tr["signal"][:10]
        if start <= d <= end:
            out.append(tr)
    return out


def _regime_table(bar, trades, last: str) -> List[Dict[str, Any]]:
    rows = []
    for rid, a, b in REGIMES:
        end = last if b is None else b
        sub = _slice_trades(trades, a, end)
        stats = v1eng._summ([t["net"] for t in sub], HOLD)
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
    print("GOLD H1 V9 sparse", flush=True)
    ensure()
    path = HIST / "GOLD_H1.csv"
    if not path.is_file():
        return {"ok": False, "error": "NO_H1"}
    bar = load_h1(path)
    names, x = build_sparse(bar)
    if names != list(SPARSE):
        raise RuntimeError("sparse feature list drifted")
    o = bar["open"]
    n = len(o)
    y = np.full(n, np.nan)
    y[: -(HOLD + 1)] = o[HOLD + 1:] / o[1:-HOLD] - 1.0
    first = v1eng.FIRST_PRED
    val_i = int(first + (1.0 - VAL_FRAC) * (n - first))
    research = np.zeros(n, dtype=bool)
    research[:val_i] = True
    research &= np.all(np.isfinite(x), axis=1) & np.isfinite(y)
    print("V9 true in-sample rows=%d val_i=%d" % (int(research.sum()), val_i), flush=True)
    if int(research.sum()) < 200:
        isin = {"ok": False, "error": "TOO_FEW_ROWS", "n_train": int(research.sum())}
    else:
        model_is = _fit_lgbm(x[research], y[research], names)
        pred_is = model_is.predict(x[research])
        isin = _fit_metrics(y[research], pred_is)
        isin["ok"] = True
        isin["n_train"] = int(research.sum())
    print("V9 in-sample ic=%s r2=%s hit=%s stuck=%s" % (
        isin.get("ic"), isin.get("r2"), isin.get("hit"), isin.get("stuck_constant"),
    ), flush=True)
    print("V9 walk-forward folds", flush=True)
    scores, folds = walk_sparse(x, y, names)
    tr_ics = [f["train_ic"] for f in folds if f.get("train_ic") is not None]
    te_ics = [f["test_ic"] for f in folds if f.get("test_ic") is not None]

    def ml_side(t):
        s = scores[t]
        if not np.isfinite(s):
            return 0
        return 1 if s > 0 else -1

    meta = _meta()
    ml = _window_reports(bar, meta, ml_side, first, val_i, n)
    trades = ml.pop("trades")
    last = bar["ts"][-1][:10]
    regimes = _regime_table(bar, trades, last)
    oos = np.isfinite(scores) & np.isfinite(y)
    fit_v = _verdict(isin, folds) if folds else {"kind": "NO_FOLDS"}
    summary = {
        "profile": PROFILE, "ok": True, "candidate": False, "level1": False, "promise": False,
        "writes_9000": False, "us_shares": False, "timeframe": "H1", "hold": HOLD,
        "n_bars": n, "first": bar["ts"][0], "last": bar["ts"][-1],
        "n_refits": len(folds), "features": names,
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
        "v1_anchor": {"true_in_sample_ic": 0.52, "mean_fold_test_ic": 0.038},
        "books": {
            "H1_SPARSE": {
                **ml,
                "rule": "先验五列 LightGBM + sign(score)，持有 24 根",
            },
        },
        "n_viable": int(ml["viable_historical"]),
        "note": "稀疏五列对照。不是从 IC 表挑列。不是 Candidate。不晋升状态窗。",
    }
    import json
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / "SPARSE_trades.json").write_text(json.dumps(trades, ensure_ascii=False), encoding="utf-8")
    (RES / "FOLDS.json").write_text(json.dumps(folds, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
