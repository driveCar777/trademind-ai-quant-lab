"""V32 runner — contract docs/research_engine/V32_MT5_MACRO_POOLED_CONTRACT.md. Everything fixed; no knobs."""
from __future__ import print_function

import csv
import datetime as dt
import json
import os
import time

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_ml_v25 import LGBM_PARAMS
from research_engine.mt5_macro_v32 import CACHE, DATA, DATASET_ID, OUT, ensure

TAG = "V32"
HOLD = 5
MIN_HIST = 270
MIN_CS = 20
FIRST_PRED = "2006-01-03"
TRAIN_START = "2003-01-02"
REFIT_EVERY = 250
EMBARGO = HOLD + 1
RESEARCH = ("2006-01-03", "2019-12-31")
VALIDATION = ("2020-01-02", "2026-08-28")
BLOCKS = (("2008-01-01", "2010-12-31"), ("2011-01-01", "2013-12-31"), ("2014-01-01", "2016-12-31"), ("2017-01-01", "2019-12-31"), ("2020-01-02", "2026-08-28"))
SLIP = 0.0002
DROP = ("VIX", "WTICrude", "SI_FUTURE", "GOLD_FUTURE", "CrudeTEST", "SPAIN35")
FEATURES = ("R1", "R5", "R21", "R63", "R126", "R252", "VOLRATIO_21_252", "RANGEPOS_63", "CS_R21", "CS_R252")


def _idx(dates, day):
    for i, d in enumerate(dates):
        if d >= day:
            return i
    return len(dates)


# ------------------------------------------------------------------ panel
def load_panel():
    specs = json.load(open(os.path.join(DATA, "specs.json"), encoding="utf-8"))
    specs = [s for s in specs if s["n_bars"] and s["trade_mode"] == 4 and s["mt5_symbol"] not in DROP]
    rows, dates = {}, set()
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
    P["spread_now"] = np.array([(s["spread_points_now"] * s["point"] / s["bid"]) if s["bid"] else 0.001 for s in specs], dtype=np.float64)
    P["swap_mode"] = np.array([s["swap_mode"] for s in specs])
    P["swap_long"] = np.array([s["swap_long"] for s in specs], dtype=np.float64)
    P["swap_short"] = np.array([s["swap_short"] for s in specs], dtype=np.float64)
    P["point"] = np.array([s["point"] for s in specs], dtype=np.float64)
    P["roll3"] = np.array([s.get("swap_rollover3days", 3) for s in specs])
    print(TAG, "panel", T, "x", N, dates[0], dates[-1], flush=True)
    return P


def _lag(x, k):
    out = np.full_like(x, np.nan)
    out[k:] = x[:-k]
    return out


def _roll_std(x, w):
    out = np.full_like(x, np.nan)
    for i in range(w - 1, x.shape[0]):
        out[i] = np.nanstd(x[i - w + 1:i + 1], axis=0)
    return out


def _roll_minmax(x, w):
    mn, mx = np.full_like(x, np.nan), np.full_like(x, np.nan)
    for i in range(w - 1, x.shape[0]):
        mn[i], mx[i] = np.nanmin(x[i - w + 1:i + 1], axis=0), np.nanmax(x[i - w + 1:i + 1], axis=0)
    return mn, mx


def _cs_rank(x, m):
    out = np.full_like(x, np.nan)
    for t in range(x.shape[0]):
        k = m[t] & np.isfinite(x[t])
        n = k.sum()
        if n >= MIN_CS:
            r = np.empty(n)
            r[np.argsort(x[t, k], kind="mergesort")] = np.arange(n)
            out[t, k] = r / max(1, n - 1)
    return out


