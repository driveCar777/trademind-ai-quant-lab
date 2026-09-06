"""V31 runner — contract docs/research_engine/V31_CN_FUTURES_XS_CONTRACT.md. Single read."""
from __future__ import print_function

import csv
import json
import os
import time

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_ml_v25 import LGBM_PARAMS
from research_engine.cn_a_share_ml_v25.features import cs_rank_row, ranked_row
from research_engine.cn_futures_v31 import (
    CACHE, COST_BPS_SIDE, DATASET_ID, EMBARGO, FEATURES, FIRST_PRED, HOLD, MIN_HIST, MIN_N,
    OUT, REFIT_EVERY, RESEARCH, ROLLING_BLOCKS, TRAIN_START, TRAIN_STRIDE, VALIDATION, ensure,
)
from research_engine.cn_futures_v31.pack import load_pack, roll_adjust_unit_test

TAG = "V31"


def _idx(dates, day):
    for i, d in enumerate(dates):
        if d >= day:
            return i
    return len(dates)


def _roll_mean(x, w):
    c = np.nancumsum(np.where(np.isfinite(x), x, 0.0), axis=0)
    n = np.cumsum(np.isfinite(x), axis=0)
    out = np.full_like(x, np.nan, dtype=np.float64)
    prev_c = np.vstack([np.zeros((1, x.shape[1])), c[:-w]])
    prev_n = np.vstack([np.zeros((1, x.shape[1])), n[:-w]])
    cnt = n[w - 1:] - prev_n
    out[w - 1:] = np.where(cnt > 0, (c[w - 1:] - prev_c) / np.maximum(cnt, 1), np.nan)
    return out


def _roll_std(x, w):
    m = _roll_mean(x, w)
    m2 = _roll_mean(x * x, w)
    return np.sqrt(np.maximum(0.0, m2 - m * m))


def build_features(P):
    path = os.path.join(CACHE, "features_v31.npz")
    if os.path.isfile(path):
        z = np.load(path)
        return dict((k, z[k]) for k in FEATURES)
    c = P["close"].astype(np.float64)
    oi = P["oi"].astype(np.float64)
    vol = P["volume"].astype(np.float64)
    ret = np.full_like(c, np.nan)
    ret[1:] = np.where((c[:-1] > 0) & np.isfinite(c[1:]) & np.isfinite(c[:-1]), c[1:] / c[:-1] - 1.0, np.nan)
    f = {}
    r20 = np.vstack([np.full((20, c.shape[1]), np.nan), c[:-20]])
    r60 = np.vstack([np.full((60, c.shape[1]), np.nan), c[:-60]])
    f["REV_20"] = -(c / r20 - 1.0)
    f["XS_MOM_60_20"] = (c / r60 - 1.0) - (c / r20 - 1.0)
    f["NEG_VOL_60"] = -_roll_std(ret, 60)
    oi20 = np.vstack([np.full((20, c.shape[1]), np.nan), oi[:-20]])
    f["OI_CHG_20"] = np.where((oi20 > 0) & np.isfinite(oi), oi / oi20 - 1.0, np.nan)
    f["VOLU_RATIO_20_120"] = _roll_mean(vol, 20) / np.maximum(1e-9, _roll_mean(vol, 120))
    amt = vol * c
    f["NEG_LOG_AMT_20"] = -np.log(np.maximum(1e-9, _roll_mean(amt, 20)))
    f["TERM_SLOPE"] = P["term_slope"].astype(np.float64)
    ts = f["TERM_SLOPE"]
    f["BASIS_MOM_20"] = ts - np.vstack([np.full((20, ts.shape[1]), np.nan), ts[:-20]])
    f = dict((k, v.astype(np.float32)) for k, v in f.items())
    np.savez(path, **f)
    return f


def eligibility(P):
    c = P["close"]
    hist = np.cumsum(np.isfinite(c).astype(np.int32), axis=0)
    oi20 = _roll_mean(P["oi"].astype(np.float64), 20)
    elig = np.isfinite(c) & (hist >= MIN_HIST) & np.isfinite(oi20) & np.isfinite(P["fwd_same"])
    # listing-year: hist already >= 250 covers first year
    # liquidity: 20d OI >= cross-section 20th percentile
    for t in range(elig.shape[0]):
        m = elig[t]
        if m.sum() < 5:
            continue
        q = np.nanpercentile(oi20[t, m], 20)
        elig[t] = m & (oi20[t] >= q)
    xok = np.isfinite(P["fwd_same"])
    return elig, xok


