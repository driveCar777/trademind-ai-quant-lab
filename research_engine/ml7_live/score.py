"""ML7 model on the REFIT_240 schedule (same dates as ML1 live) + top-20% list per session. Output-only."""
from __future__ import print_function

import os
import pickle
import time

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_ml_v25 import EMBARGO, FIRST_PRED, HOLD_DAYS, LGBM_PARAMS, RESEARCH, TRAIN_STRIDE
from research_engine.cn_a_share_ml_v25.features import ranked_row
from research_engine.cn_a_share_ml_v25.model import _first_at_or_after, _label_row, forward_open_matrix
from research_engine.cn_a_share_strategy_v14_1.scores import pick_lexsort
from research_engine.ml1_live import LIVE_REFIT, LOT, QUANTILE
from research_engine.ml7_live import ML7_ID, MODELS, SIGNALS
from research_engine.ml7_live.features import feature_list

TAG = "ML7_SCORE"


def refit_dates(dates, upto_index):
    i_first = _first_at_or_after(dates, FIRST_PRED)
    return [s for s in range(i_first, upto_index + 1, LIVE_REFIT)]


def model_for(pack, feats, elig, xok, t):
    import lightgbm as lgb

    names = tuple(f[0] for f in feature_list())
    dates = pack["dates"]
    s = refit_dates(dates, t)[-1]
    path = os.path.join(MODELS, "ML7_REFIT_%s.pkl" % dates[s])
    if os.path.isfile(path):
        with open(path, "rb") as fh:
            return pickle.load(fh), dates[s], False
    t0 = time.time()
    cutoff = s - EMBARGO
    i_res_start = _first_at_or_after(dates, RESEARCH[0])
    fwd = forward_open_matrix(pack, HOLD_DAYS, cutoff)
    Xs, ys = [], []
    for g in range(i_res_start, cutoff + 1, TRAIN_STRIDE):
        mask = elig[g] & np.isfinite(fwd[g]) & xok[g + 1]
        if int(mask.sum()) < 100:
            continue
        X = ranked_row(feats, g, mask, names)
        y = _label_row(fwd[g], mask)
        keep = mask & np.isfinite(y)
        Xs.append(X[keep])
        ys.append(y[keep])
    model = lgb.LGBMRegressor(**LGBM_PARAMS)
    model.fit(np.concatenate(Xs), np.concatenate(ys))
    imp = model.booster_.feature_importance(importance_type="gain")
    imp = (imp / max(float(imp.sum()), 1e-12)).tolist()
    meta = {"id": ML7_ID, "fit_at": dates[s], "train_last_label_session": dates[cutoff], "train_rows": int(sum(len(y) for y in ys)),
            "params": LGBM_PARAMS, "features": list(names), "gain_share": dict(zip(names, [round(v, 4) for v in imp])), "sec": round(time.time() - t0, 1),
            "note": "all history up to the refit date is training data (contract: no historical window is an evaluation window for ML7)"}
    with open(path, "wb") as fh:
        pickle.dump(model, fh)
    dump_json(path.replace(".pkl", ".json"), meta)
    print(TAG, "fitted", meta["fit_at"], "rows", meta["train_rows"], "%.0fs" % meta["sec"], flush=True)
    return model, dates[s], True


def score_session(pack, feats, elig, xok, t, capital, tag="SIGNAL_ML7"):
    names = tuple(f[0] for f in feature_list())
    dates = pack["dates"]
    model, fit_at, fitted = model_for(pack, feats, elig, xok, t)
    mask = elig[t]
    Xt = ranked_row(feats, t, mask, names)
    rows = np.where(mask)[0]
    scores = np.full(len(pack["symbols"]), np.nan, dtype=np.float32)
    scores[rows] = model.predict(Xt[rows]).astype(np.float32)
    js = pick_lexsort(scores, mask)
    sel = [int(j) for j in js] if js is not None else []
    close = np.array(pack["close"][t], dtype=np.float64)
    w = 1.0 / len(sel) if sel else 0.0
    out_names = []
    for j in sel:
        px = float(close[j]) if np.isfinite(close[j]) else None
        out_names.append({"symbol": pack["symbols"][j], "score": float(scores[j]), "weight": w, "target_yuan": round(capital * w, 2),
                          "last_close": px, "lots_100": int((capital * w) // (px * LOT)) if px else None})
    cover = dict((n, float(np.isfinite(np.array(feats[n][t])[rows]).mean())) if len(rows) else None for n in names)
    sig = {"kind": tag, "id": ML7_ID, "signal_date": dates[t], "execution": "open of next session", "hold_sessions": HOLD_DAYS, "quantile": QUANTILE,
           "model_refit_date": fit_at, "model_fitted_now": fitted, "n_eligible": int(mask.sum()), "n_selected": len(sel), "capital_yuan": capital,
           "feature_coverage_eligible": cover, "live_pack": pack["meta"], "names": out_names, "orders_sent": False,
           "read_rule": "not evaluated before >= 24 closed periods (V38_S3_INFO_STACK_CONTRACT.md)"}
    dump_json(os.path.join(SIGNALS, "%s_%s.json" % (tag, dates[t])), sig)
    print(TAG, tag, dates[t], "eligible", sig["n_eligible"], "selected", len(sel), "model", fit_at, flush=True)
    return sig, scores
