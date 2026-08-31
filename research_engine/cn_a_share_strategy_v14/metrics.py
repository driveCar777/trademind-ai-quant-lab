"""Strategy economic and risk metrics. Not a selector."""
from __future__ import print_function

import math

import numpy as np

from research_engine.cn_a_share_strategy_v14 import HOLD_DAYS, RESEARCH, VALIDATION


def _eq_arr(curve):
    return np.array([r["equity"] for r in curve], dtype=np.float64)


def _daily_rets(curve):
    dates = [r["date"] for r in curve]
    eq = _eq_arr(curve)
    out = []
    for i in range(1, len(eq)):
        if eq[i - 1] > 0 and np.isfinite(eq[i]) and np.isfinite(eq[i - 1]):
            out.append((dates[i], float(eq[i] / eq[i - 1] - 1.0)))
    return out


def maxdd_path(curve):
    peak = -1e99
    dd = 0.0
    peak_date = None
    trough_date = None
    start = None
    rec = None
    last_peak = None
    worst = 0.0
    eq = 1.0
    for row in curve:
        eq = row["equity"]
        if eq > peak:
            peak = eq
            last_peak = row["date"]
            if dd < 0 and rec is None and peak_date and trough_date:
                rec = row["date"]
        if peak > 0:
            cur = eq / peak - 1.0
            if cur < worst:
                worst = cur
                peak_date = last_peak
                trough_date = row["date"]
                rec = None
            dd = min(dd, cur)
    return {
        "maxdd": dd,
        "peak_date": peak_date,
        "trough_date": trough_date,
        "recovery_date": rec,
    }


def cagr(start, end, n_days, year_days=242.0):
    if start <= 0 or end <= 0 or n_days <= 0:
        return None
    years = n_days / year_days
    return (end / start) ** (1.0 / years) - 1.0


def book_metrics(sim, window_name, start, end):
    trades = [tr for tr in sim["trades"] if start <= tr["signal_date"] <= end]
    curve = [r for r in sim["curve"] if start <= r["date"] <= end]
    if not curve:
        return {"window": window_name, "n_trades": 0}
    if curve[0]["date"] != start:
        curve = [{"date": start, "equity": curve[0]["equity"], "cash": curve[0].get("cash"), "invested": 0.0}] + curve
    s0 = float(curve[0]["equity"])
    s1 = float(curve[-1]["equity"])
    drets = [r for _, r in _daily_rets(curve)]
    xs = np.array(drets, dtype=np.float64) if drets else np.array([])
    vol = float(np.std(xs, ddof=1) * math.sqrt(242.0)) if xs.size > 2 else None
    down = xs[xs < 0] if xs.size else np.array([])
    dvol = float(np.std(down, ddof=1) * math.sqrt(242.0)) if down.size > 2 else None
    cg = cagr(s0, s1, max(1, len(curve) - 1))
    ddinfo = maxdd_path(curve)
    mdd = ddinfo["maxdd"]
    sharpe = None if vol in (None, 0) or xs.size == 0 else float(np.mean(xs) / np.std(xs, ddof=1) * math.sqrt(242.0))
    sortino = None if dvol in (None, 0) else float(np.mean(xs) / (np.std(down, ddof=1)) * math.sqrt(242.0))
    calmar = None if not mdd else (None if mdd == 0 else (cg / abs(mdd) if cg is not None else None))
    nets = np.array([tr["net"] for tr in trades], dtype=np.float64) if trades else np.array([])
    rets = np.array([tr["ret"] for tr in trades], dtype=np.float64) if trades else np.array([])
    win = float(np.mean(rets > 0)) if rets.size else None
    gp = float(np.sum(rets[rets > 0])) if rets.size else 0.0
    gl = float(np.abs(np.sum(rets[rets < 0]))) if rets.size else 0.0
    pf = None if gl == 0 else gp / gl
    turn = 2.0 / float(HOLD_DAYS)
    cost_drag = None
    if trades:
        cost_drag = float(np.sum([tr["gross"] - tr["net"] for tr in trades]) / sim["start"])
    years = {}
    for tr in trades:
        y = tr["signal_date"][:4]
        years.setdefault(y, []).append(tr["ret"])
    year_tab = {}
    for y, rs in sorted(years.items()):
        a = np.array(rs, dtype=np.float64)
        year_tab[y] = {"n": int(a.size), "mean_ret": float(np.mean(a)), "sum_ret": float(np.sum(a)), "win": float(np.mean(a > 0))}
    months = {}
    for d, r in _daily_rets(curve):
        m = d[:7]
        months.setdefault(m, []).append(r)
    month_tab = dict((m, float(np.prod(1.0 + np.array(v)) - 1.0)) for m, v in sorted(months.items()))
    return {
        "window": window_name,
        "start": start,
        "end": end,
        "start_equity": s0,
        "end_equity": s1,
        "total_return": s1 / s0 - 1.0 if s0 else None,
        "cagr": cg,
        "ann_vol": vol,
        "maxdd": mdd,
        "dd": ddinfo,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "n_trades": len(trades),
        "win_rate": win,
        "profit_factor": pf,
        "turnover_daily": turn,
        "turnover_weekly": turn * 5.0,
        "turnover_monthly": turn * 21.0,
        "turnover_annual": turn * 242.0,
        "average_holding": HOLD_DAYS,
        "cost_drag_over_start": cost_drag,
        "mean_period_net": float(np.mean(nets)) if nets.size else None,
        "years": year_tab,
        "monthly": month_tab,
        "worst_year": min(year_tab.items(), key=lambda kv: kv[1]["sum_ret"])[0] if year_tab else None,
    }


