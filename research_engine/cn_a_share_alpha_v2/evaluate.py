"""V15 metrics. MEAN_FORWARD_RETURN is not CAGR."""
from __future__ import print_function

import math

import numpy as np

from research_engine.cn_a_share_alpha.evaluate import block_bootstrap, fdr_from_pvals, iid_bootstrap, onesided_p, ttest_p
from research_engine.cn_a_share_alpha_v2.books import capital_cagr, maxdd_from_trades


def summarize_predictive(rows):
    if not rows:
        return {"n": 0, "MEAN_FORWARD_RETURN": None, "mean_raw": None}
    nets = np.array([r["MEAN_FORWARD_RETURN"] for r in rows], dtype=np.float64)
    raws = np.array([r.get("raw", np.nan) for r in rows], dtype=np.float64)
    tstat, pval = ttest_p(nets)
    return {
        "n": int(nets.size),
        "MEAN_FORWARD_RETURN": float(np.mean(nets)),
        "mean_raw": float(np.nanmean(raws)) if raws.size else None,
        "hit_rate": float(np.mean(nets > 0)),
        "tstat": tstat,
        "pval": pval,
        "not_cagr": True,
    }


def excess_mean(hyp_rows, bench_rows):
    b = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in bench_rows)
    xs = []
    for r in hyp_rows:
        if r["date"] in b:
            xs.append(r["MEAN_FORWARD_RETURN"] - b[r["date"]])
    if not xs:
        return None, None, None
    arr = np.array(xs, dtype=np.float64)
    tstat, pval = ttest_p(arr)
    return float(np.mean(arr)), tstat, pval


def summarize_capital(sim, start_date, hold):
    trades = sim["trades"]
    if not trades:
        return {"n_trades": 0, "total": None, "CAGR": None}
    n_days = hold * len(trades)
    dd = maxdd_from_trades(trades, sim["start"], start_date)
    rets = np.array([tr["capital_ret"] for tr in trades], dtype=np.float64)
    # daily-equivalent from period rets for sharpe: period vol * sqrt(242/hold)
    per_year = 242.0 / float(hold)
    vol = float(np.std(rets, ddof=1) * math.sqrt(per_year)) if rets.size > 2 else None
    down = rets[rets < 0]
    dvol = float(np.std(down, ddof=1) * math.sqrt(per_year)) if down.size > 2 else None
    mean_p = float(np.mean(rets))
    sharpe = None if vol in (None, 0) else mean_p / (np.std(rets, ddof=1)) * math.sqrt(per_year)
    sortino = None if dvol in (None, 0) else mean_p / (np.std(down, ddof=1)) * math.sqrt(per_year)
    cg = capital_cagr(sim["start"], sim["end"], n_days)
    calmar = None if not dd["maxdd"] else (None if dd["maxdd"] == 0 else (cg / abs(dd["maxdd"]) if cg is not None else None))
    years = {}
    for tr in trades:
        y = tr["signal_date"][:4]
        years.setdefault(y, []).append(tr["capital_ret"])
    year_tab = {}
    for y, rs in sorted(years.items()):
        a = np.array(rs, dtype=np.float64)
        eq = 1.0
        for r in a:
            eq *= 1.0 + r
        year_tab[y] = {"n": int(a.size), "compound": eq - 1.0, "mean": float(np.mean(a))}
    return {
        "n_trades": len(trades),
        "start": sim["start"],
        "end": sim["end"],
        "total": sim["total"],
        "CAGR": cg,
        "maxdd": dd["maxdd"],
        "dd": dd,
        "sharpe": None if sharpe is None else float(sharpe),
        "sortino": None if sortino is None else float(sortino),
        "calmar": calmar,
        "unfilled_rate": sim.get("unfilled_rate"),
        "recon_ok": sim.get("recon_ok"),
        "turnover_daily": 2.0 / float(hold),
        "years": year_tab,
        "win_rate": float(np.mean(rets > 0)) if rets.size else None,
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


def corr_maps(a, b):
    keys = sorted(set(a) & set(b))
    if len(keys) < 8:
        return None
    xa = np.array([a[k] for k in keys], dtype=np.float64)
    xb = np.array([b[k] for k in keys], dtype=np.float64)
    if float(np.std(xa)) == 0 or float(np.std(xb)) == 0:
        return None
    return float(np.corrcoef(xa, xb)[0, 1])