def build_scores(P, feats, elig, fwd):
    import lightgbm as lgb

    dates = P["dates"]
    T, N = len(dates), len(P["products"])
    i_first = _idx(dates, FIRST_PRED)
    i_train = _idx(dates, TRAIN_START)
    i_res_end = _idx(dates, RESEARCH[1])
    if dates[i_res_end] > RESEARCH[1]:
        i_res_end -= 1
    scores = np.full((T, N), np.nan, dtype=np.float32)
    i_val_end = min(_idx(dates, VALIDATION[1]), T - 1)
    refit_at = list(range(i_first, i_res_end + 1, REFIT_EVERY))
    if not refit_at:
        refit_at = [i_first]
    meta = []
    for k, s in enumerate(refit_at):
        cutoff = s - EMBARGO
        Xs, ys = [], []
        for g in range(i_train, cutoff + 1, TRAIN_STRIDE):
            m = elig[g] & np.isfinite(fwd[g])
            if int(m.sum()) < MIN_N:
                continue
            X = ranked_row(feats, g, m, FEATURES)
            y = cs_rank_row(fwd[g], m) - np.float32(0.5)
            keep = m & np.isfinite(y)
            Xs.append(X[keep])
            ys.append(y[keep])
        if not Xs:
            print(TAG, "skip empty refit", dates[s], flush=True)
            continue
        model = lgb.LGBMRegressor(**LGBM_PARAMS)
        model.fit(np.concatenate(Xs), np.concatenate(ys))
        s_end = refit_at[k + 1] - 1 if k + 1 < len(refit_at) else i_val_end
        for u in range(s, s_end + 1):
            m = elig[u]
            if int(m.sum()) < MIN_N:
                continue
            X = ranked_row(feats, u, m, FEATURES)
            r = np.where(m)[0]
            scores[u, r] = model.predict(X[r]).astype(np.float32)
        meta.append({"fit_at": dates[s], "rows": int(sum(len(y) for y in ys)), "scored_through": dates[s_end]})
        print(TAG, "refit", k + 1, "/", len(refit_at), dates[s], "rows", meta[-1]["rows"], "->", dates[s_end], flush=True)
    np.save(os.path.join(OUT, "SCORES_V31.npy"), scores)
    return scores, meta


COST = COST_BPS_SIDE / 1e4 * 2  # round-trip per name


