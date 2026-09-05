"""V30 runner — contract docs/research_engine/V30_MT5_US_XS_CONTRACT.md. Everything below is fixed by the contract; no knobs."""
from __future__ import print_function

import csv
import json
import os
import time

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_ml_v25 import LGBM_PARAMS
from research_engine.cn_a_share_ml_v25.features import cs_rank_row, ranked_row
from research_engine.mt5_xs_v30 import CACHE, DATA, DATASET_ID, OUT, ensure

TAG = "V30"
HOLD = 20
Q = 0.20
MIN_HIST = 270
MIN_PRICE = 5.0
FIRST_PRED = "2006-01-03"
TRAIN_START = "2004-01-02"
REFIT_EVERY = 240
EMBARGO = HOLD + 1
TRAIN_STRIDE = 5
RESEARCH = ("2006-01-03", "2019-12-31")
VALIDATION = ("2020-01-02", "2026-08-28")
BLOCKS = (("2008-01-01", "2010-12-31"), ("2011-01-01", "2013-12-31"), ("2014-01-01", "2016-12-31"), ("2017-01-01", "2019-12-31"), ("2020-01-02", "2026-08-28"))
SLIP = 0.0005
FEATURES = ("REV_20", "MOM_250_20", "NEG_VOL_60", "NEG_VOL_120", "NEG_LOG_AMT_20", "VOLU_RATIO_20_120", "NEG_MAX_RET_20")


# ------------------------------------------------------------------ panel
def load_panel():
    specs = json.load(open(os.path.join(DATA, "specs.json"), encoding="utf-8"))
    specs = [s for s in specs if s["n_bars"] and s["trade_mode"] == 4]
    rows = {}
    dates = set()
    for s in specs:
        with open(os.path.join(DATA, s["file"]), encoding="utf-8") as fh:
            r = [x for x in csv.DictReader(fh)]
        rows[s["mt5_symbol"]] = r
        dates.update(x["timestamp_utc"][:10] for x in r)
    dates = sorted(dates)
    dix = dict((d, i) for i, d in enumerate(dates))
    syms = [s["mt5_symbol"] for s in specs]
    T, N = len(dates), len(syms)
    P = dict((k, np.full((T, N), np.nan, dtype=np.float32)) for k in ("open", "high", "low", "close", "vol", "spread_pct"))
    for j, s in enumerate(specs):
        pt = s["point"]
        for x in rows[s["mt5_symbol"]]:
            i = dix[x["timestamp_utc"][:10]]
            c = float(x["close"])
            P["open"][i, j], P["high"][i, j], P["low"][i, j], P["close"][i, j] = float(x["open"]), float(x["high"]), float(x["low"]), c
            P["vol"][i, j] = float(x["tick_volume"])
            P["spread_pct"][i, j] = float(x["spread"]) * pt / c if c > 0 else np.nan
    P["dates"], P["symbols"], P["specs"] = dates, syms, specs
    P["swap_long"] = np.array([s["swap_long"] for s in specs], dtype=np.float64) / 100.0   # annual, negative = pay
    P["swap_short"] = np.array([s["swap_short"] for s in specs], dtype=np.float64) / 100.0
    P["spread_now"] = np.array([(s["spread_points_now"] * s["point"] / s["bid"]) if s["bid"] else 0.002 for s in specs], dtype=np.float64)
    print(TAG, "panel", T, "x", N, dates[0], dates[-1], flush=True)
    return P


def _roll_mean(x, w):
    out = np.full_like(x, np.nan)
    c = np.nancumsum(np.where(np.isfinite(x), x, 0.0), axis=0)
    n = np.cumsum(np.isfinite(x), axis=0)
    out[w - 1:] = (c[w - 1:] - np.vstack([np.zeros((1, x.shape[1])), c[:-w]])) / np.maximum(1, n[w - 1:] - np.vstack([np.zeros((1, x.shape[1])), n[:-w]]))
    return out


def _roll_std(x, w):
    m = _roll_mean(x, w)
    m2 = _roll_mean(x * x, w)
    return np.sqrt(np.maximum(0.0, m2 - m * m))


