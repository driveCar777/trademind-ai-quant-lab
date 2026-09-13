"""Read-only: true in-sample / purged fold IC / regimes. Does not rewrite READ.json."""
from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research_engine.hot_mt5_gold_h1.data import build_h1_matrix, load_h1
from research_engine.hot_mt5_gold_h1.engine import (
    EMBARGO,
    FIRST_PRED,
    HOLD,
    MIN_HIST,
    REFIT_EVERY,
    _summ,
)
from research_engine.hot_mt5_gold_h1.paths import HIST, RES
from research_engine.hot_mt5_gold_h1.why_so_bad import verify_trades
from research_engine.hot_mt5_products.products import LGBM_PARAMS, VAL_FRAC

# Pre-declared. Do not pick winners after seeing numbers.
REGIMES = (
    ("COVID_2020", "2020-02-01", "2020-06-30"),
    ("HIKING_2022", "2022-01-01", "2022-12-31"),
    ("CHOP_2023", "2023-01-01", "2023-12-31"),
    ("GOLD_BULL_2024_26", "2024-05-01", "2026-09-11"),
)
STUCK_STD = 1e-12
STUCK_UNIQUE = 2


def _pearson(a: np.ndarray, b: np.ndarray) -> Optional[float]:
    m = np.isfinite(a) & np.isfinite(b)
    if int(m.sum()) < 10:
        return None
    aa, bb = a[m], b[m]
    if float(aa.std()) < STUCK_STD or float(bb.std()) < STUCK_STD:
        return 0.0
    return float(np.corrcoef(aa, bb)[0, 1])


def _r2(y: np.ndarray, p: np.ndarray) -> Optional[float]:
    m = np.isfinite(y) & np.isfinite(p)
    if int(m.sum()) < 10:
        return None
    yt, yp = y[m], p[m]
    ss_res = float(np.sum((yt - yp) ** 2))
    ss_tot = float(np.sum((yt - yt.mean()) ** 2))
    if ss_tot < 1e-18:
        return None
    return 1.0 - ss_res / ss_tot


def _hit(y: np.ndarray, p: np.ndarray) -> Optional[float]:
    m = np.isfinite(y) & np.isfinite(p)
    if int(m.sum()) < 10:
        return None
    return float(np.mean(np.sign(p[m]) == np.sign(y[m])))


def _score_pack(p: np.ndarray) -> Dict[str, Any]:
    s = p[np.isfinite(p)]
    if len(s) == 0:
        return {
            "n": 0, "mean_abs_score": None, "score_min": None, "score_max": None,
            "score_std": None, "n_unique": 0, "stuck_constant": True,
        }
    n_unique = int(np.unique(np.round(s, 10)).size)
    std = float(s.std())
    return {
        "n": int(len(s)),
        "mean_abs_score": float(np.mean(np.abs(s))),
        "score_min": float(s.min()),
        "score_max": float(s.max()),
        "score_std": std,
        "n_unique": n_unique,
        "stuck_constant": bool(std < STUCK_STD or n_unique <= STUCK_UNIQUE),
    }


def _fit_metrics(y: np.ndarray, p: np.ndarray) -> Dict[str, Any]:
    pack = _score_pack(p)
    pack["ic"] = _pearson(p, y)
    pack["r2"] = _r2(y, p)
    pack["hit"] = _hit(y, p)
    return pack


def _fit_lgbm(x: np.ndarray, y: np.ndarray, names: List[str]):
    import warnings
    import lightgbm as lgb
    warnings.filterwarnings("ignore", message="X does not have valid feature names")
    model = lgb.LGBMRegressor(**LGBM_PARAMS)
    model.fit(x, np.clip(y, -5, 5), feature_name=names)
    return model


def true_in_sample(x: np.ndarray, y: np.ndarray, names: List[str], mask: np.ndarray) -> Dict[str, Any]:
    if int(mask.sum()) < 200:
        return {"ok": False, "error": "TOO_FEW_ROWS"}
    model = _fit_lgbm(x[mask], y[mask], names)
    pred = np.full(len(y), np.nan)
    pred[mask] = model.predict(x[mask])
    out = _fit_metrics(y[mask], pred[mask])
    out["ok"] = True
    out["n_train"] = int(mask.sum())
    return out