def build_features(P, elig):
    ensure()
    path = os.path.join(CACHE, "features.npz")
    if os.path.isfile(path):
        z = np.load(path)
        return dict((k, z[k]) for k in FEATURES), z["vol63"]
    c = P["close"].astype(np.float64)
    ret = np.full_like(c, np.nan)
    ret[1:] = c[1:] / c[:-1] - 1.0
    vol63 = _roll_std(ret, 63)
    vol21 = _roll_std(ret, 21)
    vol252 = _roll_std(ret, 252)
    f = {}
    for h in (1, 5, 21, 63, 126, 252):
        f["R%d" % h] = (c / _lag(c, h) - 1.0) / np.maximum(1e-6, vol63 * np.sqrt(h))
    f["VOLRATIO_21_252"] = vol21 / np.maximum(1e-9, vol252)
    mn, mx = _roll_minmax(c, 63)
    f["RANGEPOS_63"] = (c - mn) / np.maximum(1e-9, mx - mn)
    f["CS_R21"] = _cs_rank(f["R21"], elig)
    f["CS_R252"] = _cs_rank(f["R252"], elig)
    f = dict((k, v.astype(np.float32)) for k, v in f.items())
    np.savez(path, vol63=vol63.astype(np.float32), **f)
    return f, vol63.astype(np.float32)


def eligibility(P):
    c = P["close"]
    hist = np.cumsum(np.isfinite(c).astype(np.int32), axis=0)
    elig = np.isfinite(c) & (P["vol"] > 0) & (hist >= MIN_HIST)
    xok = np.isfinite(P["open"]) & (P["open"] > 0)
    return elig, xok


def forward_open(P):
    o = P["open"].astype(np.float64)
    fwd = np.full_like(o, np.nan)
    fwd[:-HOLD - 1] = o[HOLD + 1:] / o[1:-HOLD] - 1.0
    return fwd


# ------------------------------------------------------------------ model
def build_scores(P, feats, vol63, elig, xok, fwd):
    import lightgbm as lgb

    dates = P["dates"]
    T, N = len(dates), len(P["symbols"])
    X_all = np.stack([feats[k] for k in FEATURES], axis=-1)  # T x N x F
    y_all = fwd / np.maximum(1e-6, vol63.astype(np.float64) * np.sqrt(HOLD))
    scores = np.full((T, N), np.nan, dtype=np.float32)
    refits, t = [], _idx(dates, FIRST_PRED)
    i_res = _idx(dates, TRAIN_START)
    while t < T:
        cutoff = t - EMBARGO
        m = elig[i_res:cutoff + 1] & np.isfinite(y_all[i_res:cutoff + 1]) & xok[i_res + 1:cutoff + 2] & np.all(np.isfinite(X_all[i_res:cutoff + 1]), axis=-1)
        X, y = X_all[i_res:cutoff + 1][m], np.clip(y_all[i_res:cutoff + 1][m], -5, 5)
        model = lgb.LGBMRegressor(**LGBM_PARAMS)
        model.fit(X, y)
        end = min(T, t + REFIT_EVERY)
        for u in range(t, end):
            k = elig[u] & np.all(np.isfinite(X_all[u]), axis=-1)
            if k.sum() < MIN_CS:
                continue
            scores[u, k] = model.predict(X_all[u][k]).astype(np.float32)
        refits.append({"fit_at": dates[t], "rows": int(len(y)), "scored_through": dates[end - 1]})
        print(TAG, "refit", dates[t], "rows", len(y), flush=True)
        t = end
    np.save(os.path.join(OUT, "SCORES_V32.npy"), scores)
    return scores, refits


# ------------------------------------------------------------------ costs & books
def _swap_frac(P, j, side, t_in, t_out):
    """Fraction of notional paid (negative) for holding side over [t_in, t_out] sessions; current swap applied (history unavailable)."""
    nights = 0.0
    for u in range(t_in, t_out):
        d = dt.date.fromisoformat(P["dates"][u])
        nights += 3.0 if (d.isoweekday() == int(P["roll3"][j])) else 1.0
    sw = P["swap_long"][j] if side > 0 else P["swap_short"][j]
    if P["swap_mode"][j] == 1:
        return sw * P["point"][j] / float(P["open"][t_in, j]) * nights
    if P["swap_mode"][j] == 5:
        return sw / 100.0 * nights / 365.0
    return 0.0


