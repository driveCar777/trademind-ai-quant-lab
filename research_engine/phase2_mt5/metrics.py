"""Unified Phase 2 metrics. Monthly DISTRIBUTION, not just the mean."""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def _safe_t(x: np.ndarray) -> Optional[float]:
    if len(x) < 3:
        return None
    sd = float(x.std(ddof=1))
    if sd <= 0:
        return None
    return float(x.mean() / (sd / np.sqrt(len(x))))


def from_returns(rets: List[float], hold: int, bars_per_year: float) -> Dict[str, Any]:
    x = np.array(rets, dtype=np.float64)
    if len(x) == 0:
        return {
            "n": 0, "total_return": None, "cagr": None, "mean": None, "t": None,
            "hit": None, "maxdd": None, "sharpe": None, "sortino": None, "calmar": None,
            "profit_factor": None, "expectancy": None, "payoff": None,
        }
    eq = np.cumprod(1.0 + x)
    yrs = max(1e-9, len(x) * hold / float(bars_per_year))
    peak = np.maximum.accumulate(eq)
    dd = float(np.min(eq / peak - 1.0))
    total = float(eq[-1] - 1.0)
    cagr = float(eq[-1] ** (1.0 / yrs) - 1.0)
    mu = float(x.mean())
    sd = float(x.std(ddof=1)) if len(x) > 1 else 0.0
    periods_year = float(bars_per_year) / max(1, hold)
    sharpe = float(mu / sd * np.sqrt(periods_year)) if sd > 0 else None
    downside = x[x < 0]
    dsd = float(downside.std(ddof=1)) if len(downside) > 1 else 0.0
    sortino = float(mu / dsd * np.sqrt(periods_year)) if dsd > 0 else None
    calmar = float(cagr / abs(dd)) if dd < 0 else None
    wins = x[x > 0]
    loss = x[x < 0]
    pf = float(wins.sum() / abs(loss.sum())) if len(loss) and abs(loss.sum()) > 0 else None
    payoff = float(wins.mean() / abs(loss.mean())) if len(wins) and len(loss) and abs(loss.mean()) > 0 else None
    return {
        "n": int(len(x)),
        "total_return": total,
        "cagr": cagr,
        "mean": mu,
        "t": _safe_t(x),
        "hit": float((x > 0).mean()),
        "maxdd": dd,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "profit_factor": pf,
        "expectancy": mu,
        "payoff": payoff,
    }


def monthly_from_equity(dates: List[str], equity: np.ndarray) -> Dict[str, Any]:
    """Month-end equity ratios. Reports the DISTRIBUTION, not only the mean."""
    by: Dict[str, Tuple[str, float]] = {}
    for i, day in enumerate(dates):
        if i >= len(equity):
            break
        key = day[:7]
        by[key] = (day, float(equity[i]))
    keys = sorted(by)
    rets = []
    labels = []
    prev = None
    for key in keys:
        val = by[key][1]
        if prev is not None and prev > 0:
            rets.append(val / prev - 1.0)
            labels.append(key)
        prev = val
    arr = np.array(rets, dtype=np.float64)
    if len(arr) == 0:
        return {"n": 0, "returns": [], "months": [], "median": None, "mean": None,
                "worst": None, "best": None, "p10": None, "p90": None,
                "frac_ge_20pct": None, "frac_ge_10pct": None}
    return {
        "n": int(len(arr)),
        "returns": [float(v) for v in arr],
        "months": labels,
        "median": float(np.median(arr)),
        "mean": float(arr.mean()),
        "worst": float(arr.min()),
        "best": float(arr.max()),
        "p10": float(np.percentile(arr, 10)),
        "p90": float(np.percentile(arr, 90)),
        "frac_ge_20pct": float((arr >= 0.20).mean()),
        "frac_ge_10pct": float((arr >= 0.10).mean()),
    }


def path_mfe_mae(
    high: np.ndarray,
    low: np.ndarray,
    entry: float,
    t_in: int,
    t_out: int,
    side: int,
) -> Dict[str, float]:
    if entry <= 0 or t_out <= t_in:
        return {"mfe": float("nan"), "mae": float("nan"), "max_dd_during_trade": float("nan")}
    hs = high[t_in:t_out]
    ls = low[t_in:t_out]
    if side > 0:
        mfe = float(np.max(hs) / entry - 1.0)
        mae = float(np.min(ls) / entry - 1.0)
    else:
        mfe = float(1.0 - np.min(ls) / entry)
        mae = float(1.0 - np.max(hs) / entry)
    # running close-less path DD vs peak favorable
    if side > 0:
        px = hs  # optimistic; use lows for DD
        eq = ls / entry
    else:
        eq = 2.0 - hs / entry
    peak = np.maximum.accumulate(eq)
    dd = float(np.min(eq / np.maximum(peak, 1e-12) - 1.0))
    return {"mfe": mfe, "mae": mae, "max_dd_during_trade": dd}


def year_of(day: str) -> int:
    return dt.date.fromisoformat(day[:10]).year
