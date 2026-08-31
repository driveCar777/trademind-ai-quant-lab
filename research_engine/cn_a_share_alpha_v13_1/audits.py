"""Concentration, cost, PIT, liquidity. No retune."""
from __future__ import print_function

import math

import numpy as np

from research_engine.cn_a_share.pit import future_delist_mutation_stable, universe_excludes_future_ipo
from research_engine.cn_a_share.universe import listed_on
from research_engine.cn_a_share.universe_daily import load_equities
from research_engine.cn_a_share.paths import REFERENCE
from research_engine.cn_a_share_alpha.evaluate import block_bootstrap, iid_bootstrap, ttest_p
from research_engine.cn_a_share_alpha.cost import round_trip_cost
from research_engine.cn_a_share_alpha_v13_1 import SEED
from research_engine.cn_a_share_alpha_v13_1.path_b import market_ew_60, regime_label
import os


def share_of_top(values, fracs=(0.01, 0.05, 0.10, 0.20)):
    xs = np.array(values, dtype=np.float64)
    xs = xs[np.isfinite(xs)]
    if xs.size == 0:
        return {}
    total = float(np.sum(xs))
    order = np.argsort(xs)[::-1]
    out = {}
    for f in fracs:
        k = max(1, int(math.ceil(xs.size * f)))
        top = float(np.sum(xs[order[:k]]))
        out["top_%s" % int(f * 100)] = None if total == 0 else top / total
    neg = xs[xs < 0]
    out["n"] = int(xs.size)
    out["n_negative"] = int(neg.size)
    out["neg_share"] = None if total == 0 else float(np.sum(neg) / total)
    return out


def stock_concentration(stock_map):
    nets = [v["net"] for v in stock_map.values()]
    return share_of_top(nets)


def time_concentration(rows, key="net"):
    return share_of_top([r[key] for r in rows])


def year_table(rows, hold_days=20):
    buckets = {}
    for r in rows:
        y = r["date"][:4]
        buckets.setdefault(y, []).append(r)
    out = {}
    per_year = 242.0 / float(hold_days)
    turn = 2.0 / float(hold_days)
    for y, rs in sorted(buckets.items()):
        nets = np.array([x["net"] for x in rs], dtype=np.float64)
        mean_net = float(np.mean(nets))
        eq = 1.0
        peak = 1.0
        dd = 0.0
        for x in rs:
            eq *= 1.0 + float(x["net"])
            if eq > peak:
                peak = eq
            if peak > 0:
                dd = min(dd, eq / peak - 1.0)
        out[y] = {
            "n": int(nets.size),
            "mean_net": mean_net,
            "cagr_equivalent_diagnostic": (1.0 + mean_net) ** per_year - 1.0,
            "maxdd_overlapping_diagnostic": dd,
            "turnover_daily_equivalent": turn,
            "trade_count_overlapping": int(nets.size),
            "win_rate": float(np.mean(nets > 0)),
            "sum_net": float(np.sum(nets)),
        }
    return out


def turnover_audit(hold_days=20):
    daily = 2.0 / float(hold_days)
    return {
        "contract_rebalance": "NON_OVERLAPPING_EVERY_HOLD",
        "hold_days": hold_days,
        "daily_equivalent": daily,
        "weekly_equivalent": daily * 5.0,
        "monthly_equivalent": daily * 21.0,
        "note": "Two-way unit-book turnover if the book is fully replaced every hold.",
    }


def portfolio_concentration(rows):
    fills = [int(r["n_fill"]) for r in rows if r.get("n_fill")]
    if not fills:
        return {"equal_weight": True, "mean_effective_n": None}
    hhi = [1.0 / float(n) for n in fills]
    return {
        "equal_weight": True,
        "mean_filled": float(np.mean(fills)),
        "min_filled": int(min(fills)),
        "max_filled": int(max(fills)),
        "mean_effective_n": float(np.mean(fills)),
        "mean_hhi": float(np.mean(hhi)),
        "note": "EW book: effective N = filled count. Abnormal concentration would be min_filled << 20.",
    }