def walk_fold_table(x: np.ndarray, y: np.ndarray, names: List[str]) -> Tuple[List[Dict[str, Any]], np.ndarray]:
    import warnings
    warnings.filterwarnings("ignore", message="X does not have valid feature names")
    t_n = x.shape[0]
    scores = np.full(t_n, np.nan)
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
        if n_tr < 200:
            t += 1
            continue
        model = _fit_lgbm(x[:cutoff][ok], y[:cutoff][ok], names)
        tr_pred = model.predict(x[:cutoff][ok])
        tr = _fit_metrics(y[:cutoff][ok], tr_pred)
        end = min(t_n, t + REFIT_EVERY)
        sl = slice(t, end)
        finite = np.all(np.isfinite(x[sl]), axis=1)
        pred = np.full(end - t, np.nan)
        if finite.any():
            pred[finite] = model.predict(x[sl][finite])
        scores[sl] = pred
        te_idx = np.arange(t, end)[finite]
        if len(te_idx):
            te = _fit_metrics(y[te_idx], scores[te_idx])
        else:
            te = _fit_metrics(np.array([]), np.array([]))
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
        fold += 1
        t = end
        print("  fold %d train_ic=%s test_ic=%s n_tr=%d n_te=%d stuck=%s" % (
            fold - 1,
            None if tr["ic"] is None else round(tr["ic"], 4),
            None if te["ic"] is None else round(te["ic"], 4),
            n_tr, len(te_idx), te["stuck_constant"],
        ), flush=True)
    return folds, scores


def _feature_ics(names: List[str], x: np.ndarray, y: np.ndarray, mask: np.ndarray) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {}
    for j, name in enumerate(names):
        out[name] = _pearson(x[:, j][mask], y[mask])
    return out


def _in_range(ts: str, start: str, end: str) -> bool:
    d = ts[:10]
    return start <= d <= end


def _book_slice(trades: List[Dict[str, Any]], start: str, end: str) -> Dict[str, Any]:
    xs = [tr for tr in trades if _in_range(tr["signal"], start, end)]
    stats = _summ([tr["net"] for tr in xs], HOLD)
    stats["n_trades"] = len(xs)
    return stats


def _buy_hold(bar: Dict[str, Any], start: str, end: str) -> Optional[float]:
    c = bar["close"]
    idx = [i for i, t in enumerate(bar["ts"]) if _in_range(t, start, end)]
    if len(idx) < 2:
        return None
    a, b = float(c[idx[0]]), float(c[idx[-1]])
    if a <= 0:
        return None
    return b / a - 1.0


def _regime_rows(bar, trades, y, names, x, first: str, last: str) -> Dict[str, Any]:
    book = _book_slice(trades, first, last)
    bh = _buy_hold(bar, first, last)
    mask = np.array([_in_range(t, first, last) for t in bar["ts"]]) & np.isfinite(y)
    feat = _feature_ics(names, x, y, mask)
    twr = book.get("twr")
    return {
        "start": first, "end": last,
        "n_trades": book["n_trades"],
        "twr": twr, "hit": book.get("hit"), "t": book.get("t"),
        "buy_hold": bh,
        "vs_buy_hold": None if twr is None or bh is None else float(twr - bh),
        "feature_ic": feat,
        "n_label_rows": int(mask.sum()),
    }


def _verdict(isin: Dict[str, Any], folds: List[Dict[str, Any]]) -> Dict[str, Any]:
    ics = [f["train_ic"] for f in folds if f.get("train_ic") is not None]
    tes = [f["test_ic"] for f in folds if f.get("test_ic") is not None]
    stuck_te = sum(1 for f in folds if f.get("stuck_constant"))
    stuck_tr = sum(1 for f in folds if f.get("train_stuck_constant"))
    mean_tr = float(np.mean(ics)) if ics else None
    mean_te = float(np.mean(tes)) if tes else None
    is_ic = isin.get("ic")
    is_r2 = isin.get("r2")
    if isin.get("stuck_constant") or stuck_tr > 0 or stuck_te > len(folds) // 2:
        kind = "CONSTANT_SCORES_BUG"
    elif is_ic is not None and abs(is_ic) < 0.02 and (is_r2 is None or abs(is_r2) < 0.01):
        kind = "DEAD_FEATURES_OR_TARGET"
    elif mean_tr is not None and mean_tr >= 0.15 and (mean_te is None or abs(mean_te) < 0.08):
        kind = "OVERFIT"
    elif mean_tr is not None and mean_tr >= 0.08 and mean_te is not None and mean_te >= 0.04:
        kind = "FITS_AND_TRANSFERS"
    else:
        kind = "WEAK_FIT_WEAK_OOS"
    return {
        "kind": kind,
        "true_in_sample_ic": is_ic,
        "true_in_sample_r2": is_r2,
        "mean_fold_train_ic": mean_tr,
        "mean_fold_test_ic": mean_te,
        "n_folds": len(folds),
        "n_folds_test_stuck": stuck_te,
        "n_folds_train_stuck": stuck_tr,
    }