def _roll_max(x, w):
    out = np.full_like(x, np.nan)
    for i in range(w - 1, x.shape[0]):
        out[i] = np.nanmax(x[i - w + 1:i + 1], axis=0)
    return out


def build_features(P):
    ensure()
    path = os.path.join(CACHE, "features.npz")
    if os.path.isfile(path):
        z = np.load(path)
        return dict((k, z[k]) for k in FEATURES)
    c = P["close"].astype(np.float64)
    ret = np.full_like(c, np.nan)
    ret[1:] = c[1:] / c[:-1] - 1.0
    f = {}
    f["REV_20"] = -(c / np.vstack([np.full((20, c.shape[1]), np.nan), c[:-20]]) - 1.0)
    f["MOM_250_20"] = np.vstack([np.full((20, c.shape[1]), np.nan), c[:-20]]) / np.vstack([np.full((250, c.shape[1]), np.nan), c[:-250]]) - 1.0
    f["NEG_VOL_60"] = -_roll_std(ret, 60)
    f["NEG_VOL_120"] = -_roll_std(ret, 120)
    amt = P["vol"].astype(np.float64) * c
    f["NEG_LOG_AMT_20"] = -np.log(np.maximum(1e-9, _roll_mean(amt, 20)))
    f["VOLU_RATIO_20_120"] = _roll_mean(P["vol"].astype(np.float64), 20) / np.maximum(1e-9, _roll_mean(P["vol"].astype(np.float64), 120))
    f["NEG_MAX_RET_20"] = -_roll_max(ret, 20)
    f = dict((k, v.astype(np.float32)) for k, v in f.items())
    np.savez(path, **f)
    return f


def eligibility(P):
    c = P["close"]
    hist = np.cumsum(np.isfinite(c).astype(np.int32), axis=0)
    elig = np.isfinite(c) & (P["vol"] > 0) & (hist >= MIN_HIST) & (c >= MIN_PRICE)
    xok = np.isfinite(P["open"]) & (P["open"] > 0)
    return elig, xok


def forward_open(P):
    o = P["open"].astype(np.float64)
    fwd = np.full_like(o, np.nan)
    fwd[:-HOLD - 1] = o[HOLD + 1:] / o[1:-HOLD] - 1.0
    return fwd


# ------------------------------------------------------------------ model
def _idx(dates, day):
    for i, d in enumerate(dates):
        if d >= day:
            return i
    return len(dates)


def build_scores(P, feats, elig, xok, fwd):
    import lightgbm as lgb

    dates = P["dates"]
    T, N = len(dates), len(P["symbols"])
    i_first = _idx(dates, FIRST_PRED)
    i_res = _idx(dates, TRAIN_START)
    scores = np.full((T, N), np.nan, dtype=np.float32)
    refits = []
    t = i_first
    while t < T:
        s = t
        cutoff = s - EMBARGO
        Xs, ys = [], []
        for g in range(i_res, cutoff + 1, TRAIN_STRIDE):
            m = elig[g] & np.isfinite(fwd[g]) & xok[g + 1]
            if m.sum() < 50:
                continue
            X = ranked_row(feats, g, m, FEATURES)
            y = cs_rank_row(fwd[g], m) - np.float32(0.5)
            k = m & np.isfinite(y)
            Xs.append(X[k])
            ys.append(y[k])
        model = lgb.LGBMRegressor(**LGBM_PARAMS)
        model.fit(np.concatenate(Xs), np.concatenate(ys))
        end = min(T, s + REFIT_EVERY)
        for u in range(s, end):
            m = elig[u]
            if m.sum() < 50:
                continue
            X = ranked_row(feats, u, m, FEATURES)
            r = np.where(m)[0]
            scores[u, r] = model.predict(X[r]).astype(np.float32)
        refits.append({"fit_at": dates[s], "rows": int(sum(len(y) for y in ys)), "scored_through": dates[end - 1]})
        print(TAG, "refit", dates[s], "rows", refits[-1]["rows"], flush=True)
        t = end
    np.save(os.path.join(OUT, "SCORES_V30.npy"), scores)
    return scores, refits


