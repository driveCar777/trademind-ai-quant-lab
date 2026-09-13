"""Same V1 24h sign shell; Ridge(alpha=1) after per-fold z-score. One shot."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

from research_engine.hot_mt5_gold_h1.data import build_h1_matrix, load_h1
from research_engine.hot_mt5_gold_h1 import engine as v1eng
from research_engine.hot_mt5_gold_h1.engine import HOLD, _meta, _window_reports
from research_engine.hot_mt5_gold_h1.train_val_regime import _fit_metrics
from research_engine.hot_mt5_gold_h1_v6.paths import HIST, RES
from research_engine.hot_mt5_products.products import VAL_FRAC

PROFILE = "HOT_MT5_GOLD_H1_V6_RIDGE"
RIDGE_ALPHA = 1.0


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES


def _zscore(train: np.ndarray, test: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    mu = np.nanmean(train, axis=0)
    sd = np.nanstd(train, axis=0)
    sd = np.where(sd < 1e-12, 1.0, sd)
    return (train - mu) / sd, (test - mu) / sd


def _fit_ridge(x: np.ndarray, y: np.ndarray):
    from sklearn.linear_model import Ridge
    model = Ridge(alpha=RIDGE_ALPHA)
    model.fit(x, np.clip(y, -5, 5))
    return model


def walk_ridge(x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
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
        end = min(t_n, t + v1eng.REFIT_EVERY)
        sl = slice(t, end)
        finite = np.all(np.isfinite(x[sl]), axis=1)
        xte = x[sl]
        xz_tr, xz_all = _zscore(xtr, np.vstack([xtr, xte]))
        xz_te = xz_all[len(xtr):]
        model = _fit_ridge(xz_tr, ytr)
        tr_pred = model.predict(xz_tr)
        pred = np.full(end - t, np.nan)
        if finite.any():
            pred[finite] = model.predict(xz_te[finite])
        scores[sl] = pred
        tr = _fit_metrics(ytr, tr_pred)
        te_idx = np.arange(t, end)[finite]
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
        })
        fold += 1
        t = end
    return scores, folds


def run() -> Dict[str, Any]:
    print("GOLD H1 V6 Ridge", flush=True)
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
    first = v1eng.FIRST_PRED
    val_i = int(first + (1.0 - VAL_FRAC) * (n - first))
    research = np.zeros(n, dtype=bool)
    research[:val_i] = True
    research &= np.all(np.isfinite(x), axis=1) & np.isfinite(y)
    xz_is, _ = _zscore(x[research], x[research])
    model_is = _fit_ridge(xz_is, y[research])
    pred_is = model_is.predict(xz_is)
    isin = _fit_metrics(y[research], pred_is)
    isin["ok"] = True
    isin["n_train"] = int(research.sum())
    print("V6 in-sample ic=%s r2=%s hit=%s" % (isin.get("ic"), isin.get("r2"), isin.get("hit")), flush=True)
    scores, folds = walk_ridge(x, y)
    tr_ics = [f["train_ic"] for f in folds if f.get("train_ic") is not None]
    te_ics = [f["test_ic"] for f in folds if f.get("test_ic") is not None]

    def ml_side(t):
        s = scores[t]
        if not np.isfinite(s):
            return 0
        return 1 if s > 0 else -1

    meta = _meta()
    ml = _window_reports(bar, meta, ml_side, first, val_i, n)
    tr = ml.pop("trades")
    summary = {
        "profile": PROFILE, "ok": True, "candidate": False, "level1": False, "promise": False,
        "writes_9000": False, "us_shares": False, "timeframe": "H1", "hold": HOLD,
        "n_bars": n, "first": bar["ts"][0], "last": bar["ts"][-1],
        "n_refits": len(folds), "features": names,
        "model": {"type": "Ridge", "alpha": RIDGE_ALPHA, "standardize": True},
        "true_in_sample": isin,
        "fold_ic": {
            "n_folds": len(folds),
            "mean_train_ic": None if not tr_ics else float(np.mean(tr_ics)),
            "mean_test_ic": None if not te_ics else float(np.mean(te_ics)),
        },
        "books": {
            "H1_RIDGE": {**ml, "rule": "标准化 + Ridge(α=1) + sign(score)，持有 24 根"},
        },
        "n_viable": int(ml["viable_historical"]),
        "note": "过拟合对照。不是 Candidate。不覆盖 V1–V5。",
    }
    import json
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / "RIDGE_trades.json").write_text(json.dumps(tr, ensure_ascii=False), encoding="utf-8")
    (RES / "FOLDS.json").write_text(json.dumps(folds, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
