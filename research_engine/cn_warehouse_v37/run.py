"""V37 runner — warehouse receipts to futures XS. Single read."""
from __future__ import print_function

import csv
import json
import os
import time

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_ml_v25 import LGBM_PARAMS
from research_engine.cn_a_share_ml_v25.features import cs_rank_row, ranked_row
from research_engine.cn_futures_v31 import COST_BPS_SIDE, EMBARGO, HOLD, REFIT_EVERY, TRAIN_START, TRAIN_STRIDE
from research_engine.cn_futures_v31.pack import load_pack
from research_engine.cn_futures_v31.run import _clean, _idx, books, spread_t
from research_engine.cn_warehouse_v37 import (
    CACHE, FEATURES, FIRST_PRED, MIN_N, OUT, RAW, RESEARCH, ROLLING_BLOCKS, VALIDATION, WH_MAP, ensure, map_varname,
)
from research_engine.cn_warehouse_v37.pull import parse_totals

TAG = "V37"


def build_wh_panel(P):
    path = os.path.join(CACHE, "wh_panel.npz")
    if os.path.isfile(path):
        z = np.load(path)
        return z["wh"]
    products = P["products"]
    dates = P["dates"]
    T, N = len(dates), len(products)
    pix = dict((p, j) for j, p in enumerate(products))
    wh = np.full((T, N), np.nan, dtype=np.float64)
    n_ok = 0
    for i, d in enumerate(dates):
        fp = os.path.join(RAW, d + ".json")
        if not os.path.isfile(fp):
            continue
        try:
            j = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        totals, seen = parse_totals(j)
        for p in seen:
            jn = pix.get(p)
            if jn is None:
                continue
            wh[i, jn] = totals[p]
        n_ok += 1
        if i % 500 == 0:
            print(TAG, "panel", d, "files", n_ok, flush=True)
    np.savez(path, wh=wh)
    print(TAG, "panel files", n_ok, "finite", int(np.isfinite(wh).sum()), flush=True)
    return wh


def build_features(P, wh):
    path = os.path.join(CACHE, "features_v37.npz")
    if os.path.isfile(path):
        z = np.load(path)
        return dict((k, z[k]) for k in FEATURES)
    T, N = wh.shape
    level = np.log1p(np.where(wh > 0, wh, np.nan))
    ret = np.full_like(wh, np.nan)
    prev = np.vstack([np.full((1, N), np.nan), wh[:-1]])
    ret = np.where((prev > 0) & np.isfinite(wh), wh / prev - 1.0, np.nan)

    def _sum(x, w):
        out = np.full_like(x, np.nan)
        cs = np.nancumsum(np.where(np.isfinite(x), x, 0.0), axis=0)
        cn = np.cumsum(np.isfinite(x).astype(np.int32), axis=0)
        for i in range(w - 1, T):
            n = cn[i] - (cn[i - w] if i >= w else 0)
            good = n == w
            s = cs[i] - (cs[i - w] if i >= w else 0)
            out[i] = np.where(good, s, np.nan)
        return out

    def _std(x, w):
        m = _sum(x, w) / w
        m2 = _sum(x * x, w) / w
        return np.sqrt(np.maximum(0.0, m2 - m * m))

    f = {
        "WH_CHG_20": _sum(ret, 20),
        "WH_CHG_60": _sum(ret, 60),
        "WH_REV_5": -_sum(ret, 5),
        "NEG_WH_LEVEL": -level,
        "WH_VOL_60": _std(ret, 60),
    }
    f = dict((k, v.astype(np.float32)) for k, v in f.items())
    np.savez(path, **f)
    return f


def eligibility(P, feats):
    from research_engine.cn_futures_v31.run import eligibility as elig_v31
    elig, _xok = elig_v31(P)
    mapped = np.array([p in set(WH_MAP.values()) for p in P["products"]])
    has = np.isfinite(feats["NEG_WH_LEVEL"])
    return elig & mapped[None, :] & has, mapped


def build_scores(P, feats, elig, fwd):
    import lightgbm as lgb

    dates = P["dates"]
    T, N = len(dates), len(P["products"])
    i_first = _idx(dates, FIRST_PRED)
    i_train = _idx(dates, TRAIN_START)
    i_res_end = _idx(dates, RESEARCH[1])
    if dates[i_res_end] > RESEARCH[1]:
        i_res_end -= 1
    i_val_end = min(_idx(dates, VALIDATION[1]), T - 1)
    scores = np.full((T, N), np.nan, dtype=np.float32)
    refit_at = list(range(i_first, i_res_end + 1, REFIT_EVERY)) or [i_first]
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
            print(TAG, "skip", dates[s], flush=True)
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
        print(TAG, "refit", k + 1, "/", len(refit_at), dates[s], "rows", meta[-1]["rows"], flush=True)
    np.save(os.path.join(OUT, "SCORES_V37.npy"), scores)
    return scores, meta


