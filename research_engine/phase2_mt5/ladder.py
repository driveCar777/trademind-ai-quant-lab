"""EXP-001 model ladder: Naive → Linear only. Stop if no RESEARCH OOS increment."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research_engine.hot_mt5_products.features import _atr, _rsi, _sma
from research_engine.phase2_mt5 import FINAL_OOS_START, FLAT_THRESHOLD, RESEARCH_END, SEED
from research_engine.phase2_mt5.baselines import book_sides, load_bars, load_meta
from research_engine.phase2_mt5.hashes import code_hash, sha256_bytes, sha256_files
from research_engine.phase2_mt5.labels import summarize
from research_engine.phase2_mt5.ledger import write_once
from research_engine.phase2_mt5.metrics import from_returns
from research_engine.phase2_mt5.paths import LIVE_HIST, RES, ensure

FIRST_PRED = 300
REFIT = 250
EMBARGO = 21
HOLD = 20
FEATURES = ("R20", "VOL20", "DIST_SMA50", "RSI14", "ATR_PCT")


def _force() -> bool:
    return os.environ.get("TRADEMIND_PHASE2_FORCE") == "1"


def _slice_i(dates: List[str], end: str) -> int:
    last = -1
    for i, d in enumerate(dates):
        if d[:10] <= end:
            last = i
    return last


def _features(bar: Dict[str, np.ndarray]) -> np.ndarray:
    c, h, l = bar["close"], bar["high"], bar["low"]
    n = len(c)
    r1 = np.full(n, np.nan)
    r1[1:] = c[1:] / c[:-1] - 1.0
    r20 = np.full(n, np.nan)
    r20[20:] = c[20:] / c[:-20] - 1.0
    vol20 = np.array([np.nanstd(r1[max(0, i - 19):i + 1]) if i >= 19 else np.nan for i in range(n)])
    sma50 = _sma(c, 50)
    atr = _atr(h, l, c, 14)
    rsi = _rsi(c, 14)
    pack = np.column_stack([
        r20,
        vol20,
        c / np.maximum(1e-12, sma50) - 1.0,
        rsi,
        atr / np.maximum(1e-12, c),
    ]).astype(np.float64)
    return pack


def _ols_fit(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    a = np.column_stack([np.ones(len(x)), x])
    try:
        coef, *_ = np.linalg.lstsq(a, y, rcond=None)
    except np.linalg.LinAlgError:
        coef = np.zeros(a.shape[1])
    return coef


def _ols_pred(coef: np.ndarray, xrow: np.ndarray) -> float:
    return float(coef[0] + np.dot(coef[1:], xrow))


def walk_linear(x: np.ndarray, y: np.ndarray, last_fit_i: int) -> np.ndarray:
    """Walk-forward OLS. Fits only use rows < t-embargo and dates already inside last_fit_i."""
    n = x.shape[0]
    scores = np.full(n, np.nan)
    t = FIRST_PRED
    while t < n and t <= last_fit_i:
        cutoff = t - EMBARGO
        if cutoff < 80:
            t += 1
            continue
        ok = np.all(np.isfinite(x[:cutoff]), axis=1) & np.isfinite(y[:cutoff])
        if int(ok.sum()) < 80:
            t += 1
            continue
        coef = _ols_fit(x[:cutoff][ok], np.clip(y[:cutoff][ok], -0.5, 0.5))
        end = min(n, t + REFIT, last_fit_i + 1)
        for u in range(t, end):
            if np.all(np.isfinite(x[u])):
                scores[u] = _ols_pred(coef, x[u])
        t = end
    return scores


def _threshold_sides(score: np.ndarray, thr: float = FLAT_THRESHOLD) -> np.ndarray:
    out = np.zeros(len(score))
    out[score > thr] = 1.0
    out[score < -thr] = -1.0
    out[~np.isfinite(score)] = 0.0
    return out


def run_exp001_ladder(out_dir: Optional[Path] = None) -> Dict[str, Any]:
    ensure()
    dest = out_dir or (RES / "exp001_ladder")
    dest.mkdir(parents=True, exist_ok=True)
    read_path = dest / "READ.json"
    if read_path.is_file() and not _force():
        return json.loads(read_path.read_text(encoding="utf-8"))

    bar = load_bars("D1")
    meta = load_meta()
    dates = bar["dates"]
    end_i = _slice_i(dates, RESEARCH_END)
    o = bar["open"]
    y = np.full(len(o), np.nan)
    y[: -(HOLD + 1)] = o[HOLD + 1:] / o[1:-HOLD] - 1.0
    x = _features(bar)
    naive_score = np.full(len(o), np.nan)
    naive_score[20:] = bar["close"][20:] / bar["close"][:-20] - 1.0
    naive_sides = _threshold_sides(naive_score)
    linear_scores = walk_linear(x, y, end_i)
    linear_sides = _threshold_sides(linear_scores)

    start_i = FIRST_PRED
    n_res = end_i - start_i + 1
    val_cut = start_i + int(0.70 * n_res)

    def pack(name: str, sides: np.ndarray) -> Dict[str, Any]:
        trades, nets = book_sides(bar, meta, sides, HOLD, start_i, end_i, "base")
        res_tr = [t for t in trades if t["signal"][:10] <= dates[val_cut][:10]]
        oos_tr = [t for t in trades if t["signal"][:10] > dates[val_cut][:10]]
        return {
            "research": from_returns(nets, HOLD, 252.0),
            "research_70": from_returns([t["net"] for t in res_tr], HOLD, 252.0),
            "research_30": from_returns([t["net"] for t in oos_tr], HOLD, 252.0),
            "economic": summarize(trades, 0.0020),
            "n_trades": len(trades),
            "n_flat": int(np.sum(sides[start_i:end_i + 1] == 0)),
            "threshold": FLAT_THRESHOLD,
        }, trades

    naive_rep, naive_tr = pack("NAIVE", naive_sides)
    lin_rep, lin_tr = pack("LINEAR", linear_sides)

    oos_n = naive_rep["research_30"].get("total_return")
    oos_l = lin_rep["research_30"].get("total_return")
    t_n = naive_rep["research_30"].get("t") or 0.0
    t_l = lin_rep["research_30"].get("t") or 0.0
    incremental = (
        oos_l is not None and oos_n is not None
        and oos_l > oos_n
        and (t_l - t_n) > 0
    )
    stop = not incremental
    verdict = "NO_INCREMENTAL_OOS_STOP" if stop else "LINEAR_INCREMENT_RESEARCH30_ONLY"
    report = {
        "experiment_id": "EXP-001",
        "profile": "PHASE2_EXP001_LADDER",
        "candidate": False,
        "order_send": False,
        "writes_9000": False,
        "final_oos_evaluated": False,
        "final_oos_start": FINAL_OOS_START,
        "research_end": RESEARCH_END,
        "threshold_preregistered": FLAT_THRESHOLD,
        "features": list(FEATURES),
        "walk_forward": {"first_pred": FIRST_PRED, "refit": REFIT, "embargo": EMBARGO, "seed": SEED},
        "naive": naive_rep,
        "linear": lin_rep,
        "incremental_vs_naive_research30": incremental,
        "delta_twr_research30": None if oos_l is None or oos_n is None else float(oos_l - oos_n),
        "next_layer": "NONE" if stop else "LOGISTIC_NOT_THIS_SESSION",
        "verdict": verdict,
        "contract": "docs/research_engine/EXP001_GOLD_D1_OWNPRICE_CONTRACT.md",
        "data_hash": sha256_files([LIVE_HIST / "GOLD_D1.csv", LIVE_HIST / "GOLD_META.json"]),
        "code_hash": code_hash(),
        "note": "Stopped before Logistic/Ridge/LightGBM. FINAL OOS not opened. Not a Candidate.",
    }
    body = json.dumps(report, ensure_ascii=False, indent=2)
    report["result_hash"] = sha256_bytes(body.encode("utf-8"))
    write_once(report, read_path)
    (dest / "NAIVE_trades.json").write_text(json.dumps(naive_tr, ensure_ascii=False), encoding="utf-8")
    (dest / "LINEAR_trades.json").write_text(json.dumps(lin_tr, ensure_ascii=False), encoding="utf-8")
    return report


if __name__ == "__main__":
    r = run_exp001_ladder()
    print(r.get("verdict"), r.get("delta_twr_research30"), r.get("next_layer"))
