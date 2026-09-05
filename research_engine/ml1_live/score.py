"""Features + REFIT_240 model + top-20% list for one session of the live pack. V26 policy; nothing tunable here."""
from __future__ import print_function

import json
import os
import pickle
import time

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_ml_v25 import EMBARGO, FIRST_PRED, LGBM_PARAMS, RESEARCH, TRAIN_STRIDE
from research_engine.cn_a_share_ml_v25 import HOLD_DAYS as V25_HOLD
from research_engine.cn_a_share_ml_v25.features import NAMES, build_features, ranked_row
from research_engine.cn_a_share_ml_v25.model import _first_at_or_after, _label_row, forward_open_matrix
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix, pick_lexsort
from research_engine.ml1_live import FEATURES, LIVE_REFIT, LOT, MODELS, QUANTILE, SIGNALS, ensure_live

TAG = "ML1_LIVE_SCORE"


def features_for(pack, force):
    """V25 feature stack on the live pack, cached in live/features (env TRADEMIND_V25_FEAT_CACHE must point there)."""
    assert os.path.abspath(os.environ.get("TRADEMIND_V25_FEAT_CACHE", "")) == os.path.abspath(FEATURES), "feature cache env not set to live dir"
    stamp = os.path.join(FEATURES, "PACK_STAMP.json")
    prev = json.load(open(stamp, encoding="utf-8")) if os.path.isfile(stamp) else {}
    cur = {"n_dates": len(pack["dates"]), "n_symbols": len(pack["symbols"]), "live_hash": pack["meta"]["live_hash"]}
    rebuild = force or prev != cur
    feats = build_features(pack, force=rebuild)
    if rebuild:
        json.dump(cur, open(stamp, "w", encoding="utf-8"))
    return feats, rebuild


def refit_dates(dates, upto_index):
    i_first = _first_at_or_after(dates, FIRST_PRED)
    return [s for s in range(i_first, upto_index + 1, LIVE_REFIT)]


def model_for(pack, feats, elig, xok, t):
    """Model of the latest refit <= t under the REFIT_240 schedule; fitted once and pickled by refit date."""
    import lightgbm as lgb

    dates = pack["dates"]
    s = refit_dates(dates, t)[-1]
    path = os.path.join(MODELS, "REFIT_%s.pkl" % dates[s])
    if os.path.isfile(path):
        with open(path, "rb") as fh:
            return pickle.load(fh), dates[s], False
    t0 = time.time()
    cutoff = s - EMBARGO
    i_res_start = _first_at_or_after(dates, RESEARCH[0])
    fwd = forward_open_matrix(pack, V25_HOLD, cutoff)
    Xs, ys = [], []
    for g in range(i_res_start, cutoff + 1, TRAIN_STRIDE):
        mask = elig[g] & np.isfinite(fwd[g]) & xok[g + 1]
        if int(mask.sum()) < 100:
            continue
        X = ranked_row(feats, g, mask)
        y = _label_row(fwd[g], mask)
        keep = mask & np.isfinite(y)
        Xs.append(X[keep])
        ys.append(y[keep])
    model = lgb.LGBMRegressor(**LGBM_PARAMS)
    model.fit(np.concatenate(Xs), np.concatenate(ys))
    meta = {"fit_at": dates[s], "train_last_label_session": dates[cutoff], "train_rows": int(sum(len(y) for y in ys)),
            "params": LGBM_PARAMS, "features": list(NAMES), "sec": round(time.time() - t0, 1)}
    with open(path, "wb") as fh:
        pickle.dump(model, fh)
    dump_json(path.replace(".pkl", ".json"), meta)
    print(TAG, "fitted", meta["fit_at"], "rows", meta["train_rows"], "%.0fs" % meta["sec"], flush=True)
    return model, dates[s], True


def score_session(pack, feats, elig, xok, t, capital, tag="SIGNAL"):
    """Top-quintile list at session t (close of t; execution = open of t+1). Emits SIGNAL_{date}.json. No orders."""
    ensure_live()
    dates = pack["dates"]
    model, fit_at, fitted = model_for(pack, feats, elig, xok, t)
    mask = elig[t]
    Xt = ranked_row(feats, t, mask)
    rows = np.where(mask)[0]
    scores = np.full(len(pack["symbols"]), np.nan, dtype=np.float32)
    scores[rows] = model.predict(Xt[rows]).astype(np.float32)
    js = pick_lexsort(scores, mask)
    sel = [int(j) for j in js] if js is not None else []
    close = np.array(pack["close"][t], dtype=np.float64)
    w = 1.0 / len(sel) if sel else 0.0
    names = []
    for j in sel:
        px = float(close[j]) if np.isfinite(close[j]) else None
        lots = int((capital * w) // (px * LOT)) if px else None
        names.append({"symbol": pack["symbols"][j], "score": float(scores[j]), "weight": w, "target_yuan": round(capital * w, 2),
                      "last_close": px, "lots_100": lots})
    cover = dict((n, float(np.isfinite(np.array(feats[n][t])[rows]).mean())) if len(rows) else None for n in NAMES)
    sig = {"kind": tag, "signal_date": dates[t], "execution": "open of next session", "hold_sessions": V25_HOLD, "quantile": QUANTILE,
           "model_refit_date": fit_at, "model_fitted_now": fitted, "n_eligible": int(mask.sum()), "n_selected": len(sel),
           "capital_yuan": capital, "feature_coverage_eligible": cover, "live_pack": pack["meta"], "names": names,
           "orders_sent": False}
    dump_json(os.path.join(SIGNALS, "%s_%s.json" % (tag, dates[t])), sig)
    print(TAG, tag, dates[t], "eligible", sig["n_eligible"], "selected", len(sel), "model", fit_at, flush=True)
    return sig, scores


def eligibility(pack):
    return eligible(pack, 20), exec_ok_matrix(pack)
