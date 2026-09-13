"""H1-native own-price features + the same 24h sign(score) shell as V1 ML."""
from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np

from research_engine.hot_mt5_gold_h1.data import load_h1
from research_engine.hot_mt5_gold_h1 import engine as v1eng
from research_engine.hot_mt5_gold_h1.engine import HOLD, _meta, _window_reports, walk_scores
from research_engine.hot_mt5_gold_h1_v5.paths import HIST, RES
from research_engine.hot_mt5_products.features import _atr, _rsi, _sma

PROFILE = "HOT_MT5_GOLD_H1_V5_NATIVE"
NATIVE = [
    "R1", "R6", "R24", "VOL24", "VOL120", "ATR14",
    "DIST_SMA24", "DIST_SMA120", "RSI14", "RANGE_ATR",
    "HOUR_SIN", "HOUR_COS", "DOW",
]


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES


def build_native(bar: Dict[str, np.ndarray]) -> Tuple[List[str], np.ndarray]:
    c, o, h, l = bar["close"], bar["open"], bar["high"], bar["low"]
    n = len(c)
    r1 = np.full(n, np.nan)
    r1[1:] = c[1:] / c[:-1] - 1.0
    r6 = np.full(n, np.nan)
    r6[6:] = c[6:] / c[:-6] - 1.0
    r24 = np.full(n, np.nan)
    r24[24:] = c[24:] / c[:-24] - 1.0
    vol24 = np.array([np.nanstd(r1[max(0, i - 23):i + 1]) if i >= 23 else np.nan for i in range(n)])
    vol120 = np.array([np.nanstd(r1[max(0, i - 119):i + 1]) if i >= 119 else np.nan for i in range(n)])
    atr = _atr(h, l, c, 14)
    sma24, sma120 = _sma(c, 24), _sma(c, 120)
    hour = bar["hour"]
    ang = 2.0 * math.pi * hour / 24.0
    import datetime as dt
    dow = np.array([dt.date.fromisoformat(d).weekday() for d in bar["dates"]], dtype=np.float64)
    pack = {
        "R1": r1, "R6": r6, "R24": r24, "VOL24": vol24, "VOL120": vol120,
        "ATR14": atr / np.maximum(1e-12, c),
        "DIST_SMA24": c / np.maximum(1e-12, sma24) - 1.0,
        "DIST_SMA120": c / np.maximum(1e-12, sma120) - 1.0,
        "RSI14": _rsi(c, 14),
        "RANGE_ATR": (h - l) / np.maximum(1e-12, atr),
        "HOUR_SIN": np.sin(ang), "HOUR_COS": np.cos(ang), "DOW": dow,
    }
    x = np.column_stack([pack[k] for k in NATIVE]).astype(np.float64)
    return list(NATIVE), x


def run():
    print("GOLD H1 V5 native", flush=True)
    ensure()
    path = HIST / "GOLD_H1.csv"
    if not path.is_file():
        return {"ok": False, "error": "NO_H1"}
    bar = load_h1(path)
    names, x = build_native(bar)
    o = bar["open"]
    n = len(o)
    y = np.full(n, np.nan)
    y[: -(HOLD + 1)] = o[HOLD + 1:] / o[1:-HOLD] - 1.0
    scores, refits = walk_scores(x, y, names)

    def ml_side(t):
        s = scores[t]
        if not np.isfinite(s):
            return 0
        return 1 if s > 0 else -1

    meta = _meta()
    first = v1eng.FIRST_PRED
    val_i = int(first + (1.0 - v1eng.VAL_FRAC) * (n - first))
    ml = _window_reports(bar, meta, ml_side, first, val_i, n)
    tr = ml.pop("trades")
    summary = {
        "profile": PROFILE, "ok": True, "candidate": False, "level1": False, "promise": False,
        "writes_9000": False, "us_shares": False, "timeframe": "H1", "hold": HOLD,
        "n_bars": n, "first": bar["ts"][0], "last": bar["ts"][-1],
        "n_refits": len(refits), "features": names,
        "books": {
            "H1_NATIVE": {**ml, "rule": "小时钟 13 列 LightGBM + sign(score)，持有 24 根"},
        },
        "n_viable": int(ml["viable_historical"]),
        "note": "只测特征时钟。不是 Candidate。",
    }
    import json
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / "NATIVE_trades.json").write_text(json.dumps(tr, ensure_ascii=False), encoding="utf-8")
    return summary
