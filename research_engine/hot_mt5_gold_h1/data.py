"""H1 bars keep the hour. D1 loader slices to calendar day and cannot be reused."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from research_engine.hot_mt5_products.features import _atr, _rsi, _sma


def load_h1(path: Path) -> Dict[str, np.ndarray]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        raise ValueError("empty H1 %s" % path)
    ts = [r["timestamp_utc"] for r in rows]

    def col(name):
        return np.array([float(r[name]) for r in rows], dtype=np.float64)

    return {
        "ts": ts,
        "dates": [t[:10] for t in ts],
        "open": col("open"),
        "high": col("high"),
        "low": col("low"),
        "close": col("close"),
        "spread": np.array([float(r.get("spread") or 0) for r in rows], dtype=np.float64),
        "hour": np.array([int(t[11:13]) for t in ts], dtype=np.float64),
    }


def build_h1_matrix(bar: Dict[str, np.ndarray]) -> Tuple[List[str], np.ndarray]:
    names = ["R1", "R5", "R20", "VOL20", "VOL60", "ATR14", "DIST_SMA50", "DIST_SMA200",
             "RSI14", "GAP", "RANGE_ATR", "DOW", "MONTH", "HOUR"]
    c, o, h, l = bar["close"], bar["open"], bar["high"], bar["low"]
    n = len(c)
    r1 = np.full(n, np.nan)
    r1[1:] = c[1:] / c[:-1] - 1.0
    r5 = np.full(n, np.nan)
    r5[5:] = c[5:] / c[:-5] - 1.0
    r20 = np.full(n, np.nan)
    r20[20:] = c[20:] / c[:-20] - 1.0
    vol20 = np.array([np.nanstd(r1[max(0, i - 19):i + 1]) if i >= 19 else np.nan for i in range(n)])
    vol60 = np.array([np.nanstd(r1[max(0, i - 59):i + 1]) if i >= 59 else np.nan for i in range(n)])
    atr = _atr(h, l, c, 14)
    sma50, sma200 = _sma(c, 50), _sma(c, 200)
    gap = np.full(n, np.nan)
    gap[1:] = o[1:] / c[:-1] - 1.0
    rng = (h - l) / np.maximum(1e-12, atr)
    import datetime as dt
    dow = np.array([dt.date.fromisoformat(d).weekday() for d in bar["dates"]], dtype=np.float64)
    month = np.array([int(d[5:7]) for d in bar["dates"]], dtype=np.float64)
    pack = {
        "R1": r1, "R5": r5, "R20": r20, "VOL20": vol20, "VOL60": vol60,
        "ATR14": atr / np.maximum(1e-12, c),
        "DIST_SMA50": c / np.maximum(1e-12, sma50) - 1.0,
        "DIST_SMA200": c / np.maximum(1e-12, sma200) - 1.0,
        "RSI14": _rsi(c, 14), "GAP": gap, "RANGE_ATR": rng,
        "DOW": dow, "MONTH": month, "HOUR": bar["hour"],
    }
    x = np.column_stack([pack[k] for k in names]).astype(np.float64)
    return names, x
