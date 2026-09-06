"""V36 runner — industry-bucket returns to futures XS. Single read."""
from __future__ import print_function

import csv
import os
import time

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.pack import load_pack as load_ashare
from research_engine.cn_a_share_ml_v25 import LGBM_PARAMS
from research_engine.cn_a_share_ml_v25.features import cs_rank_row, ranked_row
from research_engine.cn_futures_v31 import COST_BPS_SIDE, EMBARGO, HOLD, MIN_N, REFIT_EVERY, TRAIN_START, TRAIN_STRIDE
from research_engine.cn_futures_v31.pack import load_pack as load_fut
from research_engine.cn_futures_v31.run import _clean, _idx, books, spread_t
from research_engine.cn_ind_fut_v36 import (
    BUCKET_NEEDLES, CACHE, FEATURES, FIRST_PRED, IND_CSV, OUT, PRODUCT_BUCKET, RESEARCH, ROLLING_BLOCKS, VALIDATION, ensure,
)
from research_engine.cn_a_share_strategy_v14_1.scores import eligible as ashare_eligible

TAG = "V36"


def _needles_of(label):
    hits = []
    for b, ns in BUCKET_NEEDLES.items():
        if any(n in label for n in ns):
            hits.append(b)
    return hits


def load_industry_snaps():
    snaps = {}
    with open(IND_CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            d = r["effective_date"]
            snaps.setdefault(d, {})[r["symbol"]] = r["industry"]
    dates = sorted(snaps)
    print(TAG, "industry snaps", len(dates), dates[0], dates[-1], flush=True)
    return dates, snaps


def bucket_daily_on_ashare():
    path = os.path.join(CACHE, "bucket_daily.npz")
    if os.path.isfile(path):
        z = np.load(path)
        return list(z["dates"]), dict((k, z[k]) for k in BUCKET_NEEDLES), z["mkt"]
    pack = load_ashare()
    adates, asym = pack["dates"], pack["symbols"]
    close = np.array(pack["close"], dtype=np.float64)
    ret = np.full_like(close, np.nan)
    ret[1:] = np.where((close[:-1] > 0) & np.isfinite(close[1:]), close[1:] / close[:-1] - 1.0, np.nan)
    elig = ashare_eligible(pack, 20)
    sidx = dict((s, i) for i, s in enumerate(asym))
    idates, snaps = load_industry_snaps()
    buckets = list(BUCKET_NEEDLES)
    B = {b: np.full(len(adates), np.nan, dtype=np.float64) for b in buckets}
    mkt = np.full(len(adates), np.nan, dtype=np.float64)
    si = 0
    members = {b: [] for b in buckets}
    for t, day in enumerate(adates):
        while si + 1 < len(idates) and idates[si + 1] <= day:
            si += 1
            members = {b: [] for b in buckets}
            for sym, lab in snaps[idates[si]].items():
                j = sidx.get(sym)
                if j is None:
                    continue
                for b in _needles_of(lab):
                    members[b].append(j)
        ok = elig[t]
        js = np.where(ok & np.isfinite(ret[t]))[0]
        if js.size >= 50:
            mkt[t] = float(np.mean(ret[t, js]))
        for b in buckets:
            idx = [j for j in members[b] if ok[j] and np.isfinite(ret[t, j])]
            if len(idx) >= 5:
                B[b][t] = float(np.mean(ret[t, idx]))
        if t % 500 == 0:
            print(TAG, "ashare day", day, flush=True)
    np.savez(path, dates=np.array(adates), mkt=mkt, **B)
    return adates, B, mkt


def _roll_sum(x, w):
    out = np.full_like(x, np.nan, dtype=np.float64)
    cs = np.nancumsum(np.where(np.isfinite(x), x, 0.0))
    cn = np.cumsum(np.isfinite(x).astype(np.int32))
    for i in range(w - 1, len(x)):
        n = cn[i] - (cn[i - w] if i >= w else 0)
        if n == w:
            out[i] = cs[i] - (cs[i - w] if i >= w else 0.0)
    return out


def _roll_std(x, w):
    out = np.full_like(x, np.nan, dtype=np.float64)
    cs = np.nancumsum(np.where(np.isfinite(x), x, 0.0))
    cs2 = np.nancumsum(np.where(np.isfinite(x), x * x, 0.0))
    cn = np.cumsum(np.isfinite(x).astype(np.int32))
    for i in range(w - 1, len(x)):
        n = cn[i] - (cn[i - w] if i >= w else 0)
        if n < w - 5:
            continue
        s = cs[i] - (cs[i - w] if i >= w else 0.0)
        s2 = cs2[i] - (cs2[i - w] if i >= w else 0.0)
        var = (s2 - s * s / n) / max(n - 1, 1)
        out[i] = np.sqrt(max(var, 0.0))
    return out


def _asof_index(src_dates, dst_dates):
    """Last source index with date <= dest date; -1 if none."""
    out = np.full(len(dst_dates), -1, dtype=np.int32)
    j = 0
    n = len(src_dates)
    for i, d in enumerate(dst_dates):
        while j + 1 < n and src_dates[j + 1] <= d:
            j += 1
        if j < n and src_dates[j] <= d:
            out[i] = j
        elif n and src_dates[0] <= d:
            out[i] = 0
    return out


def align_features(P):
    path = os.path.join(CACHE, "feat_on_fut.npz")
    if os.path.isfile(path):
        z = np.load(path)
        return dict((k, z[k]) for k in FEATURES)
    adates, B, mkt = bucket_daily_on_ashare()
    fdates, products = P["dates"], P["products"]
    T, N = len(fdates), len(products)
    # Features live on the A-share calendar (no double-count of extra futures dates),
    # then as-of map onto the futures calendar (last A-share session <= futures date).
    ash = {}
    mkt20 = _roll_sum(mkt, 20)
    for b, x in B.items():
        r20 = _roll_sum(x, 20)
        r60 = _roll_sum(x, 60)
        r5 = _roll_sum(x, 5)
        vol = _roll_std(x, 60)
        ash[b] = {
            "IND_RET_20": r20,
            "IND_MOM_60_20": r60 - r20,
            "IND_REL_MKT_20": r20 - mkt20,
            "IND_VOL_60": vol,
            "IND_REV_5": -r5,
        }
    aix = _asof_index(adates, fdates)
    feats = {k: np.full((T, N), np.nan, dtype=np.float32) for k in FEATURES}
    ok = aix >= 0
    take = aix[ok]
    for j, p in enumerate(products):
        b = PRODUCT_BUCKET.get(p)
        if not b:
            continue
        for k in FEATURES:
            col = np.full(T, np.nan, dtype=np.float32)
            col[ok] = ash[b][k][take]
            feats[k][:, j] = col
    np.savez(path, **feats)
    return feats


def eligibility(P):
    from research_engine.cn_futures_v31.run import eligibility as elig_v31
    elig, xok = elig_v31(P)
    mapped = np.array([p in PRODUCT_BUCKET for p in P["products"]])
    elig = elig & mapped[None, :]
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
    np.save(os.path.join(OUT, "SCORES_V36.npy"), scores)
    return scores, meta


def corr_ml1(trades):
    import datetime as dt
    import json
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
        raise SystemExit("V36 already read once; refusing")
    t0 = time.time()
    P = load_fut()
    feats = align_features(P)
    elig, xok = eligibility(P)
    fwd = P["fwd_same"]
    print(TAG, "elig mean", float(elig.mean()), "mapped", sum(p in PRODUCT_BUCKET for p in P["products"]), flush=True)
    scores, meta = build_scores(P, feats, elig, fwd)
    res = {"contract": "V36_INDUSTRY_TO_FUTURES_CONTRACT.md", "features": list(FEATURES), "refits": meta,
           "product_bucket": PRODUCT_BUCKET, "cost_bps_side": COST_BPS_SIDE,
           "pre_run_revision": "industry file ends 2024-02; validation 2022-07..2024-02"}
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
    res["label"] = "CN_INDUSTRY_TO_FUTURES_V36_LEVEL1" if all(gates.values()) else "CN_INDUSTRY_TO_FUTURES_V36_NO_CANDIDATE"
    res["elapsed_s"] = round(time.time() - t0, 1)
    dump_json(os.path.join(OUT, "RESULTS.json"), _clean(res))
    dump_json(os.path.join(OUT, "DECISION.json"), _clean({"label": res["label"], "gates": gates, "validation_LS": v.get("LS"), "rolling": res["rolling"], "orders_sent": False}))
    print(TAG, "DONE", res["label"], gates, "val LS", v.get("LS"), flush=True)


if __name__ == "__main__":
    main()
