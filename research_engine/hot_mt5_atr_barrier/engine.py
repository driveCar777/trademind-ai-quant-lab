"""Walk-forward 3-class. Hurdle = 1.0 * ATR14/close * sqrt(hold). Not 2x cost, not 20bp."""
from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional

import numpy as np

from research_engine.hot_mt5_atr_barrier.paths import HIST, RES
from research_engine.hot_mt5_cost_aware.engine import (
    CASH,
    LGBM_CLF,
    LONG,
    MIN_COVERAGE,
    MIN_VAL_TRADES,
    SHORT,
    _meta,
    _summ,
    book,
    walk_classes,
)
from research_engine.hot_mt5_products.features import _atr, build_matrix, load_d1
from research_engine.hot_mt5_products.products import FIRST_PRED_BARS, PRODUCTS, SPECIAL, VAL_FRAC

ATR_K = 1.0
PROFILE = "HOT_MT5_ATR_BARRIER_V3"


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES


def atr_frac(bar) -> np.ndarray:
    a = _atr(bar["high"], bar["low"], bar["close"], 14)
    return a / np.maximum(1e-12, bar["close"])


def make_labels(y_raw: np.ndarray, atr_f: np.ndarray, hold: int) -> np.ndarray:
    scale = ATR_K * math.sqrt(float(hold))
    lab = np.full(len(y_raw), np.nan)
    for i, y in enumerate(y_raw):
        if not np.isfinite(y) or not np.isfinite(atr_f[i]):
            continue
        h = float(atr_f[i]) * scale
        if y > h:
            lab[i] = LONG
        elif y < -h:
            lab[i] = SHORT
        else:
            lab[i] = CASH
    return lab


def run_product(pid: str) -> Dict[str, Any]:
    print("V3 train", pid, flush=True)
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
    # _meta reads V2 HIST unless we point cost-aware HIST at the same folder (it is).
    af = atr_frac(bar)
    y = make_labels(y_raw, af, hold)
    pred, refits = walk_classes(x, y, hold, names)
    n = len(bar["dates"])
    first = FIRST_PRED_BARS
    val_i = int(first + (1.0 - VAL_FRAC) * (n - first))
    long_s, long_tr, _ = book(bar, meta, pred, hold, first, n)
    res_s, _, _ = book(bar, meta, pred, hold, first, val_i - 1)
    val_s, _, _ = book(bar, meta, pred, hold, val_i, n)
    years = {}
    for tr in long_tr:
        years.setdefault(tr["signal"][:4], []).append(tr["net"])
    year_tab = {k: _summ(v, hold) for k, v in sorted(years.items())}
    special = {}
    for tag, a, b in SPECIAL:
        from research_engine.hot_mt5_cost_aware.engine import _slice_summ
        special[tag] = _slice_summ(long_tr, hold, a, min(b, bar["dates"][-1]))
    n_lab = int(np.isfinite(y).sum())
    lab_share = {
        "cash": float(np.nansum(y == CASH) / max(1, n_lab)),
        "long": float(np.nansum(y == LONG) / max(1, n_lab)),
        "short": float(np.nansum(y == SHORT) / max(1, n_lab)),
    }
    finite_h = af[np.isfinite(af)] * math.sqrt(float(hold))
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
        "atr_k": ATR_K, "hurdle_not_20bp": True, "hurdle_not_v2_lambda": True,
        "median_hurdle": float(np.median(finite_h)) if len(finite_h) else None,
        "label_share": lab_share,
        "broker_meta": {k: meta.get(k) for k in ("broker", "swap_mode", "swap_long", "swap_short", "point", "bid")},
        "shell": "ATR_BARRIER_3WAY", "hold": hold, "features": names,
        "lgbm": LGBM_CLF, "n_bars": n, "first": bar["dates"][0], "last": bar["dates"][-1],
        "n_refits": len(refits),
        "long_sample": long_s, "research_70": res_s, "validation_30": val_s,
        "year_by_year": year_tab, "special_diagnostic": special,
        "viable_historical": viable, "coverage_fail": cover_fail, "deny": deny, "verdict": verdict,
        "strategy": {
            "deploy": bool(viable),
            "rule": "三分类 argmax。门槛=1×ATR14/close×√hold。CASH 次日再看。不是 2×成本，不是 20bp。",
            "do_not": "不要改 k/特征/hold；不要和 A 股对冲。",
        },
        "n_trades_long": len(long_tr),
        "note": "波动门槛。覆盖过低直接否。不是 Candidate。",
    }
    (RES / ("%s.json" % pid)).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / ("%s_trades.json" % pid)).write_text(json.dumps(long_tr, ensure_ascii=False), encoding="utf-8")
    return report


def run_all(ids: Optional[List[str]] = None) -> Dict[str, Any]:
    ensure()
    ids = ids or list(PRODUCTS)
    items = [run_product(pid) for pid in ids]
    summary = {
        "profile": PROFILE,
        "candidate": False,
        "writes_9000": False,
        "us_shares": False,
        "atr_k": ATR_K,
        "n_ok": sum(1 for r in items if r.get("ok")),
        "n_viable": sum(1 for r in items if r.get("viable_historical")),
        "items": items,
        "note": "ATR×√hold 三分类。不是 V2 补丁。不是 Candidate。",
    }
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