def breadth_stats(rows):
    if not rows:
        return {}
    elig = [r["n_elig"] for r in rows if "n_elig" in r]
    sel = [r["n_sel"] for r in rows if "n_sel" in r]
    fill = [r["n_fill"] for r in rows if "n_fill" in r]
    return {
        "mean_eligible": float(np.mean(elig)) if elig else None,
        "min_eligible": int(min(elig)) if elig else None,
        "mean_selected": float(np.mean(sel)) if sel else None,
        "min_selected": int(min(sel)) if sel else None,
        "mean_filled": float(np.mean(fill)) if fill else None,
        "min_filled": int(min(fill)) if fill else None,
        "thin_days_selected_lt_20": int(sum(1 for x in sel if x < 20)),
        "thin_days_selected_lt_10": int(sum(1 for x in sel if x < 10)),
    }


def liquidity_diag(trades):
    ratios = []
    advs = []
    for tr in trades:
        med = tr.get("adv")
        if med is None:
            fills = [n["amount"] for n in tr.get("names") or [] if n.get("amount")]
            if not fills:
                continue
            med = float(np.median(fills))
        advs.append(med)
        n = max(1, int(tr.get("n_fill") or tr.get("n_sel") or 1))
        ratios.append((1.0 / n) / med if med and med > 0 else None)
    ratios = [x for x in ratios if x is not None]
    return {
        "median_adv_amount": float(np.median(advs)) if advs else None,
        "n_rebalances": len(trades),
        "note": "position/ADV is a unit-book diagnostic. Not a capital mandate.",
        "median_unit_weight_over_adv": float(np.median(ratios)) if ratios else None,
    }


def cost_breakdown(rows):
    if not rows:
        return {}
    return {
        "mean_gross": float(np.mean([r["gross"] for r in rows])),
        "mean_net": float(np.mean([r["net"] for r in rows])),
        "mean_cost": float(np.mean([r["cost"] for r in rows])),
        "mean_commission": float(np.mean([r["commission"] for r in rows])),
        "mean_stamp": float(np.mean([r["stamp"] for r in rows])),
        "mean_slippage": float(np.mean([r["slippage"] for r in rows])),
        "mean_transfer": float(np.mean([r["transfer"] for r in rows])),
    }


def beta_vs_market(hyp_rows, mkt_rows):
    h = dict((r["date"], r["net"]) for r in hyp_rows)
    m = dict((r["date"], r["raw"]) for r in mkt_rows)
    xs = []
    ys = []
    for d in h:
        if d in m:
            xs.append(m[d])
            ys.append(h[d])
    xs = np.array(xs, dtype=np.float64)
    ys = np.array(ys, dtype=np.float64)
    if xs.size < 20 or float(np.var(xs)) == 0:
        return {"beta": None, "down_mean": None}
    beta = float(np.cov(ys, xs, ddof=1)[0, 1] / np.var(xs, ddof=1))
    down = ys[xs < 0]
    return {
        "beta": beta,
        "down_market_mean_net": float(np.mean(down)) if down.size else None,
        "n": int(xs.size),
        "limitation": "Industry PIT BLOCKED. Size is amount-proxy only.",
    }


def regime_table(pack, elig, rows):
    r60, dd = market_ew_60(pack, elig)
    dates = pack["dates"]
    ix = dict((d, i) for i, d in enumerate(dates))
    buckets = {}
    for r in rows:
        i = ix.get(r["date"])
        if i is None:
            continue
        lab = regime_label(r60[i], dd[i])
        if not lab:
            continue
        buckets.setdefault(lab, []).append(r["net"])
    return dict((k, {"n": len(v), "mean_net": float(np.mean(v))}) for k, v in sorted(buckets.items()))