# ------------------------------------------------------------------ books
def _cost_side(P, t_in, t_out, j, side):
    """Round-trip cost fraction for one name: half-spread each side + slippage each side + swap over calendar days."""
    sp = np.nanmedian(P["spread_pct"][max(0, t_in - 60):t_in, j])
    sp = 0.0 if not np.isfinite(sp) else float(sp)
    sp = max(sp, P["spread_now"][j])  # historical bars often carry spread 0; today's quoted spread is the floor
    rt = sp + 2 * SLIP
    import datetime as dt
    d_in, d_out = dt.date.fromisoformat(P["dates"][t_in]), dt.date.fromisoformat(P["dates"][t_out])
    cal_days = (d_out - d_in).days
    swap = (P["swap_long"][j] if side > 0 else P["swap_short"][j]) * cal_days / 365.0   # negative = pay
    return rt - swap  # swap negative -> adds cost


def books(P, scores, elig, xok, start, end):
    dates = P["dates"]
    T = len(dates)
    i0, i1 = _idx(dates, start), _idx(dates, end)
    o = P["open"].astype(np.float64)
    eq_lo, eq_ls = 1.0, 1.0
    trades = []
    t = i0
    while t + HOLD + 1 < T and t <= i1:
        s = scores[t]
        m = elig[t] & np.isfinite(s) & xok[t + 1]
        idx = np.where(m)[0]
        if len(idx) < 50:
            t += 1
            continue
        order = idx[np.argsort(-s[idx], kind="mergesort")]
        k = max(1, int(round(Q * len(idx))))
        longs, shorts = order[:k], order[-k:]
        t_in, t_out = t + 1, t + 1 + HOLD
        def leg(js, side):
            rets = []
            for j in js:
                if not (np.isfinite(o[t_in, j]) and np.isfinite(o[t_out, j]) and o[t_in, j] > 0):
                    rets.append(0.0)  # unfilled -> cash
                    continue
                r = (o[t_out, j] / o[t_in, j] - 1.0) * side
                rets.append(r - _cost_side(P, t_in, t_out, j, side))
            return float(np.mean(rets))
        r_long = leg(longs, +1)
        r_short = leg(shorts, -1)
        # EW benchmark gross over the same window
        allj = idx
        ew = float(np.nanmean([(o[t_out, j] / o[t_in, j] - 1.0) for j in allj if np.isfinite(o[t_in, j]) and np.isfinite(o[t_out, j]) and o[t_in, j] > 0]))
        r_ls = r_long + r_short
        eq_lo *= 1.0 + r_long
        eq_ls *= 1.0 + r_ls
        trades.append({"signal": dates[t], "entry": dates[t_in], "exit": dates[t_out], "n": int(k), "lo_ret": r_long, "short_leg_ret": r_short, "ls_ret": r_ls, "ew_ret": ew,
                       "lo_minus_ew": r_long - ew, "eq_lo": eq_lo, "eq_ls": eq_ls})
        t = t_out
    def summ(key, eqk):
        x = np.array([tr[key] for tr in trades])
        yrs = max(1e-9, len(trades) * HOLD / 252.0)
        eq = np.array([tr[eqk] for tr in trades])
        dd = float(np.min(eq / np.maximum.accumulate(np.concatenate([[1.0], eq]))[1:] - 1.0)) if len(eq) else None
        return {"n_periods": len(trades), "total": float(eq[-1] - 1.0) if len(eq) else None, "cagr": float(eq[-1] ** (1 / yrs) - 1.0) if len(eq) else None,
                "mean_per_period": float(x.mean()) if len(x) else None, "t": float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 else None,
                "hit": float((x > 0).mean()) if len(x) else None, "maxdd": dd}
    return {"trades": trades, "LO20": summ("lo_ret", "eq_lo"), "LS20": summ("ls_ret", "eq_ls"), "LO_minus_EW": summ("lo_minus_ew", "eq_lo")}


