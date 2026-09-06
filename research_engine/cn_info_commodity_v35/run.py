"""V35 runner. Single read. Does not reuse V31's 8 features."""
from __future__ import print_function

import csv
import os
import time

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_ml_v25 import LGBM_PARAMS
from research_engine.cn_futures_v31 import COST_BPS_SIDE, EMBARGO, FIRST_PRED, HOLD, REFIT_EVERY, RESEARCH, ROLLING_BLOCKS, TRAIN_START, TRAIN_STRIDE, VALIDATION
from research_engine.cn_futures_v31.pack import load_pack
from research_engine.cn_info_commodity_v35 import FEATURES, INDEX_DAILY, OUT, PRODUCTS, ensure

TAG = "V35"
COST = COST_BPS_SIDE / 1e4 * 2


def _idx(dates, day):
    for i, d in enumerate(dates):
        if d >= day:
            return i
    return len(dates)


def _load_index(name):
    path = os.path.join(INDEX_DAILY, name + ".csv")
    d, c = [], []
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            d.append(r["date"])
            c.append(float(r["close"]))
    return d, np.array(c, dtype=np.float64)


def align_index(dates):
    hs_d, hs_c = _load_index("HS300")
    zz_d, zz_c = _load_index("ZZ500")
    hix, zix = dict(zip(hs_d, range(len(hs_d)))), dict(zip(zz_d, range(len(zz_d))))
    hs = np.array([hs_c[hix[d]] if d in hix else np.nan for d in dates])
    zz = np.array([zz_c[zix[d]] if d in zix else np.nan for d in dates])
    def ret(px, w):
        out = np.full_like(px, np.nan)
        out[w:] = np.where(px[:-w] > 0, px[w:] / px[:-w] - 1.0, np.nan)
        return out
    r1 = np.full_like(hs, np.nan)
    r1[1:] = np.where(hs[:-1] > 0, hs[1:] / hs[:-1] - 1.0, np.nan)
    vol = np.full_like(hs, np.nan)
    for i in range(60, len(hs)):
        w = r1[i - 59:i + 1]
        if np.isfinite(w).sum() >= 40:
            vol[i] = np.nanstd(w, ddof=1)
    f = {
        "HS300_RET_20": ret(hs, 20),
        "ZZ500_RET_20": ret(zz, 20),
        "HS300_REV_5": -ret(hs, 5),
        "HS300_VOL_60": -vol,
    }
    f["SIZE_SPREAD_20"] = f["ZZ500_RET_20"] - f["HS300_RET_20"]
    return f


def build_scores(dates, feats, y_mat, prod_idx):
    import lightgbm as lgb

    T, K = y_mat.shape
    i_first = _idx(dates, FIRST_PRED)
    i_train = _idx(dates, TRAIN_START)
    i_res_end = _idx(dates, RESEARCH[1])
    if dates[i_res_end] > RESEARCH[1]:
        i_res_end -= 1
    i_val_end = min(_idx(dates, VALIDATION[1]), T - 1)
    daily = np.full(T, np.nan, dtype=np.float32)
    refit_at = list(range(i_first, i_res_end + 1, REFIT_EVERY)) or [i_first]
    meta = []
    for k, s in enumerate(refit_at):
        cutoff = s - EMBARGO
        X, y = [], []
        for g in range(i_train, cutoff + 1, TRAIN_STRIDE):
            row = np.array([feats[n][g] for n in FEATURES], dtype=np.float64)
            if not np.isfinite(row).all():
                continue
            for j in range(K):
                if np.isfinite(y_mat[g, j]):
                    X.append(row)
                    y.append(y_mat[g, j])
        if len(y) < 80:
            print(TAG, "skip", dates[s], "rows", len(y), flush=True)
            continue
        model = lgb.LGBMRegressor(**LGBM_PARAMS)
        model.fit(np.vstack(X), np.array(y))
        s_end = refit_at[k + 1] - 1 if k + 1 < len(refit_at) else i_val_end
        for u in range(s, s_end + 1):
            row = np.array([feats[n][u] for n in FEATURES], dtype=np.float64)
            if np.isfinite(row).all():
                daily[u] = float(model.predict(row.reshape(1, -1))[0])
        meta.append({"fit_at": dates[s], "rows": int(len(y)), "scored_through": dates[s_end]})
        print(TAG, "refit", k + 1, "/", len(refit_at), dates[s], "rows", len(y), flush=True)
    return daily, meta


