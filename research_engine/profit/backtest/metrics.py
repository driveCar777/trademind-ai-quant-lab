"""Equity metrics. CAGR on short M15 samples is reported but weak."""
from __future__ import print_function

import math

from research_engine.profit import BARS_PER_YEAR
from research_engine.statistics import mean, stdev


def max_drawdown(curve):
    peak = None
    worst = 0.0
    for x in curve:
        if x is None:
            continue
        if peak is None or x > peak:
            peak = x
        if peak and peak > 0:
            dd = (x - peak) / peak
            if dd < worst:
                worst = dd
    return worst


def bar_returns(curve):
    out = []
    i = 1
    while i < len(curve):
        a = curve[i - 1]
        b = curve[i]
        if a and a != 0 and b is not None:
            out.append(b / float(a) - 1.0)
        i += 1
    return out


def summarize_equity(curve, timeframe, start_equity, trades):
    bpy = BARS_PER_YEAR.get(timeframe) or 252
    n = len(curve)
    end = curve[-1] if curve else start_equity
    total = None
    if start_equity and start_equity > 0 and end is not None:
        total = end / float(start_equity) - 1.0
    cagr = None
    if total is not None and n > 1 and (1.0 + total) > 0:
        cagr = (1.0 + total) ** (bpy / float(n - 1)) - 1.0
    elif total is not None and (1.0 + total) <= 0:
        cagr = -1.0
    rets = bar_returns(curve)
    s = stdev(rets)
    m = mean(rets)
    sharpe = None
    if s and s > 0 and m is not None:
        sharpe = (m / s) * math.sqrt(bpy)
    pnls = [tr.get("pnl") for tr in trades if tr.get("pnl") is not None]
    abs_sum = 0.0
    max_abs = 0.0
    for p in pnls:
        ap = abs(p)
        abs_sum += ap
        if ap > max_abs:
            max_abs = ap
    dominance = None if abs_sum == 0 else max_abs / abs_sum
    turnover = 0.0
    for tr in trades:
        turnover += abs(tr.get("notional") or 0.0)
    if start_equity:
        turnover = turnover / float(start_equity)
    wins = 0
    for p in pnls:
        if p > 0:
            wins += 1
    return {
        "n_bars": n,
        "start_equity": start_equity,
        "end_equity": end,
        "total_return": total,
        "cagr": cagr,
        "max_drawdown": max_drawdown(curve),
        "sharpe": sharpe,
        "trade_count": len(trades),
        "win_count": wins,
        "turnover": turnover,
        "max_trade_share": dominance,
        "bars_per_year": bpy,
        "timeframe": timeframe,
    }
