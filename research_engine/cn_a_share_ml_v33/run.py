"""V33 runner: event features -> limit-up label -> walk-forward LGBM classifier -> predictive lift + owner-shell book (hold 5). Single read."""
from __future__ import print_function

import os
import time

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.cn_a_share_alpha_v2.books import ew_overlapping
from research_engine.cn_a_share_ml_v25 import FIRST_PRED, LGBM_PARAMS, REFIT_EVERY, RESEARCH, TRAIN_STRIDE, VALIDATION
from research_engine.cn_a_share_ml_v25.features import NAMES as ML1_NAMES, load_features, ranked_row
from research_engine.cn_a_share_ml_v25.model import _first_at_or_after, _last_at_or_before
from research_engine.cn_a_share_ml_v25.top_n_book import board_mask, summarize, top_n_book
from research_engine.cn_a_share_ml_v33 import CACHE, EMBARGO, EVT_NAMES, HOLD, LABEL_FROM, LABEL_TO, OUT, TOP_FRAC
from research_engine.cn_a_share_strategy_v14_1.scores import _limit_col, daily_return, eligible, exec_ok_matrix

TAG = "V33"
NAMES = tuple(ML1_NAMES) + EVT_NAMES


def _roll_sum(x, w):
    c = np.nancumsum(np.where(np.isfinite(x), x, 0.0), axis=0)
    n = np.cumsum(np.isfinite(x), axis=0)
    s = c.copy()
    s[w:] = c[w:] - c[:-w]
    cnt = n.copy()
    cnt[w:] = n[w:] - n[:-w]
    return s, cnt


def _roll_max(x, w):
    T = x.shape[0]
    out = np.full_like(x, np.nan)
    for t in range(T):
        a = max(0, t - w + 1)
        out[t] = np.nanmax(np.where(np.isfinite(x[a:t + 1]), x[a:t + 1], -np.inf), axis=0)
    out[~np.isfinite(out)] = np.nan
    return out


def limit_up_matrix(pack):
    dates, symbols = pack["dates"], pack["symbols"]
    close = np.array(pack["close"], dtype=np.float64)
    pre = np.array(pack["preclose"], dtype=np.float64)
    st = np.array(pack["isST"]) == 1
    lim = np.stack([_limit_col(s, dates) for s in symbols], axis=1)
    lim = np.where(st, 0.05, lim)
    mv = close / pre - 1.0
    return np.isfinite(mv) & (mv >= lim - 0.002)


def event_features(pack, lu):
    os.makedirs(CACHE, exist_ok=True)
    paths = dict((n, os.path.join(CACHE, n + ".npy")) for n in EVT_NAMES)
    if all(os.path.isfile(p) for p in paths.values()):
        return dict((n, np.load(p, mmap_mode="r")) for n, p in paths.items())
    close = np.array(pack["close"], dtype=np.float64)
    high = np.array(pack["high"], dtype=np.float64)
    low = np.array(pack["low"], dtype=np.float64)
    pre = np.array(pack["preclose"], dtype=np.float64)
    vol = np.array(pack["volume"], dtype=np.float64)
    ret = daily_return(close)
    s5, c5 = _roll_sum(ret, 5)
    r5 = np.where(c5 == 5, s5, np.nan)
    med5 = np.nanmedian(r5, axis=1)
    v5, n5 = _roll_sum(vol, 5)
    v60, n60 = _roll_sum(vol, 60)
    volr = np.where((n5 == 5) & (n60 >= 40), (v5 / 5.0) / np.maximum(v60 / np.maximum(n60, 1), 1e-9), np.nan)
    nlu, _ = _roll_sum(lu.astype(np.float64), 10)
    hi250 = _roll_max(close, 250)
    amp = np.where(np.isfinite(high) & np.isfinite(low) & (pre > 0), (high - low) / pre, np.nan)
    a5, ca5 = _roll_sum(amp, 5)
    out = {
        "EVT_RET_1": ret.astype(np.float32),
        "EVT_RET_5": r5.astype(np.float32),
        "EVT_ABN_5": (r5 - med5[:, None]).astype(np.float32),
        "EVT_VOLR_5_60": volr.astype(np.float32),
        "EVT_NLU_10": nlu.astype(np.float32),
        "EVT_DIST_HI_250": (close / hi250 - 1.0).astype(np.float32),
        "EVT_AMP_5": np.where(ca5 == 5, a5 / 5.0, np.nan).astype(np.float32),
    }
    for n, p in paths.items():
        np.save(p, out[n])
    return dict((n, np.load(p, mmap_mode="r")) for n, p in paths.items())