def books(dates, daily, y_mat, start, end):
    i0, i1 = _idx(dates, start), _idx(dates, end)
    T = len(dates)
    eq, eq_ew, trades, t = 1.0, 1.0, [], i0
    while t + HOLD + 1 < T and t <= i1:
        pred = daily[t]
        ys = y_mat[t]
        ok = np.isfinite(ys)
        if int(ok.sum()) < 1 or not np.isfinite(pred):
            t += 1
            continue
        ew = float(np.mean(ys[ok])) - COST
        r = (ew if pred > 0 else 0.0)
        # when we go long we pay cost; cash = 0
        if pred > 0:
            r = float(np.mean(ys[ok])) - COST
        eq *= 1.0 + r
        eq_ew *= 1.0 + ew
        trades.append({"signal": dates[t], "pred": float(pred), "on": bool(pred > 0), "n": int(ok.sum()),
                       "lf_ret": r, "ew4_ret": ew, "eq_lf": eq, "eq_ew4": eq_ew})
        t = t + 1 + HOLD
    def summ(key, eqk):
        x = np.array([tr[key] for tr in trades])
        yrs = max(1e-9, len(trades) * (HOLD + 1) / 242.0)
        e = np.array([tr[eqk] for tr in trades])
        dd = float(np.min(e / np.maximum.accumulate(np.concatenate([[1.0], e]))[1:] - 1.0)) if len(e) else None
        years = {}
        for tr in trades:
            years.setdefault(tr["signal"][:4], []).append(tr[key])
        return {"n_periods": len(trades), "total": float(e[-1] - 1) if len(e) else None,
                "cagr": float(e[-1] ** (1 / yrs) - 1) if len(e) else None,
                "mean_per_period": float(x.mean()) if len(x) else None,
                "t": float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 else None,
                "hit": float((x > 0).mean()) if len(x) else None, "maxdd": dd,
                "frac_on": float(np.mean([tr["on"] for tr in trades])) if trades else None,
                "by_year": dict((y, float(np.prod([1 + a for a in v]) - 1)) for y, v in sorted(years.items()))}
    return {"trades": trades, "LONGFLAT": summ("lf_ret", "eq_lf"), "EW4": summ("ew4_ret", "eq_ew4")}


def _clean(obj):
    if isinstance(obj, dict):
        return dict((k, _clean(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        return None if np.isnan(v) or np.isinf(v) else v
    if isinstance(obj, (np.integer,)):
        return int(obj)
    return obj


def main():
    ensure()
    if os.path.isfile(os.path.join(OUT, "RESULTS.json")):
        raise SystemExit("V35 already read once; refusing")
    t0 = time.time()
    P = load_pack()
    dates, products = P["dates"], P["products"]
    pix = dict((p, i) for i, p in enumerate(products))
    missing = [p for p in PRODUCTS if p not in pix]
    if missing:
        raise SystemExit("missing products %s" % missing)
    y_mat = np.stack([P["fwd_same"][:, pix[p]] for p in PRODUCTS], axis=1)
    feats = align_index(dates)
    daily, meta = build_scores(dates, feats, y_mat, pix)
    np.save(os.path.join(OUT, "SCORES_V35_DAILY.npy"), daily)
    res = {"contract": "V35_CN_INFO_TO_COMMODITY_CONTRACT.md", "products": list(PRODUCTS), "features": list(FEATURES),
           "refits": meta, "cost_bps_side": COST_BPS_SIDE}
    bk_r = books(dates, daily, y_mat, *RESEARCH)
    bk_v = books(dates, daily, y_mat, *VALIDATION)
    res["research"] = dict((k, v) for k, v in bk_r.items() if k != "trades")
    res["validation"] = dict((k, v) for k, v in bk_v.items() if k != "trades")
    res["rolling"] = []
    for a, b in ROLLING_BLOCKS:
        bk = books(dates, daily, y_mat, a, b)
        res["rolling"].append({"block": [a, b], "LF_total": bk["LONGFLAT"]["total"], "EW4_total": bk["EW4"]["total"], "n": bk["LONGFLAT"]["n_periods"]})
    v = res["validation"]
    n_pos = sum(1 for r in res["rolling"] if r["LF_total"] is not None and r["LF_total"] > 0)
    beat = (v["LONGFLAT"]["total"] or 0) - (v["EW4"]["total"] or 0)
    gates = {
        "G1_val_LF_gt_0": bool(v["LONGFLAT"]["total"] is not None and v["LONGFLAT"]["total"] > 0),
        "G2_val_t_ge_2": bool(v["LONGFLAT"]["t"] is not None and v["LONGFLAT"]["t"] >= 2),
        "G3_rolling_ge_4_of_5": n_pos >= 4,
        "G4_research_LF_gt_0": bool(res["research"]["LONGFLAT"]["total"] is not None and res["research"]["LONGFLAT"]["total"] > 0),
        "G5_val_LF_beats_EW4": bool(beat > 0),
    }
    res["gates"], res["rolling_positive"] = gates, n_pos
    res["label"] = "CN_INFO_TO_COMMODITY_V35_LEVEL1" if all(gates.values()) else "CN_INFO_TO_COMMODITY_V35_NO_CANDIDATE"
    res["elapsed_s"] = round(time.time() - t0, 1)
    for key, bk in (("research", bk_r), ("validation", bk_v)):
        if bk["trades"]:
            with open(os.path.join(OUT, "EQUITY_%s.csv" % key.upper()), "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(bk["trades"][0].keys()))
                w.writeheader()
                w.writerows(bk["trades"])
    dump_json(os.path.join(OUT, "RESULTS.json"), _clean(res))
    dump_json(os.path.join(OUT, "DECISION.json"), _clean({"label": res["label"], "gates": gates, "validation": v, "rolling": res["rolling"], "orders_sent": False}))
    print(TAG, "DONE", res["label"], gates, "val LF", v["LONGFLAT"], "val EW4", v["EW4"], flush=True)


if __name__ == "__main__":
    main()
