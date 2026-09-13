"""Read-only GOLD H1 V1 forensics. Does not retrain. Does not rewrite READ.json."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any, Dict, List

import numpy as np

from research_engine.hot_mt5_gold_h1.data import load_h1
from research_engine.hot_mt5_gold_h1.paths import HIST, RES

HOLD = 24
SESSION = {
    "ASIA": range(0, 7),
    "LONDON": range(7, 13),
    "NY": range(13, 21),
    "LATE": range(21, 24),
}


def _twr(xs):
    x = np.asarray(xs, float)
    return None if len(x) == 0 else float(np.prod(1.0 + x) - 1.0)


def _mean(xs):
    return None if not xs else float(np.mean(xs))


def _hit(xs):
    return None if not xs else float(np.mean(np.asarray(xs, float) > 0))


def _payoff(xs):
    x = np.asarray(xs, float)
    w, l = x[x > 0], x[x <= 0]
    if len(w) == 0 or len(l) == 0 or l.mean() >= 0:
        return None
    return float(w.mean() / (-l.mean()))


def _tstat(xs):
    x = np.asarray(xs, float)
    if len(x) < 3 or x.std(ddof=1) <= 0:
        return None
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))


def _streak(sides):
    if not sides:
        return 0
    best = cur = 1
    last = sides[0]
    for s in sides[1:]:
        cur = cur + 1 if s == last else 1
        best = max(best, cur)
        last = s
    return best


def _session(hour: int) -> str:
    for name, rng in SESSION.items():
        if hour in rng:
            return name
    return "LATE"


def _sleeve(trades, key="net"):
    long_t = [t[key] for t in trades if t["side"] == "LONG"]
    short_t = [t[key] for t in trades if t["side"] == "SHORT"]
    return {
        "n": len(trades),
        "long_n": len(long_t),
        "short_n": len(short_t),
        "long_share": (len(long_t) / float(len(trades))) if trades else None,
        "raw_twr": _twr([t["raw"] for t in trades]),
        "net_twr": _twr([t["net"] for t in trades]),
        "mean_raw": _mean([t["raw"] for t in trades]),
        "mean_net": _mean([t["net"] for t in trades]),
        "mean_cost": _mean([t["cost"] for t in trades]),
        "median_cost": float(np.median([t["cost"] for t in trades])) if trades else None,
        "hit": _hit([t["net"] for t in trades]),
        "payoff": _payoff([t["net"] for t in trades]),
        "t": _tstat([t["net"] for t in trades]),
        "long_mean_net": _mean(long_t),
        "short_mean_net": _mean(short_t),
        "long_twr": _twr(long_t),
        "short_twr": _twr(short_t),
        "max_same_side": _streak([t["side"] for t in trades]),
    }


def _by(trades, fn):
    bags = defaultdict(list)
    for t in trades:
        bags[fn(t)].append(t)
    out = {}
    for k in sorted(bags):
        xs = bags[k]
        out[str(k)] = {
            "n": len(xs),
            "net_twr": _twr([t["net"] for t in xs]),
            "mean_net": _mean([t["net"] for t in xs]),
            "mean_raw": _mean([t["raw"] for t in xs]),
            "mean_cost": _mean([t["cost"] for t in xs]),
            "hit": _hit([t["net"] for t in xs]),
            "t": _tstat([t["net"] for t in xs]),
            "long_share": float(np.mean([t["side"] == "LONG" for t in xs])),
        }
    return out


def _path(bar, trades, ts_index):
    high, low, o = bar["high"], bar["low"], bar["open"]
    n = len(o)
    mfe, mae, giveback, peak_bar = [], [], [], []
    for t in trades:
        i = ts_index.get(t["entry"])
        if i is None or i + HOLD >= n:
            continue
        entry = float(o[i])
        if entry <= 0:
            continue
        side = 1.0 if t["side"] == "LONG" else -1.0
        window_h = high[i:i + HOLD + 1]
        window_l = low[i:i + HOLD + 1]
        if side > 0:
            fav = float(np.max(window_h) / entry - 1.0)
            adv = float(np.min(window_l) / entry - 1.0)
        else:
            fav = float(1.0 - np.min(window_l) / entry)
            adv = float(1.0 - np.max(window_h) / entry)
        raw = float(t["raw"])
        mfe.append(fav)
        mae.append(adv)
        giveback.append(fav - raw)
        intra = (high[i:i + HOLD + 1] - low[i:i + HOLD + 1]) / entry
        peak_bar.append(float(np.max(intra)))
    return {
        "n_matched": len(mfe),
        "mean_mfe": _mean(mfe),
        "mean_mae": _mean(mae),
        "median_mfe": float(np.median(mfe)) if mfe else None,
        "median_mae": float(np.median(mae)) if mae else None,
        "mean_giveback": _mean(giveback),
        "mean_intrabar_range": _mean(peak_bar),
        "share_mfe_gt_2cost": (
            float(np.mean(np.asarray(mfe) > 2.0 * np.asarray([t["cost"] for t in trades[:len(mfe)]])))
            if mfe else None
        ),
    }


def _ceiling(trades):
    """Perfect-foresight sit-out: take the trade only if |raw| > 2*cost. Diagnostic, not a book."""
    kept = [t["net"] if abs(t["raw"]) > 2.0 * t["cost"] else 0.0 for t in trades]
    taken = [t for t in trades if abs(t["raw"]) > 2.0 * t["cost"]]
    return {
        "note": "DIAGNOSTIC_NOT_A_BOOK. Uses realized raw. Cannot trade.",
        "share_tradable": (len(taken) / float(len(trades))) if trades else None,
        "n_taken": len(taken),
        "oracle_twr_if_taken_same_side": _twr([t["net"] for t in taken]),
        "oracle_twr_sit_else": _twr(kept),
        "mean_abs_raw": _mean([abs(t["raw"]) for t in trades]),
        "mean_abs_raw_over_cost": _mean([abs(t["raw"]) / max(1e-12, t["cost"]) for t in trades]),
    }


def _bars(bar):
    ts, o, h, l, c, spr = bar["ts"], bar["open"], bar["high"], bar["low"], bar["close"], bar["spread"]
    n = len(ts)
    hours = [int(t[11:13]) for t in ts]
    dates = [t[:10] for t in ts]
    per_day = Counter(dates)
    r1 = np.full(n, np.nan)
    r1[1:] = c[1:] / c[:-1] - 1.0
    fwd24 = np.full(n, np.nan)
    fwd24[: -(HOLD + 1)] = o[HOLD + 1:] / o[1:-HOLD] - 1.0
    mom120 = np.full(n, np.nan)
    mom120[120:] = c[120:] / c[:-120] - 1.0
    mom252d = np.full(n, np.nan)
    lb = 252 * 24
    if n > lb:
        mom252d[lb:] = c[lb:] / c[:-lb] - 1.0
    hour_ic = {}
    for hr in range(24):
        mask = (np.array(hours) == hr) & np.isfinite(fwd24)
        hour_ic[str(hr)] = {
            "n": int(mask.sum()),
            "mean_abs_fwd24": float(np.nanmean(np.abs(fwd24[mask]))) if mask.any() else None,
            "mean_fwd24": float(np.nanmean(fwd24[mask])) if mask.any() else None,
            "mean_range": float(np.nanmean((h[mask] - l[mask]) / np.maximum(1e-12, c[mask]))) if mask.any() else None,
        }
    sess_vol = {}
    for name, rng in SESSION.items():
        mask = np.array([h_ in rng for h_ in hours]) & np.isfinite(r1)
        sess_vol[name] = {
            "n": int(mask.sum()),
            "mean_abs_r1": float(np.nanmean(np.abs(r1[mask]))) if mask.any() else None,
            "mean_range": float(np.nanmean((h[mask] - l[mask]) / np.maximum(1e-12, c[mask]))) if mask.any() else None,
        }

    def _ic(a, b):
        m = np.isfinite(a) & np.isfinite(b)
        if int(m.sum()) < 50:
            return None
        return float(np.corrcoef(a[m], b[m])[0, 1])

    # Sunday gap: previous Friday close -> first Sunday/Monday bar
    gaps = []
    for i in range(1, n):
        if dates[i] != dates[i - 1]:
            wd = __import__("datetime").date.fromisoformat(dates[i]).isoweekday()
            if wd in (7, 1) and dates[i - 1] < dates[i]:
                gaps.append(float(o[i] / c[i - 1] - 1.0))

    bh = float(c[-1] / c[0] - 1.0)
    eq = c / c[0]
    peak = np.maximum.accumulate(eq)
    bh_dd = float(np.min(eq / peak - 1.0))
    spread_frac = spr * 0.01 / np.maximum(1e-12, c)
    spread_frac = spread_frac[np.isfinite(spread_frac) & (spread_frac > 0)]
    return {
        "n_bars": n,
        "first": ts[0],
        "last": ts[-1],
        "hours_unique": sorted(set(hours)),
        "median_bars_per_day": float(np.median(list(per_day.values()))),
        "min_bars_per_day": int(min(per_day.values())),
        "max_bars_per_day": int(max(per_day.values())),
        "n_days": len(per_day),
        "buy_hold_twr": bh,
        "buy_hold_maxdd": bh_dd,
        "mean_abs_r1": float(np.nanmean(np.abs(r1))),
        "mean_abs_fwd24": float(np.nanmean(np.abs(fwd24))),
        "median_abs_fwd24": float(np.nanmedian(np.abs(fwd24))),
        "p90_abs_fwd24": float(np.nanpercentile(np.abs(fwd24), 90)),
        "session_vol": sess_vol,
        "hour_fwd24": hour_ic,
        "ic_mom120_vs_fwd24": _ic(mom120, fwd24),
        "ic_mom252d_vs_fwd24": _ic(mom252d, fwd24),
        "ic_r1_vs_next_r1": _ic(r1[:-1], r1[1:]),
        "weekend_gap_n": len(gaps),
        "weekend_gap_mean_abs": _mean([abs(g) for g in gaps]),
        "weekend_gap_mean": _mean(gaps),
        "median_spread_frac": float(np.median(spread_frac)) if len(spread_frac) else None,
        "mean_spread_frac": float(np.mean(spread_frac)) if len(spread_frac) else None,
        "p90_spread_frac": float(np.percentile(spread_frac, 90)) if len(spread_frac) else None,
        "sma200_hours_in_days": 200 / 24.0,
        "hold24_in_days": 1.0,
        "mom120_in_days": 120 / 24.0,
        "d1_v4_lookback_in_hours": 252 * 24,
    }


def _feature_ic(bar):
    from research_engine.hot_mt5_gold_h1.data import build_h1_matrix
    names, x = build_h1_matrix(bar)
    o = bar["open"]
    n = len(o)
    y = np.full(n, np.nan)
    y[: -(HOLD + 1)] = o[HOLD + 1:] / o[1:-HOLD] - 1.0
    val_i = int(2000 + 0.70 * (n - 2000))
    out = []
    for j, name in enumerate(names):
        col = x[:, j]
        research = np.isfinite(col[:val_i]) & np.isfinite(y[:val_i])
        valid = np.isfinite(col[val_i:]) & np.isfinite(y[val_i:])
        ic_r = float(np.corrcoef(col[:val_i][research], y[:val_i][research])[0, 1]) if research.sum() > 50 else None
        ic_v = float(np.corrcoef(col[val_i:][valid], y[val_i:][valid])[0, 1]) if valid.sum() > 50 else None
        out.append({"name": name, "ic_research70": ic_r, "ic_validation30": ic_v})
    return out


def _agree(a, b):
    ia = {t["entry"]: t["side"] for t in a}
    ib = {t["entry"]: t["side"] for t in b}
    keys = sorted(set(ia) & set(ib))
    if not keys:
        return {"n_overlap": 0}
    same = sum(1 for k in keys if ia[k] == ib[k])
    return {"n_overlap": len(keys), "same_side": same / float(len(keys))}


def _month_detail(trades):
    month = [t for t in trades if t["signal"][:10] >= "2026-08-11"]
    return {
        "n": len(month),
        "twr": _twr([t["net"] for t in month]),
        "hit": _hit([t["net"] for t in month]),
        "long_n": sum(1 for t in month if t["side"] == "LONG"),
        "fills": [
            {"signal": t["signal"], "side": t["side"], "raw": t["raw"], "cost": t["cost"], "net": t["net"]}
            for t in month
        ],
    }


def one_book(name: str, trades: List[Dict[str, Any]], bar, ts_index) -> Dict[str, Any]:
    costs = np.array([t["cost"] for t in trades], float)
    raws = np.array([t["raw"] for t in trades], float)
    years = 7.75
    return {
        "book": name,
        "sleeve": _sleeve(trades),
        "year": _by(trades, lambda t: t["signal"][:4]),
        "entry_hour": _by(trades, lambda t: t["entry"][11:13]),
        "entry_session": _by(trades, lambda t: _session(int(t["entry"][11:13]))),
        "dow": _by(trades, lambda t: __import__("datetime").date.fromisoformat(t["signal"][:10]).strftime("%a")),
        "path": _path(bar, trades, ts_index),
        "ceiling": _ceiling(trades),
        "cost_drag_sum": float(np.sum(costs)),
        "cost_per_year": float(np.sum(costs) / years),
        "trades_per_year": len(trades) / years,
        "share_cost_gt_abs_raw": float(np.mean(costs > np.abs(raws))) if len(trades) else None,
        "last_month_diagnostic": _month_detail(trades),
        "worst5": [
            {"signal": t["signal"], "side": t["side"], "net": t["net"], "raw": t["raw"]}
            for t in sorted(trades, key=lambda t: t["net"])[:5]
        ],
        "best5": [
            {"signal": t["signal"], "side": t["side"], "net": t["net"], "raw": t["raw"]}
            for t in sorted(trades, key=lambda t: t["net"], reverse=True)[:5]
        ],
    }


def run() -> Dict[str, Any]:
    bar = load_h1(HIST / "GOLD_H1.csv")
    ts_index = {t: i for i, t in enumerate(bar["ts"])}
    ml = json.loads((RES / "ML_trades.json").read_text(encoding="utf-8"))
    tsm = json.loads((RES / "TSMOM_trades.json").read_text(encoding="utf-8"))
    out = {
        "profile": "HOT_MT5_GOLD_H1_V1_FORENSICS",
        "candidate": False,
        "retune": False,
        "rewrites_read": False,
        "bars": _bars(bar),
        "feature_ic_diagnostic": _feature_ic(bar),
        "agreement_ml_vs_tsmom": _agree(ml, tsm),
        "H1_ML": one_book("H1_ML", ml, bar, ts_index),
        "H1_TSMOM": one_book("H1_TSMOM", tsm, bar, ts_index),
        "mechanism_note": (
            "V1 transplanted D1 features onto hours and stayed always-in for 24 bars. "
            "SMA200 on H1 is ~8 days. 120h mom is ~5 days, not the D1 V4 252-day trend."
        ),
    }
    (RES / "FORENSICS.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def _p(label, obj):
    print(label, json.dumps(obj, ensure_ascii=False, default=str)[:400])


def main():
    out = run()
    b = out["bars"]
    print("BARS n=%s %s→%s bh=%.1f%% dd=%.1f%% |abs r1|=%.4f |fwd24|=%.4f med=%.4f p90=%.4f" % (
        b["n_bars"], b["first"], b["last"], 100 * b["buy_hold_twr"], 100 * b["buy_hold_maxdd"],
        b["mean_abs_r1"], b["mean_abs_fwd24"], b["median_abs_fwd24"], b["p90_abs_fwd24"],
    ))
    print("SPREAD median=%.4f mean=%.4f p90=%.4f  weekend_gap |mean|=%s" % (
        b["median_spread_frac"], b["mean_spread_frac"], b["p90_spread_frac"],
        None if b["weekend_gap_mean_abs"] is None else round(b["weekend_gap_mean_abs"], 4),
    ))
    print("IC mom120=%.4f mom252d=%s r1_ac1=%s  sma200=%.1f days  mom120=%.1f days" % (
        b["ic_mom120_vs_fwd24"],
        None if b["ic_mom252d_vs_fwd24"] is None else round(b["ic_mom252d_vs_fwd24"], 4),
        None if b["ic_r1_vs_next_r1"] is None else round(b["ic_r1_vs_next_r1"], 4),
        b["sma200_hours_in_days"], b["mom120_in_days"],
    ))
    print("SESSION", {k: {kk: (None if vv is None else round(vv, 5)) for kk, vv in v.items() if kk != "n"} | {"n": v["n"]}
                      for k, v in b["session_vol"].items()})
    print("AGREE", out["agreement_ml_vs_tsmom"])
    print("FEATURE IC")
    for row in out["feature_ic_diagnostic"]:
        print("  %s R=%s V=%s" % (
            row["name"],
            None if row["ic_research70"] is None else round(row["ic_research70"], 4),
            None if row["ic_validation30"] is None else round(row["ic_validation30"], 4),
        ))
    for book in ("H1_ML", "H1_TSMOM"):
        s = out[book]["sleeve"]
        print("%s raw=%.1f%% net=%.1f%% cost/yr=%.1f%% n/yr=%.0f L/S=%d/%d longMean=%s shortMean=%s streak=%d cost>move=%.1f%%" % (
            book, 100 * (s["raw_twr"] or 0), 100 * (s["net_twr"] or 0),
            100 * out[book]["cost_per_year"], out[book]["trades_per_year"],
            s["long_n"], s["short_n"],
            None if s["long_mean_net"] is None else round(s["long_mean_net"], 4),
            None if s["short_mean_net"] is None else round(s["short_mean_net"], 4),
            s["max_same_side"],
            100 * (out[book]["share_cost_gt_abs_raw"] or 0),
        ))
        print("  path", {k: (None if v is None else (round(v, 4) if isinstance(v, float) else v))
                         for k, v in out[book]["path"].items()})
        print("  ceiling", {k: (None if v is None else (round(v, 4) if isinstance(v, float) else v))
                            for k, v in out[book]["ceiling"].items() if k != "note"})
        print("  session", {k: "n=%s twr=%s hit=%s" % (
            v["n"], None if v["net_twr"] is None else round(v["net_twr"], 3),
            None if v["hit"] is None else round(v["hit"], 2),
        ) for k, v in out[book]["entry_session"].items()})
        print("  year", {k: None if v["net_twr"] is None else round(v["net_twr"], 3)
                         for k, v in out[book]["year"].items()})
        print("  last month n=%s twr=%s L=%s" % (
            out[book]["last_month_diagnostic"]["n"],
            None if out[book]["last_month_diagnostic"]["twr"] is None else round(out[book]["last_month_diagnostic"]["twr"], 3),
            out[book]["last_month_diagnostic"]["long_n"],
        ))
    return out


if __name__ == "__main__":
    main()