def label_matrix(lu, t_end):
    T, N = lu.shape
    y = np.full((T, N), np.nan, dtype=np.float32)
    for t in range(0, min(t_end + 1, T - LABEL_TO)):
        y[t] = lu[t + LABEL_FROM:t + LABEL_TO + 1].any(axis=0)
    return y


def build_scores(pack, feats, elig, xok, y):
    import lightgbm as lgb

    dates = pack["dates"]
    T, N = len(dates), len(pack["symbols"])
    i_first = _first_at_or_after(dates, FIRST_PRED)
    i_res_start = _first_at_or_after(dates, RESEARCH[0])
    i_res_end = _last_at_or_before(dates, RESEARCH[1])
    i_val_end = _last_at_or_before(dates, VALIDATION[1])
    grid = [t for t in range(i_res_start, i_res_end - EMBARGO + 1) if (t - i_res_start) % TRAIN_STRIDE == 0]
    Xs, ys = {}, {}
    for t in grid:
        mask = elig[t] & np.isfinite(y[t]) & xok[t + 1]
        if int(mask.sum()) < 100:
            continue
        X = ranked_row(feats, t, mask, NAMES)
        Xs[t], ys[t] = X[mask], y[t][mask]
    refits = list(range(i_first, i_res_end + 1, REFIT_EVERY))
    params = dict(LGBM_PARAMS)
    params.pop("objective", None)
    scores = np.full((T, N), np.nan, dtype=np.float32)
    meta = {"features": list(NAMES), "refits": [], "frozen_after": dates[i_res_end]}
    for k, s in enumerate(refits):
        t0 = time.time()
        cutoff = s - EMBARGO
        tr = [t for t in grid if t <= cutoff and t in Xs]
        X = np.concatenate([Xs[t] for t in tr]); yy = np.concatenate([ys[t] for t in tr])
        model = lgb.LGBMClassifier(objective="binary", **params)
        model.fit(X, yy)
        s_end = refits[k + 1] - 1 if k + 1 < len(refits) else i_val_end
        for t in range(s, s_end + 1):
            mask = elig[t]
            if int(mask.sum()) < 100:
                continue
            rows = np.where(mask)[0]
            Xt = ranked_row(feats, t, mask, NAMES)
            scores[t, rows] = model.predict_proba(Xt[rows])[:, 1].astype(np.float32)
        imp = model.booster_.feature_importance(importance_type="gain")
        imp = (imp / max(float(imp.sum()), 1e-12)).tolist()
        meta["refits"].append({"fit_at": dates[s], "rows": int(X.shape[0]), "base_rate": float(yy.mean()), "gain_share": dict(zip(NAMES, [round(v, 4) for v in imp])), "sec": round(time.time() - t0, 1)})
        print(TAG, "refit", k + 1, "/", len(refits), dates[s], "rows", X.shape[0], "base %.3f" % yy.mean(), "%.0fs" % (time.time() - t0), flush=True)
    return scores, meta


def lift(pack, scores, y, elig, xok, start, end):
    dates = pack["dates"]
    i0, i1 = dates.index(start), dates.index(end)
    rows = []
    for t in range(i0, i1 + 1):
        m = elig[t] & np.isfinite(scores[t]) & np.isfinite(y[t]) & xok[t + 1] if t + 1 < len(dates) else None
        if m is None or int(m.sum()) < 200:
            continue
        idx = np.where(m)[0]
        k = max(1, int(round(idx.size * TOP_FRAC)))
        top = idx[np.argsort(scores[t][idx])[-k:]]
        rows.append((dates[t], float(y[t][top].mean()), float(y[t][idx].mean())))
    a = np.array([r[1] for r in rows]); b = np.array([r[2] for r in rows]); d = a - b
    return {"n_sessions": len(rows), "top_hit": float(a.mean()), "base_hit": float(b.mean()), "lift": float(d.mean()),
            "t": float(d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))) if len(d) > 2 else None, "frac_sessions_positive": float((d > 0).mean())}