def books(P, scores, elig, start, end):
    dates = P["dates"]
    T = len(dates)
    i0, i1 = _idx(dates, start), min(_idx(dates, end), T - 1)
    fwd = P["fwd_same"].astype(np.float64)
    eq_lo, eq_ls = 1.0, 1.0
    trades = []
    t = i0
    while t + HOLD + 1 < T and t <= i1:
        s = scores[t]
        m = elig[t] & np.isfinite(s) & np.isfinite(fwd[t])
        idx = np.where(m)[0]
        if len(idx) < MIN_N:
            t += 1
            continue
        order = idx[np.argsort(-s[idx], kind="mergesort")]
        k = max(1, len(idx) // 3)
        longs, shorts = order[:k], order[-k:]
        r_long = float(np.mean(fwd[t, longs]) - COST)
        r_short = float(np.mean(-fwd[t, shorts]) - COST)
        ew = float(np.mean(fwd[t, idx]))
        r_ls = r_long + r_short
        eq_lo *= 1.0 + r_long
        eq_ls *= 1.0 + r_ls
        trades.append({"signal": dates[t], "n": int(k), "n_elig": int(len(idx)), "lo_ret": r_long, "short_leg_ret": r_short,
                       "ls_ret": r_ls, "ew_ret": ew, "lo_minus_ew": r_long - ew, "eq_lo": eq_lo, "eq_ls": eq_ls})
        t = t + 1 + HOLD
    def summ(key, eqk):
        x = np.array([tr[key] for tr in trades])
        yrs = max(1e-9, len(trades) * (HOLD + 1) / 242.0)
        eq = np.array([tr[eqk] for tr in trades])
        dd = float(np.min(eq / np.maximum.accumulate(np.concatenate([[1.0], eq]))[1:] - 1.0)) if len(eq) else None
        years = {}
        for tr in trades:
            years.setdefault(tr["signal"][:4], []).append(tr[key])
        by_year = dict((y, float(np.prod([1 + a for a in v]) - 1)) for y, v in sorted(years.items()))
        return {"n_periods": len(trades), "total": float(eq[-1] - 1.0) if len(eq) else None,
                "cagr": float(eq[-1] ** (1 / yrs) - 1.0) if len(eq) else None,
                "mean_per_period": float(x.mean()) if len(x) else None,
                "t": float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 else None,
                "hit": float((x > 0).mean()) if len(x) else None, "maxdd": dd, "by_year": by_year}
    return {"trades": trades, "LO": summ("lo_ret", "eq_lo"), "LS": summ("ls_ret", "eq_ls"), "LO_minus_EW": summ("lo_minus_ew", "eq_lo")}


def spread_t(P, scores, elig, start, end):
    dates = P["dates"]
    i0, i1 = _idx(dates, start), _idx(dates, end)
    fwd = P["fwd_same"]
    vals = []
    for t in range(i0, min(i1, len(dates) - HOLD - 1), HOLD + 1):
        s = scores[t]
        m = elig[t] & np.isfinite(s) & np.isfinite(fwd[t])
        idx = np.where(m)[0]
        if len(idx) < MIN_N:
            continue
        order = idx[np.argsort(-s[idx], kind="mergesort")]
        k = max(1, len(idx) // 3)
        vals.append(float(np.mean(fwd[t, order[:k]]) - np.mean(fwd[t, order[-k:]])))
    x = np.array(vals)
    return {"n": int(len(x)), "mean": float(x.mean()) if len(x) else None,
            "t": float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 else None}


def jump_diag(P, elig, start, end):
    dates = P["dates"]
    i0, i1 = _idx(dates, start), _idx(dates, end)
    a, b = [], []
    for t in range(i0, min(i1, len(dates) - HOLD - 1)):
        m = elig[t] & np.isfinite(P["fwd_same"][t]) & np.isfinite(P["fwd_continuous_DIAG"][t])
        if int(m.sum()) < MIN_N:
            continue
        a.append(float(np.nanmean(P["fwd_same"][t, m])))
        b.append(float(np.nanmean(P["fwd_continuous_DIAG"][t, m])))
    a, b = np.array(a), np.array(b)
    d = b - a
    return {"n": int(len(d)), "mean_same": float(a.mean()) if len(a) else None, "mean_continuous": float(b.mean()) if len(b) else None,
            "mean_jump_bias": float(d.mean()) if len(d) else None}


def corr_vs_ml1(v31_trades):
    """Pearson corr of V31 LS period returns vs V26.8 period returns, nearest signal within 5 calendar days."""
    path = os.path.join(os.path.dirname(OUT), "cn_a_share_ml_v25", "ML1_SCALED_UNIT_FULL_CONTRIB2K_MAIN_READ.json")
    if not os.path.isfile(path):
        return {"error": "ML1_V26_8_READ_MISSING"}
    ml = json.load(open(path, encoding="utf-8"))
    rows = (ml.get("research_trades") or []) + (ml.get("validation_trades") or [])
    if not rows or not v31_trades:
        return {"n": 0}
    import datetime as dt
    ml_d = [(dt.date.fromisoformat(x["signal_date"]), x["ret"]) for x in rows]
    xs, ys = [], []
    for tr in v31_trades:
        d = dt.date.fromisoformat(tr["signal"])
        best, bd = None, 99
        for md, r in ml_d:
            gap = abs((md - d).days)
            if gap < bd:
                bd, best = gap, r
        if bd <= 5:
            xs.append(tr["ls_ret"])
            ys.append(best)
    if len(xs) < 8:
        return {"n": len(xs), "corr": None}
    return {"n": len(xs), "corr": float(np.corrcoef(xs, ys)[0, 1])}


def _clean(obj):
    if isinstance(obj, dict):
        return dict((k, _clean(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        return None if (np.isnan(v) or np.isinf(v)) else v
    if isinstance(obj, (np.integer,)):
        return int(obj)
    return obj


def main():
    ensure()
    if os.path.isfile(os.path.join(OUT, "RESULTS.json")):
        raise SystemExit("V31 already read once; refusing")
    t0 = time.time()
    ut = roll_adjust_unit_test()
    print(TAG, "unit_test", ut, flush=True)
    P = load_pack()
    feats = build_features(P)
    elig, xok = eligibility(P)
    fwd = P["fwd_same"]
    print(TAG, "elig mean", float(elig.mean()), "fwd finite", int(np.isfinite(fwd).sum()), flush=True)
    scores, refits = build_scores(P, feats, elig, fwd)
    res = {"dataset": DATASET_ID, "contract": "V31_CN_FUTURES_XS_CONTRACT.md", "features": list(FEATURES),
           "params": LGBM_PARAMS, "refits": refits, "n_products": len(P["products"]), "n_dates": len(P["dates"]),
           "unit_test_roll": ut, "cost_bps_side": COST_BPS_SIDE, "hold": HOLD,
           "pre_run_revision": "honest labels from per-contract 2018-05+; first pred 2019-07; freeze 2023-06-30"}
    bk_r = books(P, scores, elig, *RESEARCH)
    bk_v = books(P, scores, elig, *VALIDATION)
    res["research"] = dict((k, v) for k, v in bk_r.items() if k != "trades")
    res["validation"] = dict((k, v) for k, v in bk_v.items() if k != "trades")
    res["spread_t_research"] = spread_t(P, scores, elig, *RESEARCH)
    res["spread_t_validation"] = spread_t(P, scores, elig, *VALIDATION)
    res["jump_diag_research"] = jump_diag(P, elig, *RESEARCH)
    res["jump_diag_validation"] = jump_diag(P, elig, *VALIDATION)
    res["rolling"] = []
    for a, b in ROLLING_BLOCKS:
        bk = books(P, scores, elig, a, b)
        res["rolling"].append({"block": [a, b], "LS_total": bk["LS"]["total"], "LO_total": bk["LO"]["total"], "n": bk["LS"]["n_periods"]})
    res["corr_vs_ml1_v26_8"] = corr_vs_ml1(bk_r["trades"] + bk_v["trades"])
    res["corr_vs_ml1_validation"] = corr_vs_ml1(bk_v["trades"])
    for key, bk in (("research", bk_r), ("validation", bk_v)):
        if bk["trades"]:
            with open(os.path.join(OUT, "EQUITY_%s.csv" % key.upper()), "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(bk["trades"][0].keys()))
                w.writeheader()
                w.writerows(bk["trades"])
    v = res["validation"]
    n_pos = sum(1 for r in res["rolling"] if r["LS_total"] is not None and r["LS_total"] > 0)
    corr = (res["corr_vs_ml1_validation"] or {}).get("corr")
    gates = {
        "G1_val_LS_capital_gt_0": bool(v["LS"]["total"] is not None and v["LS"]["total"] > 0),
        "G2_val_spread_t_ge_3": bool(res["spread_t_validation"]["t"] is not None and res["spread_t_validation"]["t"] >= 3),
        "G3_rolling_ge_4_of_5": n_pos >= 4,
        "G4_research_LS_gt_0": bool(res["research"]["LS"]["total"] is not None and res["research"]["LS"]["total"] > 0),
        "G5_corr_vs_ml1_lt_0_3": bool(corr is not None and abs(corr) < 0.3),
    }
    res["gates"], res["rolling_positive"] = gates, n_pos
    res["label"] = "CN_FUTURES_XS_V31_LEVEL1" if all(gates.values()) else "CN_FUTURES_XS_V31_NO_CANDIDATE"
    res["elapsed_s"] = round(time.time() - t0, 1)
    res = _clean(res)
    dump_json(os.path.join(OUT, "RESULTS.json"), res)
    dump_json(os.path.join(OUT, "DECISION.json"), _clean({
        "label": res["label"], "gates": gates, "validation_LS": v["LS"], "validation_LO": v["LO"],
        "spread_t_validation": res["spread_t_validation"], "rolling": res["rolling"],
        "corr_vs_ml1_validation": res["corr_vs_ml1_validation"], "paper": False, "orders_sent": False,
    }))
    print(TAG, "DONE", res["label"], json.dumps(gates), "val LS", v["LS"], flush=True)


if __name__ == "__main__":
    main()