def _cost(P, t_in, t_out, j, side):
    sp = np.nanmedian(P["spread_pct"][max(0, t_in - 60):t_in, j])
    sp = 0.0 if not np.isfinite(sp) else float(sp)
    sp = max(sp, P["spread_now"][j])
    return sp + 2 * SLIP - _swap_frac(P, j, side, t_in, t_out)  # swap negative -> cost


def books(P, scores, vol63, elig, xok, start, end):
    dates = P["dates"]
    T = len(dates)
    i0, i1 = _idx(dates, start), _idx(dates, end)
    o = P["open"].astype(np.float64)
    eq_ls, eq_lo, trades, t = 1.0, 1.0, [], i0
    while t + HOLD + 1 < T and t <= i1:
        s = scores[t]
        m = elig[t] & np.isfinite(s) & xok[t + 1] & np.isfinite(vol63[t]) & (vol63[t] > 0)
        idx = np.where(m)[0]
        if len(idx) < MIN_CS:
            t += 1
            continue
        order = idx[np.argsort(-s[idx], kind="mergesort")]
        k = max(1, len(idx) // 3)
        longs, shorts = order[:k], order[-k:]
        t_in, t_out = t + 1, t + 1 + HOLD
        def leg(js, side):
            w = 1.0 / np.maximum(1e-6, vol63[t, js].astype(np.float64))
            w = np.minimum(w, 3.0 * w.mean())
            w = w / w.sum()
            r = 0.0
            for wj, j in zip(w, js):
                if not (np.isfinite(o[t_in, j]) and np.isfinite(o[t_out, j]) and o[t_in, j] > 0):
                    continue
                r += wj * ((o[t_out, j] / o[t_in, j] - 1.0) * side - _cost(P, t_in, t_out, j, side))
            return float(r)
        r_long, r_short = leg(longs, +1), leg(shorts, -1)
        ew = float(np.nanmean([(o[t_out, j] / o[t_in, j] - 1.0) for j in idx if np.isfinite(o[t_in, j]) and np.isfinite(o[t_out, j]) and o[t_in, j] > 0]))
        r_ls = r_long + r_short
        eq_ls *= 1.0 + r_ls
        eq_lo *= 1.0 + r_long
        trades.append({"signal": dates[t], "entry": dates[t_in], "exit": dates[t_out], "n_side": int(k), "n_cs": int(len(idx)), "lo_ret": r_long, "short_leg_ret": r_short,
                       "ls_ret": r_ls, "ew_ret": ew, "lo_minus_ew": r_long - ew, "eq_ls": eq_ls, "eq_lo": eq_lo})
        t = t_out
    def summ(key, eqk):
        x = np.array([tr[key] for tr in trades])
        yrs = max(1e-9, len(trades) * HOLD / 252.0)
        eq = np.array([tr[eqk] for tr in trades])
        dd = float(np.min(eq / np.maximum.accumulate(np.concatenate([[1.0], eq]))[1:] - 1.0)) if len(eq) else None
        return {"n_periods": len(trades), "total": float(eq[-1] - 1.0) if len(eq) else None, "cagr": float(eq[-1] ** (1 / yrs) - 1.0) if len(eq) else None,
                "mean_per_period": float(x.mean()) if len(x) else None, "t": float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 else None,
                "hit": float((x > 0).mean()) if len(x) else None, "maxdd": dd}
    return {"trades": trades, "LS": summ("ls_ret", "eq_ls"), "LO": summ("lo_ret", "eq_lo"), "LO_minus_EW": summ("lo_minus_ew", "eq_lo")}


def spread_t(P, scores, vol63, elig, xok, fwd, start, end):
    dates = P["dates"]
    i0, i1 = _idx(dates, start), _idx(dates, end)
    vals = []
    for t in range(i0, min(i1, len(dates) - HOLD - 1), HOLD):
        s = scores[t]
        m = elig[t] & np.isfinite(s) & np.isfinite(fwd[t]) & xok[t + 1]
        idx = np.where(m)[0]
        if len(idx) < MIN_CS:
            continue
        order = idx[np.argsort(-s[idx], kind="mergesort")]
        k = max(1, len(idx) // 3)
        vals.append(float(np.mean(fwd[t, order[:k]]) - np.mean(fwd[t, order[-k:]])))
    x = np.array(vals)
    return {"n": len(x), "mean": float(x.mean()) if len(x) else None, "t": float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 else None}


def main():
    ensure()
    t0 = time.time()
    P = load_panel()
    elig, xok = eligibility(P)
    feats, vol63 = build_features(P, elig)
    fwd = forward_open(P)
    scores, refits = build_scores(P, feats, vol63, elig, xok, fwd)
    res = {"dataset": DATASET_ID, "contract": "V32_MT5_MACRO_POOLED_CONTRACT.md", "features": FEATURES, "params": LGBM_PARAMS, "refits": refits, "hold": HOLD,
           "n_symbols": len(P["symbols"]), "symbols": P["symbols"], "n_dates": len(P["dates"]),
           "cost_model": {"spread": "60d median bar spread% floored at current quote", "slippage_each_side": SLIP, "swap": "current swap applied to all history (no swap history available)"},
           "median_spread_pct": float(np.nanmedian(P["spread_pct"]))}
    res["research"] = books(P, scores, vol63, elig, xok, *RESEARCH)
    res["validation"] = books(P, scores, vol63, elig, xok, *VALIDATION)
    res["spread_t_research"] = spread_t(P, scores, vol63, elig, xok, fwd, *RESEARCH)
    res["spread_t_validation"] = spread_t(P, scores, vol63, elig, xok, fwd, *VALIDATION)
    res["rolling"] = []
    for a, b in BLOCKS:
        bk = books(P, scores, vol63, elig, xok, a, b)
        res["rolling"].append({"block": [a, b], "LS_total": bk["LS"]["total"], "LO_total": bk["LO"]["total"], "n": bk["LS"]["n_periods"]})
    for key in ("research", "validation"):
        with open(os.path.join(OUT, "EQUITY_%s.csv" % key.upper()), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(res[key]["trades"][0].keys()) if res[key]["trades"] else ["signal"])
            w.writeheader()
            w.writerows(res[key]["trades"])
        res[key] = dict((k, v) for k, v in res[key].items() if k != "trades")
    v = res["validation"]
    n_pos = sum(1 for r in res["rolling"] if r["LS_total"] is not None and r["LS_total"] > 0)
    gates = {"G1_val_LS_capital_gt_0": bool(v["LS"]["total"] is not None and v["LS"]["total"] > 0),
             "G2_val_spread_t_ge_3": bool(res["spread_t_validation"]["t"] is not None and res["spread_t_validation"]["t"] >= 3),
             "G3_rolling_ge_4_of_5": n_pos >= 4, "G4_research_LS_gt_0": bool(res["research"]["LS"]["total"] is not None and res["research"]["LS"]["total"] > 0)}
    passed = all(gates.values())
    res["gates"], res["rolling_positive"] = gates, n_pos
    res["label"] = "MT5_MACRO_POOLED_V32_LEVEL1" if passed else "MT5_MACRO_POOLED_V32_NO_CANDIDATE"
    res["elapsed_s"] = round(time.time() - t0, 1)
    dump_json(os.path.join(OUT, "RESULTS.json"), res)
    dump_json(os.path.join(OUT, "DECISION.json"), {"label": res["label"], "gates": gates, "validation_LS": v["LS"], "validation_LO": v["LO"], "validation_LO_minus_EW": v["LO_minus_EW"],
                                                   "spread_t_validation": res["spread_t_validation"], "spread_t_research": res["spread_t_research"], "rolling": res["rolling"],
                                                   "paper": False, "orders_sent": False})
    print(TAG, "DONE", res["label"], json.dumps(gates), "val LS", v["LS"], "val spread", res["spread_t_validation"], flush=True)


if __name__ == "__main__":
    main()