def pit_audit():
    basic = os.path.join(REFERENCE, "tm-cn-a-BASIC-20260830-000001.csv")
    equities = load_equities(basic)
    asof = "2020-06-01"
    before = sorted(e["symbol"] for e in equities if listed_on(e, asof))
    mutated = list(equities) + [
        {"symbol": "sh.999997", "instrument_type": "EQUITY", "listing_date": "2026-06-01", "delisting_date": ""}
    ]
    after = sorted(e["symbol"] for e in mutated if listed_on(e, asof))
    basics = [
        {"code": e["symbol"], "ipoDate": e.get("listing_date") or "", "outDate": e.get("delisting_date") or "", "type": "1", "status": "1"}
        for e in equities[:50]
    ]
    return {
        "future_ipo_leaves_2020": before == after,
        "n_listed_2020_06_01": len(before),
        "delist_mutation_stable": future_delist_mutation_stable(equities, asof),
        "future_ipo_fn": universe_excludes_future_ipo(basics + [{"code": "sh.999996", "ipoDate": "2026-06-01", "outDate": "", "type": "1", "status": "1"}], asof),
    }


def execution_audit(pack, trades, xok):
    dates = pack["dates"]
    symbols = pack["symbols"]
    sym_ix = dict((s, i) for i, s in enumerate(symbols))
    date_ix = dict((d, i) for i, d in enumerate(dates))
    n_names = 0
    n_susp_fill = 0
    n_limit_fill = 0
    n_unlisted_fill = 0
    pairs = []
    for tr in trades:
        t0 = date_ix.get(tr["entry"])
        t1 = date_ix.get(tr["exit"])
        js = tr.get("filled_js") or []
        n_names += len(js)
        for j in js:
            if t0 is None:
                continue
            if int(pack["tradestatus"][t0, j]) == 0:
                n_susp_fill += 1
            if not bool(xok[t0, j]):
                n_limit_fill += 1
            if int(pack["listed"][t0, j]) != 1:
                n_unlisted_fill += 1
            pairs.append((tr, j, t0, t1))
    rng = np.random.RandomState(SEED)
    sample = []
    if pairs:
        take = min(120, len(pairs))
        pick = rng.choice(len(pairs), size=take, replace=False)
        for i in pick:
            tr, j, t0, t1 = pairs[int(i)]
            a = float(pack["open"][t0, j])
            b = float(pack["open"][t1, j])
            gross = (b / a - 1.0) if (np.isfinite(a) and np.isfinite(b) and a > 0) else None
            cost = round_trip_cost(tr["entry"], tr["exit"])
            sample.append(
                {
                    "signal_date": tr["signal_date"],
                    "entry": tr["entry"],
                    "exit": tr["exit"],
                    "symbol": symbols[j],
                    "gross": gross,
                    "net": None if gross is None else gross - cost,
                    "hold_days": tr["hold_days"],
                }
            )
    return {
        "n_filled_names": n_names,
        "suspended_fills": n_susp_fill,
        "non_exec_mask_fills": n_limit_fill,
        "unlisted_fills": n_unlisted_fill,
        "hold_days_locked": all(tr.get("hold_days") == 20 for tr in trades),
        "sample": sample,
    }


def ca_audit(pack, trades):
    dates = pack["dates"]
    symbols = pack["symbols"]
    sym_ix = dict((s, i) for i, s in enumerate(symbols))
    date_ix = dict((d, i) for i, d in enumerate(dates))
    jumps = 0
    n = 0
    for tr in trades:
        t = date_ix.get(tr["signal_date"])
        if t is None:
            continue
        js = tr.get("filled_js") or [sym_ix[n["symbol"]] for n in tr.get("names") or [] if n.get("symbol") in sym_ix]
        for j in js:
            n += 1
            c = float(pack["close"][t, j])
            p = float(pack["preclose"][t, j])
            if np.isfinite(c) and np.isfinite(p) and p > 0 and abs(c / p - 1.0) > 0.12:
                jumps += 1
    return {
        "n_checked": n,
        "close_vs_preclose_gt_12pct": jumps,
        "limitation": "Ranking uses raw close. Full qfq panel was not frozen. Possible CA jump days.",
    }


def bootstrap_report(nets):
    tstat, pval = ttest_p(nets)
    return {
        "iid": iid_bootstrap(nets, n=1000, seed=SEED),
        "block": block_bootstrap(nets, n=1000, seed=SEED),
        "tstat": tstat,
        "two_sided_p": pval,
    }