def lo20_diag(pack, scores, elig, xok, start, end):
    from research_engine.cn_a_share_alpha_v2.books import capital_book
    dates = pack["dates"]
    bk = capital_book(pack, scores, elig, xok, start, end, HOLD)
    ew = ew_overlapping(pack, elig, xok, start, dates[dates.index(end) - HOLD - 1], HOLD)
    ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
    led = bk.get("ledger") or bk.get("trades") or []
    return {"total": bk.get("total"), "n_periods": len(led), "raw": {k: v for k, v in bk.items() if not isinstance(v, (list, dict))}, "ew_mean": float(np.nanmean(list(ewm.values()))) if ewm else None}


def main():
    if os.path.isfile(os.path.join(OUT, "RESULTS.json")):
        raise SystemExit("V33 already read once; refusing")
    os.makedirs(OUT, exist_ok=True)
    pack = load_pack()
    dates = pack["dates"]
    i_val_end = _last_at_or_before(dates, VALIDATION[1])
    elig, xok = eligible(pack, 20), exec_ok_matrix(pack)
    lu = limit_up_matrix(pack)
    feats = dict(load_features())
    feats.update(event_features(pack, lu))
    y = label_matrix(lu, i_val_end)
    print(TAG, "label base rate (eligible, research+val) %.4f" % np.nanmean(np.where(elig[:i_val_end + 1], y[:i_val_end + 1], np.nan)), flush=True)
    scores, meta = build_scores(pack, feats, elig, xok, y)
    np.save(os.path.join(OUT, "SCORES_ML3_LU5.npy"), scores)
    res = {"contract": "V33_LIMITUP_EVENT_MODEL_CONTRACT.md", "hold": HOLD, "denied_window_read": False, "model_meta": meta}
    shell = dict(capital=20_000.0, boards="MAIN", max_price=100.0, eq_money=True, exposure=0.80, hold=HOLD)
    c = np.asarray(pack["close"], dtype=float)
    elig_shell = elig & board_mask(pack["symbols"], "MAIN")[None, :] & np.isfinite(c) & (c <= 100.0)
    for key, (a, b) in (("research", RESEARCH), ("validation", VALIDATION)):
        a = max(a, FIRST_PRED)
        res[key] = {"lift_top10pct": lift(pack, scores, y, elig, xok, a, b)}
        bk = top_n_book(pack, scores, elig, xok, a, b, **shell)
        ew = ew_overlapping(pack, elig_shell, xok, a, dates[dates.index(b) - HOLD - 1], HOLD)
        ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
        res[key]["shell_book_20k_main_80pct_hold5"] = summarize(bk, ewm, hold=HOLD)
        res[key]["shell_periods"] = [dict((k, v) for k, v in tr.items() if k != "names") for tr in bk["trades"]]
        try:
            res[key]["lo20_diag_hold5"] = lo20_diag(pack, scores, elig, xok, a, b)
        except Exception as e:
            res[key]["lo20_diag_hold5"] = {"error": repr(e)[:200]}
        print(TAG, key, "lift", res[key]["lift_top10pct"], flush=True)
        print(TAG, key, "shell", {k: v for k, v in res[key]["shell_book_20k_main_80pct_hold5"].items() if k in ("n_periods", "total", "cagr", "maxdd", "mean_excess_vs_ew", "t_excess", "beat_ew_periods", "mean_fill")}, flush=True)
    v = res["validation"]
    g1 = bool(v["lift_top10pct"]["lift"] > 0 and (v["lift_top10pct"]["t"] or 0) > 2)
    sb = v["shell_book_20k_main_80pct_hold5"]
    g2 = bool(sb["total"] > 0 and (sb["mean_excess_vs_ew"] or 0) > 0)
    res["gates"] = {"G1_predictive_lift": g1, "G2_shell_book": g2}
    res["label"] = "A_SHARE_LIMITUP_EVENT_V33_LEVEL1" if (g1 and g2) else ("A_SHARE_LIMITUP_EVENT_V33_PREDICTIVE_BUT_NOT_TRADABLE_AT_20K" if g1 else "A_SHARE_LIMITUP_EVENT_V33_NO_CANDIDATE")
    dump_json(os.path.join(OUT, "RESULTS.json"), res)
    print(TAG, "DONE", res["label"], flush=True)


if __name__ == "__main__":
    main()
