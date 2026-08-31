"""IC, metrics, FDR, bootstrap. Sign is locked."""
from __future__ import print_function

import math

import numpy as np

from research_engine.cn_a_share_alpha import FDR_Q, HOLD_DAYS, SEED
from research_engine.statistics import benjamini_hochberg


def _nets(rows):
    return np.array([r["net"] for r in rows], dtype=np.float64)


def _mean(xs):
    if xs.size == 0:
        return None
    return float(np.mean(xs))


def spearman_ic(pack, scores, elig, t, fwd):
    mask = elig[t] & np.isfinite(scores[t]) & np.isfinite(fwd)
    if int(np.sum(mask)) < 30:
        return None
    a = scores[t][mask]
    b = fwd[mask]
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    ra = ra.astype(np.float64)
    rb = rb.astype(np.float64)
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float(np.sum(ra * ra) * np.sum(rb * rb)))
    if den == 0:
        return None
    return float(np.sum(ra * rb) / den)


def forward_open_h(pack, t):
    t0 = t + 1
    t1 = t + 1 + HOLD_DAYS
    if t1 >= len(pack["dates"]):
        return None
    a = np.array(pack["open"][t0], dtype=np.float64)
    b = np.array(pack["open"][t1], dtype=np.float64)
    out = np.full(a.shape, np.nan)
    good = np.isfinite(a) & np.isfinite(b) & (a > 0)
    out[good] = b[good] / a[good] - 1.0
    return out


def ic_series(pack, scores, elig, start, end):
    dates = pack["dates"]
    i0 = dates.index(start)
    i1 = dates.index(end)
    ics = []
    for t in range(i0, i1 + 1):
        fwd = forward_open_h(pack, t)
        if fwd is None:
            continue
        ic = spearman_ic(pack, scores, elig, t, fwd)
        if ic is not None:
            ics.append(ic)
    return ics


def ttest_p(xs):
    xs = np.asarray(xs, dtype=np.float64)
    xs = xs[np.isfinite(xs)]
    n = xs.size
    if n < 8:
        return None, None
    m = float(np.mean(xs))
    s = float(np.std(xs, ddof=1))
    if s == 0:
        return m, 1.0
    t = m / (s / math.sqrt(n))
    # two-sided normal approx
    p = math.erfc(abs(t) / math.sqrt(2.0))
    return t, min(1.0, max(0.0, p))


def cagr_from_h(mean_h, years):
    if mean_h is None or years <= 0:
        return None
    per_year = 242.0 / float(HOLD_DAYS)
    return (1.0 + mean_h) ** per_year - 1.0


def max_dd(equity_rows):
    peak = -1e99
    dd = 0.0
    for row in equity_rows:
        eq = row["equity"]
        if eq > peak:
            peak = eq
        if peak > 0:
            dd = min(dd, eq / peak - 1.0)
    return dd


def book_metrics(rows, equity_rows, trades, years):
    nets = _nets(rows)
    raws = np.array([r["raw"] for r in rows], dtype=np.float64) if rows else np.array([])
    mean_net = _mean(nets)
    mean_raw = _mean(raws)
    tstat, pval = ttest_p(nets)
    eq = equity_rows[-1]["equity"] if equity_rows else None
    n_tr = len(trades)
    turn = 2.0 / float(HOLD_DAYS) if n_tr else 0.0
    advs = [tr["adv"] for tr in trades if tr.get("adv")]
    return {
        "n_obs": int(nets.size),
        "n_rebalances": n_tr,
        "mean_raw_h": mean_raw,
        "mean_net_h": mean_net,
        "cost_drag_h": None if mean_raw is None or mean_net is None else mean_raw - mean_net,
        "tstat": tstat,
        "pval": pval,
        "cagr": cagr_from_h(mean_net, years),
        "total_return": None if eq is None else eq - 1.0,
        "maxdd": max_dd(equity_rows) if equity_rows else None,
        "daily_turnover": turn,
        "weekly_turnover": turn * 5.0,
        "monthly_turnover": turn * 21.0,
        "median_adv": float(np.median(advs)) if advs else None,
        "win_rate": float(np.mean(nets > 0)) if nets.size else None,
    }


def excess_series(hyp_rows, bench_rows):
    b = dict((r["date"], r["net"]) for r in bench_rows)
    out = []
    for r in hyp_rows:
        if r["date"] in b:
            out.append(r["net"] - b[r["date"]])
    return np.array(out, dtype=np.float64)


def iid_bootstrap(xs, n=1000, seed=SEED):
    rng = np.random.RandomState(seed)
    xs = np.asarray(xs, dtype=np.float64)
    xs = xs[np.isfinite(xs)]
    if xs.size == 0:
        return {"mean": None, "p_pos": None}
    draws = []
    for _ in range(n):
        samp = rng.choice(xs, size=xs.size, replace=True)
        draws.append(float(np.mean(samp)))
    draws = np.array(draws)
    return {"mean": float(np.mean(xs)), "boot_mean": float(np.mean(draws)), "p_pos": float(np.mean(draws > 0)), "n": n}


def block_bootstrap(xs, block=HOLD_DAYS, n=1000, seed=SEED):
    rng = np.random.RandomState(seed + 17)
    xs = np.asarray(xs, dtype=np.float64)
    xs = xs[np.isfinite(xs)]
    if xs.size < block * 2:
        return iid_bootstrap(xs, n=n, seed=seed)
    n_b = int(math.ceil(xs.size / float(block)))
    draws = []
    for _ in range(n):
        chunks = []
        for _k in range(n_b):
            i = rng.randint(0, xs.size - block + 1)
            chunks.append(xs[i : i + block])
        samp = np.concatenate(chunks)[: xs.size]
        draws.append(float(np.mean(samp)))
    return {"mean": float(np.mean(xs)), "boot_mean": float(np.mean(draws)), "p_pos": float(np.mean(np.array(draws) > 0)), "n": n, "block": block}


def onesided_p(tstat, twosided_p):
    if tstat is None or twosided_p is None:
        return 1.0
    if tstat <= 0:
        return 1.0
    return min(1.0, 0.5 * float(twosided_p))


def fdr_from_pvals(pvals):
    return benjamini_hochberg(pvals, q=FDR_Q)


def is_level1(res, val, fdr_hit):
    """Cost-adjusted absolute profit on both windows, plus excess, IC, FDR."""
    r_net = (res.get("metrics") or {}).get("mean_net_h")
    v_net = (val.get("metrics") or {}).get("mean_net_h")
    r_ex = res.get("excess_vs_b0_mean")
    v_ex = val.get("excess_vs_b0_mean")
    r_ic = res.get("rank_ic")
    v_ic = val.get("rank_ic")
    if None in (r_net, v_net, r_ex, v_ex, r_ic, v_ic):
        return False
    if r_net <= 0 or v_net <= 0:
        return False
    if r_ex <= 0 or v_ex <= 0:
        return False
    if r_ic <= 0 or v_ic <= 0:
        return False
    if not fdr_hit:
        return False
    return True


def years_between(a, b):
    return (int(b[:4]) - int(a[:4])) + (int(b[5:7]) - int(a[5:7])) / 12.0
