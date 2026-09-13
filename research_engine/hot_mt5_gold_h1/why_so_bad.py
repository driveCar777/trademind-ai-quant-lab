"""Read-only: is H1_ML bad because of a bug, too little data, overfit, or no edge?"""
from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Dict, List

import numpy as np

from research_engine.hot_mt5_gold_h1.data import build_h1_matrix, load_h1
from research_engine.hot_mt5_gold_h1.engine import HOLD
from research_engine.hot_mt5_gold_h1.paths import HIST, RES


def _twr(xs):
    x = np.asarray(xs, float)
    return None if len(x) == 0 else float(np.prod(1.0 + x) - 1.0)


def _months(ts, px):
    bags = defaultdict(list)
    for t, p in zip(ts, px):
        bags[t[:7]].append(float(p))
    out = {}
    for m, xs in sorted(bags.items()):
        if len(xs) < 2 or xs[0] <= 0:
            continue
        out[m] = xs[-1] / xs[0] - 1.0
    return out


def verify_trades(bar, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    idx = {t: i for i, t in enumerate(bar["ts"])}
    o = bar["open"]
    n = len(o)
    err = 0
    checked = 0
    for tr in trades:
        i = idx.get(tr["entry"])
        j = idx.get(tr["exit"])
        if i is None or j is None:
            err += 1
            continue
        side = 1.0 if tr["side"] == "LONG" else -1.0
        raw = (float(o[j]) / float(o[i]) - 1.0) * side
        if abs(raw - tr["raw"]) > 1e-9:
            err += 1
        if j - i != HOLD:
            err += 1
        checked += 1
    return {"checked": checked, "mismatch": err, "hold_bars": HOLD, "n_bars": n}


def run() -> Dict[str, Any]:
    bar = load_h1(HIST / "GOLD_H1.csv")
    names, x = build_h1_matrix(bar)
    o, c = bar["open"], bar["close"]
    n = len(o)
    y = np.full(n, np.nan)
    y[: -(HOLD + 1)] = o[HOLD + 1:] / o[1:-HOLD] - 1.0
    finite_y = y[np.isfinite(y)]
    r1 = np.full(n, np.nan)
    r1[1:] = c[1:] / c[:-1] - 1.0

    ml = json.loads((RES / "ML_trades.json").read_text(encoding="utf-8"))
    tsm = json.loads((RES / "TSMOM_trades.json").read_text(encoding="utf-8"))
    read = json.loads((RES / "READ.json").read_text(encoding="utf-8"))

    bh_m = _months(bar["ts"], c)
    ml_m, tsm_m = defaultdict(list), defaultdict(list)
    for t in ml:
        ml_m[t["signal"][:7]].append(t["net"])
    for t in tsm:
        tsm_m[t["signal"][:7]].append(t["net"])
    ml_month = {k: _twr(v) for k, v in sorted(ml_m.items())}
    tsm_month = {k: _twr(v) for k, v in sorted(tsm_m.items())}

    def month_stats(d):
        xs = [v for v in d.values() if v is not None]
        return {
            "n_months": len(xs),
            "mean": float(np.mean(xs)) if xs else None,
            "median": float(np.median(xs)) if xs else None,
            "share_ge_10pct": float(np.mean(np.array(xs) >= 0.10)) if xs else None,
            "share_ge_20pct": float(np.mean(np.array(xs) >= 0.20)) if xs else None,
            "share_pos": float(np.mean(np.array(xs) > 0)) if xs else None,
            "best": float(np.max(xs)) if xs else None,
            "worst": float(np.min(xs)) if xs else None,
            "cagr_from_mean_approx": None if not xs else float((1.0 + np.mean(xs)) ** 12 - 1.0),
        }

    # overlapping 24h sign hit if always long
    long_only = finite_y
    # feature ICs already known; effective N = nonoverlap trades
    ac24 = None
    if len(finite_y) > 50:
        a, b = finite_y[:-1], finite_y[1:]
        # these overlap 23h so AC is inflated; use stride 24
        ys = y[np.arange(0, n, HOLD)]
        ys = ys[np.isfinite(ys)]
        if len(ys) > 50:
            ac24 = float(np.corrcoef(ys[:-1], ys[1:])[0, 1])

    # score-less: side vs realized
    def side_ic(trades):
        raw = np.array([t["raw"] for t in trades])
        side = np.array([1.0 if t["side"] == "LONG" else -1.0 for t in trades])
        # raw already includes side, so |raw| * sign match
        unsigned = np.array([
            (1.0 if t["side"] == "LONG" else -1.0) * t["raw"] for t in trades
        ])
        hit = float(np.mean(raw > 0))
        return {"dir_hit": hit, "mean_unsigned_24h": float(np.mean(unsigned))}

    val_i = int(2000 + 0.70 * (n - 2000))
    # in-sample vs OOS feature IC already in FORENSICS; add y scale
    out = {
        "profile": "HOT_MT5_GOLD_H1_WHY_SO_BAD",
        "candidate": False,
        "rewrites_read": False,
        "audit": {
            "ml_trade_match": verify_trades(bar, ml),
            "tsmom_trade_match": verify_trades(bar, tsm),
            "label": "y[t] = open[t+1+24]/open[t+1]-1; signal at t uses close[t]; enter next open",
            "n_refits": read.get("n_refits"),
            "n_features": len(names),
            "n_bars": n,
            "n_ml_trades": len(ml),
            "lgbm": "200 trees, 15 leaves, min_child 40 — smaller than 1500+ train rows per fold",
        },
        "gold_itself": {
            "buy_hold": float(c[-1] / c[0] - 1.0),
            "years": 7.75,
            "cagr": float((c[-1] / c[0]) ** (1.0 / 7.75) - 1.0),
            "mean_abs_24h": float(np.mean(np.abs(finite_y))),
            "median_abs_24h": float(np.median(np.abs(finite_y))),
            "share_24h_ge_10pct": float(np.mean(np.abs(finite_y) >= 0.10)),
            "share_24h_ge_2pct": float(np.mean(np.abs(finite_y) >= 0.02)),
            "always_long_24h_twr_overlap_not_a_book": float(np.prod(1.0 + finite_y) - 1.0),
            "month": month_stats(bh_m),
            "months_ge_10": [k for k, v in bh_m.items() if v >= 0.10],
            "months_ge_20": [k for k, v in bh_m.items() if v >= 0.20],
            "months_le_m10": [k for k, v in bh_m.items() if v <= -0.10],
        },
        "needed_for_10pct_month": {
            "10pct_per_month_is_annual": 1.10 ** 12 - 1.0,
            "20pct_per_month_is_annual": 1.20 ** 12 - 1.0,
            "gold_cagr": float((c[-1] / c[0]) ** (1.0 / 7.75) - 1.0),
        },
        "sample": {
            "rows_ok_for_ml": 45818,
            "nonoverlap_24h_trades": len(ml),
            "ac_nonoverlap_24h": ac24,
            "too_little_data": False,
            "why": "45k rows / 1752 independent 24h bets. Tree is small. Scarce thing is independent gold regimes, not rows.",
        },
        "overfit_signs": {
            "ml_research_twr": read["books"]["H1_ML"]["research_70"]["twr"],
            "ml_val_twr": read["books"]["H1_ML"]["validation_30"]["twr"],
            "classic_overfit": "research >> validation. Here research -46% and val -1% — no in-sample edge to overfit.",
            "last_month_ml": read["books"]["H1_ML"]["last_month_diagnostic"]["twr"],
        },
        "ml_month": month_stats(ml_month),
        "tsmom_month": month_stats(tsm_month),
        "ml_best_months": sorted(((k, v) for k, v in ml_month.items() if v is not None), key=lambda kv: -kv[1])[:5],
        "ml_worst_months": sorted(((k, v) for k, v in ml_month.items() if v is not None), key=lambda kv: kv[1])[:5],
        "side": {"ml": side_ic(ml), "tsmom": side_ic(tsm)},
        "what_is_missing": {
            "factors": "own OHLC only. No DXY, real yield, COT, news, options.",
            "h1_clock": "features named like D1 (SMA200=8.3 days). Not missing columns — wrong clock.",
            "shell": "sign(score) always-in. 13%/yr cost. Shorts fight +250% drift.",
            "target": "next 24h close-to-close sign has |IC|<0.07.",
        },
    }
    (RES / "WHY_SO_BAD.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main():
    out = run()
    a, g, n = out["audit"], out["gold_itself"], out["needed_for_10pct_month"]
    print("AUDIT ml mismatch", a["ml_trade_match"], "tsm", a["tsmom_trade_match"])
    print("GOLD BH %.1f%% CAGR %.1f%% | 24h |move| med %.1fbp | months +10%% %s +20%% %s -10%% %s" % (
        100 * g["buy_hold"], 100 * g["cagr"], 10000 * g["median_abs_24h"],
        g["month"]["share_ge_10pct"], g["month"]["share_ge_20pct"],
        len(g["months_le_m10"]) / max(1, g["month"]["n_months"]),
    ))
    print("GOLD months +10%", g["months_ge_10"], " +20%", g["months_ge_20"])
    print("10%%/mo = %.0f%%/yr   20%%/mo = %.0f%%/yr   gold was %.0f%%/yr" % (
        100 * n["10pct_per_month_is_annual"], 100 * n["20pct_per_month_is_annual"], 100 * n["gold_cagr"]))
    print("ML months", out["ml_month"])
    print("ML best", out["ml_best_months"])
    print("ML worst", out["ml_worst_months"])
    print("OVERFIT", out["overfit_signs"]["classic_overfit"])
    print("SAMPLE", out["sample"]["why"], "ac24", out["sample"]["ac_nonoverlap_24h"])


if __name__ == "__main__":
    main()