def spread_t(P, scores, elig, xok, fwd, start, end):
    """Gross long-minus-short mean forward spread on every session (overlapping, t on non-overlapping every HOLD sessions)."""
    dates = P["dates"]
    i0, i1 = _idx(dates, start), _idx(dates, end)
    vals = []
    for t in range(i0, min(i1, len(dates) - HOLD - 1), HOLD):
        s = scores[t]
        m = elig[t] & np.isfinite(s) & np.isfinite(fwd[t]) & xok[t + 1]
        idx = np.where(m)[0]
        if len(idx) < 50:
            continue
        order = idx[np.argsort(-s[idx], kind="mergesort")]
        k = max(1, int(round(Q * len(idx))))
        vals.append(float(np.mean(fwd[t, order[:k]]) - np.mean(fwd[t, order[-k:]])))
    x = np.array(vals)
    return {"n": len(x), "mean": float(x.mean()) if len(x) else None, "t": float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 else None}


def main():
    ensure()
    t0 = time.time()
    P = load_panel()
    feats = build_features(P)
    elig, xok = eligibility(P)
    fwd = forward_open(P)
    scores, refits = build_scores(P, feats, elig, xok, fwd)
    res = {"dataset": DATASET_ID, "contract": "V30_MT5_US_XS_CONTRACT.md", "features": FEATURES, "params": LGBM_PARAMS, "refits": refits,
           "n_symbols": len(P["symbols"]), "n_dates": len(P["dates"]), "survivorship": "UPPER_BOUND_SURVIVORSHIP (current listing only)",
           "cost_model": {"half_spread_each_side": "60d median bar spread% / 2", "slippage_each_side": SLIP, "swap": "specs swap_long/swap_short annual % x calendar days/365"},
           "median_spread_pct": float(np.nanmedian(P["spread_pct"])), "swap_long_annual_median": float(np.median(P["swap_long"])), "swap_short_annual_median": float(np.median(P["swap_short"]))}
    res["research"] = books(P, scores, elig, xok, *RESEARCH)
    res["validation"] = books(P, scores, elig, xok, *VALIDATION)
    res["spread_t_research"] = spread_t(P, scores, elig, xok, fwd, *RESEARCH)
    res["spread_t_validation"] = spread_t(P, scores, elig, xok, fwd, *VALIDATION)
    res["rolling"] = []
    for a, b in BLOCKS:
        bk = books(P, scores, elig, xok, a, b)
        res["rolling"].append({"block": [a, b], "LS20_total": bk["LS20"]["total"], "LO20_total": bk["LO20"]["total"], "n": bk["LS20"]["n_periods"]})
    for key in ("research", "validation"):
        with open(os.path.join(OUT, "EQUITY_%s.csv" % key.upper()), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(res[key]["trades"][0].keys()) if res[key]["trades"] else ["signal"])
            w.writeheader()
            w.writerows(res[key]["trades"])
        res[key] = dict((k, v) for k, v in res[key].items() if k != "trades")
    v = res["validation"]
    n_pos = sum(1 for r in res["rolling"] if r["LS20_total"] is not None and r["LS20_total"] > 0)
    gates = {"G1_val_LS20_capital_gt_0": bool(v["LS20"]["total"] is not None and v["LS20"]["total"] > 0),
             "G2_val_spread_t_ge_3": bool(res["spread_t_validation"]["t"] is not None and res["spread_t_validation"]["t"] >= 3),
             "G3_rolling_ge_4_of_5": n_pos >= 4, "G4_research_LS20_gt_0": bool(res["research"]["LS20"]["total"] is not None and res["research"]["LS20"]["total"] > 0)}
    passed = all(gates.values())
    res["gates"], res["rolling_positive"] = gates, n_pos
    res["label"] = "MT5_US_XS_PRICE_V30_LEVEL1_UPPER_BOUND" if passed else "MT5_US_XS_PRICE_V30_NO_CANDIDATE"
    res["elapsed_s"] = round(time.time() - t0, 1)
    dump_json(os.path.join(OUT, "RESULTS.json"), res)
    dump_json(os.path.join(OUT, "DECISION.json"), {"label": res["label"], "gates": gates, "validation_LS20": v["LS20"], "validation_LO20": v["LO20"],
                                                   "validation_LO_minus_EW": v["LO_minus_EW"], "spread_t_validation": res["spread_t_validation"],
                                                   "rolling": res["rolling"], "survivorship": res["survivorship"], "paper": False, "orders_sent": False})
    print(TAG, "DONE", res["label"], json.dumps(gates), "val LS20", v["LS20"], "val LO20", v["LO20"], flush=True)


if __name__ == "__main__":
    main()