def corr_ml1(trades):
    import datetime as dt
    path = os.path.join(os.path.dirname(OUT), "cn_a_share_ml_v25", "ML1_SCALED_UNIT_FULL_CONTRIB2K_MAIN_READ.json")
    if not os.path.isfile(path) or not trades:
        return {"n": 0}
    ml = json.load(open(path, encoding="utf-8"))
    rows = (ml.get("research_trades") or []) + (ml.get("validation_trades") or [])
    ml_d = [(dt.date.fromisoformat(x["signal_date"]), x["ret"]) for x in rows]
    xs, ys = [], []
    for tr in trades:
        d = dt.date.fromisoformat(tr["signal"])
        best, bd = None, 99
        for md, r in ml_d:
            gap = abs((md - d).days)
            if gap < bd:
                bd, best = gap, r
        if bd <= 10:
            xs.append(tr["ls_ret"])
            ys.append(best)
    if len(xs) < 8:
        return {"n": len(xs), "corr": None}
    return {"n": len(xs), "corr": float(np.corrcoef(xs, ys)[0, 1])}


def main():
    ensure()
    if os.path.isfile(os.path.join(OUT, "RESULTS.json")):
        raise SystemExit("V37 already read once; refusing")
    t0 = time.time()
    P = load_pack()
    wh = build_wh_panel(P)
    feats = build_features(P, wh)
    elig, _m = eligibility(P, feats)
    print(TAG, "elig mean", float(elig.mean()), "mapped", len(set(WH_MAP.values())), flush=True)
    scores, meta = build_scores(P, feats, elig, P["fwd_same"])
    res = {"contract": "V37_WAREHOUSE_RECEIPT_CONTRACT.md", "features": list(FEATURES), "refits": meta,
           "wh_map": WH_MAP, "min_n": MIN_N, "cost_bps_side": COST_BPS_SIDE}
    # books() uses V31 MIN_N internally — temporarily acceptable if we filter elig to have scores
    # Override: monkeypatch is worse; copy books with MIN_N from v37
    import research_engine.cn_futures_v31.run as v31r
    old = v31r.MIN_N
    v31r.MIN_N = MIN_N
    try:
        bk_r = books(P, scores, elig, *RESEARCH)
        bk_v = books(P, scores, elig, *VALIDATION)
        res["research"] = dict((k, v) for k, v in bk_r.items() if k != "trades")
        res["validation"] = dict((k, v) for k, v in bk_v.items() if k != "trades")
        res["spread_t_research"] = spread_t(P, scores, elig, *RESEARCH)
        res["spread_t_validation"] = spread_t(P, scores, elig, *VALIDATION)
        res["rolling"] = []
        for a, b in ROLLING_BLOCKS:
            bk = books(P, scores, elig, a, b)
            res["rolling"].append({"block": [a, b], "LS_total": bk["LS"]["total"], "LO_total": bk["LO"]["total"], "n": bk["LS"]["n_periods"]})
    finally:
        v31r.MIN_N = old
    res["corr_vs_ml1"] = corr_ml1(bk_r["trades"] + bk_v["trades"])
    res["corr_vs_ml1_validation"] = corr_ml1(bk_v["trades"])
    for key, bk in (("research", bk_r), ("validation", bk_v)):
        if bk["trades"]:
            with open(os.path.join(OUT, "EQUITY_%s.csv" % key.upper()), "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(bk["trades"][0].keys()))
                w.writeheader()
                w.writerows(bk["trades"])
    v = res["validation"]
    n_pos = sum(1 for r in res["rolling"] if r["LS_total"] is not None and r["LS_total"] > 0)
    corr = (res["corr_vs_ml1_validation"] or {}).get("corr")
    if corr is None:
        corr = (res["corr_vs_ml1"] or {}).get("corr")
    gates = {
        "G1_val_LS_gt_0": bool(v["LS"]["total"] is not None and v["LS"]["total"] > 0),
        "G2_val_spread_t_ge_3": bool(res["spread_t_validation"]["t"] is not None and res["spread_t_validation"]["t"] >= 3),
        "G3_rolling_ge_4_of_5": n_pos >= 4,
        "G4_research_LS_gt_0": bool(res["research"]["LS"]["total"] is not None and res["research"]["LS"]["total"] > 0),
        "G5_corr_vs_ml1_lt_0_3": bool(corr is not None and abs(corr) < 0.3),
    }
    res["gates"], res["rolling_positive"] = gates, n_pos
    res["label"] = "CN_FUTURES_WAREHOUSE_V37_LEVEL1" if all(gates.values()) else "CN_FUTURES_WAREHOUSE_V37_NO_CANDIDATE"
    res["elapsed_s"] = round(time.time() - t0, 1)
    dump_json(os.path.join(OUT, "RESULTS.json"), _clean(res))
    dump_json(os.path.join(OUT, "DECISION.json"), _clean({"label": res["label"], "gates": gates, "validation_LS": v.get("LS"), "rolling": res["rolling"], "orders_sent": False}))
    print(TAG, "DONE", res["label"], gates, "val LS", v.get("LS"), flush=True)


if __name__ == "__main__":
    main()
