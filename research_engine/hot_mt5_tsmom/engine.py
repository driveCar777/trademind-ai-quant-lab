"""Per-product 12-month TSMOM. No LightGBM. Hold 20. Same cost as V1."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import numpy as np

from research_engine.hot_mt5_cost_aware.engine import (
    CASH,
    LONG,
    MIN_COVERAGE,
    MIN_VAL_TRADES,
    SHORT,
    _meta,
    _summ,
    book,
)
from research_engine.hot_mt5_products.features import load_d1
from research_engine.hot_mt5_products.products import PRODUCTS, SPECIAL, VAL_FRAC
from research_engine.hot_mt5_tsmom.paths import HIST, RES

LOOKBACK = 252
HOLD = 20
PROFILE = "HOT_MT5_TSMOM12_V4"


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES


def mom_pred(close: np.ndarray) -> np.ndarray:
    n = len(close)
    pred = np.full(n, float(CASH))
    for t in range(LOOKBACK, n):
        a, b = close[t - LOOKBACK], close[t]
        if not np.isfinite(a) or not np.isfinite(b) or a <= 0:
            continue
        m = b / a - 1.0
        if m > 0:
            pred[t] = LONG
        elif m < 0:
            pred[t] = SHORT
        else:
            pred[t] = CASH
    return pred


def run_product(pid: str) -> Dict[str, Any]:
    print("V4 TSMOM", pid, flush=True)
    ensure()
    spec = PRODUCTS[pid]
    path = HIST / ("%s_D1.csv" % pid)
    if not path.is_file():
        return {"id": pid, "ok": False, "error": "NO_D1"}
    bar = load_d1(path)
    pred = mom_pred(bar["close"])
    meta = _meta(pid)
    n = len(bar["dates"])
    first = LOOKBACK
    val_i = int(first + (1.0 - VAL_FRAC) * (n - first))
    long_s, long_tr, _ = book(bar, meta, pred, HOLD, first, n)
    res_s, _, _ = book(bar, meta, pred, HOLD, first, val_i - 1)
    val_s, _, _ = book(bar, meta, pred, HOLD, val_i, n)
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
        "lookback": LOOKBACK, "hold": HOLD, "no_ml": True, "not_sma200": True,
        "shell": "TSMOM12", "n_bars": n, "first": bar["dates"][0], "last": bar["dates"][-1],
        "broker_meta": {k: meta.get(k) for k in ("broker", "swap_mode", "swap_long", "swap_short", "point", "bid")},
        "long_sample": long_s, "research_70": res_s, "validation_30": val_s,
        "year_by_year": year_tab, "special_diagnostic": special,
        "viable_historical": viable, "coverage_fail": cover_fail, "deny": deny, "verdict": verdict,
        "strategy": {
            "deploy": bool(viable),
            "rule": "收盘/252日前收盘的符号，下一开盘，持有 20 根。无树。不是均线。",
            "do_not": "不要改 252/20；不要加 SMA；不要和 A 股对冲。",
        },
        "n_trades_long": len(long_tr),
        "note": "教科书 TSMOM。不是 Candidate。",
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
        "no_ml": True,
        "n_ok": sum(1 for r in items if r.get("ok")),
        "n_viable": sum(1 for r in items if r.get("viable_historical")),
        "items": items,
        "note": "12-month sign, hold 20. Not Candidate.",
    }
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