def windows(sim):
    return {
        "research": book_metrics(sim, "research", RESEARCH[0], RESEARCH[1]),
        "validation": book_metrics(sim, "validation", VALIDATION[0], VALIDATION[1]),
        "research_through_validation": book_metrics(sim, "research_through_validation", RESEARCH[0], VALIDATION[1]),
    }


def beta_capture(strat_curve, mkt_curve):
    a = dict((r["date"], r["equity"]) for r in strat_curve)
    b = dict((r["date"], r["equity"]) for r in mkt_curve)
    keys = sorted(set(a) & set(b))
    xs = []
    ys = []
    for i in range(1, len(keys)):
        d0, d1 = keys[i - 1], keys[i]
        if a[d0] > 0 and b[d0] > 0:
            ys.append(a[d1] / a[d0] - 1.0)
            xs.append(b[d1] / b[d0] - 1.0)
    xs = np.array(xs, dtype=np.float64)
    ys = np.array(ys, dtype=np.float64)
    if xs.size < 8 or float(np.var(xs)) == 0:
        return {"beta": None}
    beta = float(np.cov(ys, xs, ddof=1)[0, 1] / np.var(xs, ddof=1))
    up = ys[xs > 0]
    down = ys[xs < 0]
    xu = xs[xs > 0]
    xd = xs[xs < 0]
    return {
        "beta": beta,
        "up_capture": None if xu.size == 0 or float(np.mean(xu)) == 0 else float(np.mean(up) / np.mean(xu)),
        "down_capture": None if xd.size == 0 or float(np.mean(xd)) == 0 else float(np.mean(down) / np.mean(xd)),
        "tracking_error": float(np.std(ys - xs, ddof=1) * math.sqrt(242.0)) if xs.size > 2 else None,
        "n": int(xs.size),
        "benchmark": "EW_ELIGIBLE_OPEN_TO_OPEN_PROXY",
    }


def share_of_top(values, fracs=(0.01, 0.05, 0.10, 0.20)):
    xs = np.array(values, dtype=np.float64)
    xs = xs[np.isfinite(xs)]
    if xs.size == 0:
        return {}
    pos = xs[xs > 0]
    base = float(np.sum(pos)) if pos.size else 0.0
    order = np.argsort(xs)[::-1]
    out = {"n": int(xs.size), "n_negative": int(np.sum(xs < 0))}
    for f in fracs:
        k = max(1, int(math.ceil(xs.size * f)))
        top = float(np.sum(xs[order[:k]]))
        out["top_%s_of_pos" % int(f * 100)] = None if base == 0 else top / base
    return out
