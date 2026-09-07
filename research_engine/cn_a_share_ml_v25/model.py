"""Walk-forward cross-sectional model. Expanding window, purged by EMBARGO, refit every REFIT_EVERY sessions during RESEARCH,
frozen at RESEARCH end (validation and RB5 scored by the frozen model). Produces (T x N) score matrices.

ML1_LGBM   : LightGBM regression on cross-sectionally ranked features -> rank-demeaned 20-session forward open->open return.
ML0_RANKAVG: no-fit baseline, mean of a-priori-signed feature ranks (HS300_MEMBER excluded).
"""
from __future__ import print_function

import time

import numpy as np

from research_engine.cn_a_share_ml_v25 import (
    EMBARGO, FIRST_PRED, HOLD_DAYS, LGBM_PARAMS, NO_REFIT_AFTER_RESEARCH, REFIT_EVERY, RESEARCH, TRAIN_STRIDE, VALIDATION,
)
from research_engine.cn_a_share_ml_v25.features import FEATURES, NAMES, cs_rank_row, ranked_row


def _first_at_or_after(dates, day):
    for i, d in enumerate(dates):
        if d >= day:
            return i
    raise RuntimeError("DATE_NOT_IN_PACK %s" % day)


def _last_at_or_before(dates, day):
    k = None
    for i, d in enumerate(dates):
        if d <= day:
            k = i
        else:
            break
    if k is None:
        raise RuntimeError("DATE_NOT_IN_PACK %s" % day)
    return k


def forward_open_matrix(pack, hold, t_end, chunk=400):
    """fwd[t, j] = open[t+1+hold, j] / open[t+1, j] - 1 for t <= t_end (NaN beyond)."""
    T, N = pack["open"].shape
    out = np.full((T, N), np.nan, dtype=np.float32)
    for j0 in range(0, N, chunk):
        o = np.array(pack["open"][:, j0:j0 + chunk], dtype=np.float64)
        a = o[1:T - hold]
        b = o[1 + hold:]
        good = np.isfinite(a) & np.isfinite(b) & (a > 0)
        r = np.where(good, b / a - 1.0, np.nan)
        out[:T - 1 - hold, j0:j0 + chunk] = r.astype(np.float32)
    out[t_end + 1:] = np.nan
    return out


def _label_row(fwd_t, mask):
    r = cs_rank_row(np.array(fwd_t, dtype=np.float64), mask)
    return r - np.float32(0.5)


def build_scores(pack, feats, elig, xok, features=FEATURES, tag="V25_MODEL"):
    """features: tuple of (name, layer, ml0_sign). Defaults = V25 contract. Other callers (V27) pass their own fixed list."""
    import lightgbm as lgb

    names = tuple(f[0] for f in features)
    dates = pack["dates"]
    T, N = len(dates), len(pack["symbols"])
    i_first = _first_at_or_after(dates, FIRST_PRED)
    i_res_end = _last_at_or_before(dates, RESEARCH[1])
    i_val_end = _last_at_or_before(dates, VALIDATION[1])
    fwd = forward_open_matrix(pack, HOLD_DAYS, i_val_end)

    # training-row cache on the stride grid: ranked features + rank label, eligible & label-finite only
    i_res_start = _first_at_or_after(dates, RESEARCH[0])
    grid = [t for t in range(i_res_start, i_res_end - EMBARGO + 1) if (t - i_res_start) % TRAIN_STRIDE == 0]
    Xs, ys, ts = {}, {}, {}
    print(tag, "grid", len(grid), "sessions", flush=True)
    for t in grid:
        mask = elig[t] & np.isfinite(fwd[t]) & xok[t + 1]
        if int(mask.sum()) < 100:
            continue
        X = ranked_row(feats, t, mask, names)
        y = _label_row(fwd[t], mask)
        keep = mask & np.isfinite(y)
        Xs[t] = X[keep]
        ys[t] = y[keep]
        ts[t] = int(keep.sum())
    if not NO_REFIT_AFTER_RESEARCH:
        raise RuntimeError("REFIT_AFTER_RESEARCH_NOT_ALLOWED_BY_CONTRACT")
    refits = list(range(i_first, i_res_end + 1, REFIT_EVERY))
    np.seterr(invalid="ignore")
    ml1 = np.full((T, N), np.nan, dtype=np.float32)
    ml0 = np.full((T, N), np.nan, dtype=np.float32)
    meta = {"refits": [], "n_features": len(names), "features": list(names), "first_pred": dates[i_first],
            "research_end_index": i_res_end, "validation_end_index": i_val_end, "frozen_after_research": NO_REFIT_AFTER_RESEARCH}
    signed = np.array([f[2] for f in features], dtype=np.float32)
    use0 = signed != 0
    for k, s in enumerate(refits):
        t0 = time.time()
        cutoff = s - EMBARGO  # labels of row t are fully known at open(t+1+hold) <= open(s) -> t+1+hold <= s
        tr = [t for t in grid if t <= cutoff and t in Xs]
        X = np.concatenate([Xs[t] for t in tr], axis=0)
        y = np.concatenate([ys[t] for t in tr], axis=0)
        model = lgb.LGBMRegressor(**LGBM_PARAMS)
        model.fit(X, y)
        s_end = refits[k + 1] - 1 if k + 1 < len(refits) else i_val_end
        for t in range(s, s_end + 1):
            mask = elig[t]
            if int(mask.sum()) < 100:
                continue
            Xt = ranked_row(feats, t, mask, names)
            rows = np.where(mask)[0]
            ml1[t, rows] = model.predict(Xt[rows]).astype(np.float32)
            blk = Xt[rows][:, use0]
            cnt = np.isfinite(blk).sum(axis=1)
            avg = np.where(cnt >= 3, np.nanmean(np.where(np.isfinite(blk), blk, np.nan), axis=1), np.nan)
            ml0[t, rows] = avg.astype(np.float32)
        imp = model.booster_.feature_importance(importance_type="gain")
        imp = (imp / max(float(imp.sum()), 1e-12)).tolist()
        meta["refits"].append({"fit_at": dates[s], "train_rows": int(X.shape[0]), "train_sessions": len(tr),
                               "train_last_label_session": dates[cutoff], "scores_until": dates[s_end],
                               "gain_share": dict(zip(names, [round(v, 4) for v in imp])), "sec": round(time.time() - t0, 1)})
        print(tag, "refit", k + 1, "/", len(refits), dates[s], "rows", X.shape[0], "->", dates[s_end], "%.0fs" % (time.time() - t0), flush=True)
    return {"ML1_LGBM": ml1, "ML0_RANKAVG": ml0}, meta