def diagnose_family(bar, names, x, y, trades, label: str) -> Dict[str, Any]:
    n = len(y)
    first = FIRST_PRED
    val_i = int(first + (1.0 - VAL_FRAC) * (n - first))
    research = np.zeros(n, dtype=bool)
    research[:val_i] = True
    research &= np.all(np.isfinite(x), axis=1) & np.isfinite(y)
    print("%s true in-sample rows=%d val_i=%d" % (label, int(research.sum()), val_i), flush=True)
    isin = true_in_sample(x, y, names, research)
    print("%s in-sample ic=%s r2=%s hit=%s stuck=%s" % (
        label, isin.get("ic"), isin.get("r2"), isin.get("hit"), isin.get("stuck_constant"),
    ), flush=True)
    print("%s walk-forward folds" % label, flush=True)
    folds, scores = walk_fold_table(x, y, names)
    years = []
    for yr in range(2019, 2027):
        rec = _regime_rows(bar, trades, y, names, x, "%d-01-01" % yr, "%d-12-31" % yr)
        rec["id"] = "Y%d" % yr
        years.append(rec)
    regimes = []
    for rid, a, b in REGIMES:
        rec = _regime_rows(bar, trades, y, names, x, a, b)
        rec["id"] = rid
        regimes.append(rec)
    feat_research = _feature_ics(names, x, y, research)
    oos = np.isfinite(scores) & np.isfinite(y)
    return {
        "label": label,
        "features": names,
        "n_bars": n,
        "val_i": val_i,
        "research_n": int(research.sum()),
        "lgbm_params": dict(LGBM_PARAMS),
        "true_in_sample": isin,
        "folds": folds,
        "verdict": _verdict(isin, folds),
        "oos_score_vs_y": _fit_metrics(y[oos], scores[oos]) if int(oos.sum()) else {},
        "feature_ic_research": feat_research,
        "regimes": regimes,
        "years": years,
        "n_finite_oos_scores": int(np.isfinite(scores).sum()),
    }


def run() -> Dict[str, Any]:
    print("GOLD H1 train/val/regime diagnostic (read-only)", flush=True)
    path = HIST / "GOLD_H1.csv"
    if not path.is_file():
        return {"ok": False, "error": "NO_H1"}
    read_path = RES / "READ.json"
    before = read_path.read_bytes() if read_path.is_file() else b""
    bar = load_h1(path)
    names, x = build_h1_matrix(bar)
    o = bar["open"]
    n = len(o)
    y = np.full(n, np.nan)
    y[: -(HOLD + 1)] = o[HOLD + 1:] / o[1:-HOLD] - 1.0
    ml = json.loads((RES / "ML_trades.json").read_text(encoding="utf-8"))
    audit = verify_trades(bar, ml)

    v1 = diagnose_family(bar, names, x, y, ml, "H1_ML")

    v5 = None
    try:
        from research_engine.hot_mt5_gold_h1_v5.engine import build_native
        from research_engine.hot_mt5_gold_h1_v5.paths import RES as V5RES
        native_tr = V5RES / "NATIVE_trades.json"
        if native_tr.is_file():
            n5, x5 = build_native(bar)
            t5 = json.loads(native_tr.read_text(encoding="utf-8"))
            print("V5 native diagnostic", flush=True)
            v5 = diagnose_family(bar, n5, x5, y, t5, "H1_NATIVE")
    except Exception as exc:
        v5 = {"ok": False, "error": str(exc)}

    after = read_path.read_bytes() if read_path.is_file() else b""
    out = {
        "profile": "HOT_MT5_GOLD_H1_TRAIN_VAL_REGIME",
        "ok": True,
        "candidate": False,
        "rewrites_read": False,
        "read_untouched": after == before,
        "trade_audit": audit,
        "v1": v1,
        "v5": v5,
        "note": "research_70 in V1 READ is walk-forward OOS, not true in-sample. This file is the train-set test.",
    }
    (RES / "TRAIN_VAL_REGIME.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    if after != before:
        raise RuntimeError("READ.json changed — abort")
    return out


def main():
    out = run()
    if not out.get("ok"):
        print(out)
        return 1
    v1 = out["v1"]
    ver = v1["verdict"]
    print("AUDIT mismatch", out["trade_audit"], "READ untouched", out["read_untouched"])
    print("VERDICT", ver)
    print("IN-SAMPLE", v1["true_in_sample"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
