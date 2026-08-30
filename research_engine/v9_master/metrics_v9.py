"""V9 metrics on top of V0.6 equity summary. Not a new strategy."""
from __future__ import print_function

import math

from research_engine.profit import BARS_PER_YEAR, START_EQUITY
from research_engine.profit.backtest.metrics import bar_returns, max_drawdown, summarize_equity
from research_engine.statistics import mean, stdev


def sortino(rets, bpy):
    if not rets:
        return None
    m = mean(rets)
    downside = [r for r in rets if r is not None and r < 0]
    if not downside:
        return None if m is None or m <= 0 else float("inf")
    d = stdev(downside)
    if not d or d <= 0 or m is None:
        return None
    return (m / d) * math.sqrt(bpy)


def calmar(cagr, max_dd):
    if cagr is None or max_dd is None or max_dd == 0:
        return None
    return cagr / abs(float(max_dd))


def profit_factor(trades):
    gains = 0.0
    losses = 0.0
    for tr in trades or []:
        p = tr.get("net_pnl")
        if p is None:
            p = tr.get("pnl")
        if p is None:
            continue
        if p > 0:
            gains += p
        elif p < 0:
            losses += abs(p)
    if losses == 0:
        return None if gains == 0 else float("inf")
    return gains / losses


def drawdown_duration(curve):
    peak = None
    peak_i = 0
    worst_len = 0
    worst_start = None
    worst_end = None
    i = 0
    under_start = None
    while i < len(curve):
        x = curve[i]
        if x is None:
            i += 1
            continue
        if peak is None or x >= peak:
            if under_start is not None:
                length = i - under_start
                if length > worst_len:
                    worst_len = length
                    worst_start = under_start
                    worst_end = i
                under_start = None
            peak = x
            peak_i = i
        elif peak and x < peak:
            if under_start is None:
                under_start = peak_i
        i += 1
    if under_start is not None:
        length = len(curve) - under_start
        if length > worst_len:
            worst_len = length
            worst_start = under_start
            worst_end = len(curve) - 1
    return {
        "max_dd_bars": worst_len,
        "max_dd_start_index": worst_start,
        "max_dd_end_index": worst_end,
    }


def yearly_equity(curve, bars):
    by_year = {}
    i = 0
    n = min(len(curve), len(bars or []))
    while i < n:
        ts = (bars[i] or {}).get("timestamp_utc") or (bars[i] or {}).get("date") or ""
        year = str(ts)[:4]
        if len(year) == 4 and year.isdigit():
            row = by_year.get(year)
            if row is None:
                row = {"year": year, "start": curve[i], "end": curve[i], "n": 0}
                by_year[year] = row
            row["end"] = curve[i]
            row["n"] += 1
        i += 1
    out = []
    for year in sorted(by_year.keys()):
        row = by_year[year]
        start = row["start"]
        end = row["end"]
        ret = None
        if start and start != 0 and end is not None:
            ret = end / float(start) - 1.0
        out.append({"year": year, "n_bars": row["n"], "return": ret})
    return out


def economic_status(research, validation):
    r = research or {}
    v = validation or {}
    r_tr = r.get("net_return")
    if r_tr is None:
        r_tr = r.get("total_return")
    v_tr = v.get("net_return")
    if v_tr is None:
        v_tr = v.get("total_return")
    r_n = r.get("trade_count") or 0
    v_n = v.get("trade_count") or 0
    both_pos = r_tr is not None and r_tr > 0 and v_tr is not None and v_tr > 0
    any_pos = (r_tr is not None and r_tr > 0) or (v_tr is not None and v_tr > 0)
    if both_pos and r_n >= 8 and v_n >= 4:
        return "POSITIVE_REPRODUCIBLE"
    if any_pos:
        return "POSITIVE_BUT_WEAK"
    if r_tr is not None and abs(r_tr) < 0.005 and (v_tr is None or abs(v_tr) < 0.005):
        return "BREAK_EVEN"
    return "LOSS"


def extend_metrics(curve, timeframe, start_equity, trades, bars=None):
    base = summarize_equity(curve, timeframe, start_equity, trades)
    bpy = base.get("bars_per_year") or BARS_PER_YEAR.get(timeframe) or 252
    rets = bar_returns(curve)
    pnls = []
    holds = []
    for tr in trades or []:
        p = tr.get("net_pnl")
        if p is None:
            p = tr.get("pnl")
        if p is not None:
            pnls.append(p)
        hold = tr.get("holding_bars")
        if hold is None:
            ei = tr.get("entry_index")
            xi = tr.get("exit_index")
            if ei is not None and xi is not None:
                hold = xi - ei
        if hold is not None:
            holds.append(hold)
    wins = 0
    for p in pnls:
        if p > 0:
            wins += 1
    win_rate = None if not pnls else wins / float(len(pnls))
    avg_hold = None if not holds else sum(holds) / float(len(holds))
    spread = 0.0
    comm = 0.0
    slip = 0.0
    for tr in trades or []:
        spread += float(tr.get("spread_cost") or 0.0)
        comm += float(tr.get("commission") or 0.0)
        slip += float(tr.get("slippage") or 0.0)
    dd = drawdown_duration(curve)
    out = dict(base)
    out["net_return"] = base.get("total_return")
    out["gross_return"] = None
    if start_equity and start_equity > 0:
        cost = spread + comm + slip
        end = base.get("end_equity")
        if end is not None:
            out["gross_return"] = (end + cost) / float(start_equity) - 1.0
    out["sortino"] = sortino(rets, bpy)
    out["calmar"] = calmar(base.get("cagr"), base.get("max_drawdown"))
    out["profit_factor"] = profit_factor(trades)
    out["win_rate"] = win_rate
    out["average_holding"] = avg_hold
    out["spread_cost"] = spread
    out["commission"] = comm
    out["slippage"] = slip
    out["cost_contribution"] = spread + comm + slip
    out["max_dd_bars"] = dd["max_dd_bars"]
    out["yearly"] = yearly_equity(curve, bars) if bars else []
    if out.get("sortino") == float("inf"):
        out["sortino"] = None
        out["sortino_unbounded"] = True
    if out.get("profit_factor") == float("inf"):
        out["profit_factor"] = None
        out["profit_factor_unbounded"] = True
    return out
