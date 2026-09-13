"""Own-price features only. No other symbol leaks into another product."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from research_engine.hot_mt5_products.products import PRODUCTS


def load_d1(path: Path) -> Dict[str, np.ndarray]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        raise ValueError("empty history %s" % path)
    dates = [r["timestamp_utc"][:10] for r in rows]
    def col(name):
        return np.array([float(r[name]) for r in rows], dtype=np.float64)
    spread = np.array([float(r.get("spread") or 0) for r in rows], dtype=np.float64)
    return {
        "dates": dates,
        "open": col("open"),
        "high": col("high"),
        "low": col("low"),
        "close": col("close"),
        "spread": spread,
    }


def _sma(x: np.ndarray, w: int) -> np.ndarray:
    out = np.full_like(x, np.nan)
    c = np.cumsum(np.nan_to_num(x))
    for i in range(w - 1, len(x)):
        out[i] = (c[i] - (c[i - w] if i >= w else 0.0)) / w
    return out


def _rsi(close: np.ndarray, w: int = 14) -> np.ndarray:
    out = np.full_like(close, np.nan)
    d = np.diff(close, prepend=close[0])
    up, dn = np.clip(d, 0, None), np.clip(-d, 0, None)
    au, ad = _sma(up, w), _sma(dn, w)
    rs = au / np.maximum(1e-12, ad)
    out = 100.0 - 100.0 / (1.0 + rs)
    out[:w] = np.nan
    return out


def _atr(h, l, c, w: int = 14) -> np.ndarray:
    prev = np.roll(c, 1)
    prev[0] = c[0]
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev), np.abs(l - prev)))
    return _sma(tr, w)


def build_matrix(pid: str, bar: Dict[str, np.ndarray]) -> Tuple[List[str], np.ndarray]:
    names = list(PRODUCTS[pid]["features"])
    c, o, h, l = bar["close"], bar["open"], bar["high"], bar["low"]
    n = len(c)
    ret = np.full(n, np.nan)
    ret[1:] = c[1:] / c[:-1] - 1.0
    vol20 = np.array([np.nanstd(ret[max(0, i - 19):i + 1]) if i >= 19 else np.nan for i in range(n)])
    vol60 = np.array([np.nanstd(ret[max(0, i - 59):i + 1]) if i >= 59 else np.nan for i in range(n)])
    atr = _atr(h, l, c, 14)
    sma50, sma200 = _sma(c, 50), _sma(c, 200)
    gap = np.full(n, np.nan)
    gap[1:] = o[1:] / c[:-1] - 1.0
    rng = (h - l) / np.maximum(1e-12, atr)
    dow = np.array([__import__("datetime").date.fromisoformat(d).weekday() for d in bar["dates"]], dtype=np.float64)
    month = np.array([int(d[5:7]) for d in bar["dates"]], dtype=np.float64)
    r1 = np.full(n, np.nan)
    r1[1:] = c[1:] / c[:-1] - 1.0
    r5 = np.full(n, np.nan)
    r5[5:] = c[5:] / c[:-5] - 1.0
    r20 = np.full(n, np.nan)
    r20[20:] = c[20:] / c[:-20] - 1.0
    r60 = np.full(n, np.nan)
    r60[60:] = c[60:] / c[:-60] - 1.0
    pack = {
        "R1": r1, "R5": r5, "R20": r20, "R60": r60,
        "VOL20": vol20, "VOL60": vol60,
        "ATR14": atr / np.maximum(1e-12, c),
        "DIST_SMA50": c / np.maximum(1e-12, sma50) - 1.0,
        "DIST_SMA200": c / np.maximum(1e-12, sma200) - 1.0,
        "RSI14": _rsi(c, 14),
        "GAP": gap,
        "RANGE_ATR": rng,
        "DOW": dow,
        "MONTH": month,
        "REV5": -r5,
        "VOL_EXPAND": vol20 / np.maximum(1e-12, vol60),
    }
    x = np.column_stack([pack[k] for k in names]).astype(np.float64)
    return names, x
