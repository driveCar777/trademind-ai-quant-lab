"""V38-L1 feature stack: 9 pre-announcement features, fixed a priori (no search). Layer alone (no V25 features).

Event-static (from compile.py): PA_SURPRISE, PA_TYPE, PA_REV, PA_NEG_UNCERT, PA_LEAD.
Event-reaction (from the price pack, keyed on the event session t1 = PA_EVT_INDEX):
  PA_JOR      = open(t1)/close(t1-1) - 1 minus the eligible cross-sectional mean of the same (announcement-day gap; 天风 JOR)
  PA_CAR3     = close(t1+2)/close(t1-1) - 1 minus cross-sectional mean (3-session reaction; visible from t1+2)
  PA_ABNVOL   = amount(t1) / mean amount(t1-20 .. t1-1)
  PA_NEG_AGE  = -(t - t1) sessions since the event (fresh = high)
Ties in PA_TYPE / PA_NEG_AGE are broken deterministically by a 1e-3 * clipped-surprise term (cs_rank_row breaks exact ties by index).
"""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share_preann_v38 import FEAT_CACHE, NORM, ensure_v38l1
from research_engine.cn_a_share_preann_v38.compile import ALL_ARRAYS, STATIC, compile_arrays, load_arrays

PA_FEATURES = (
    ("PA_SURPRISE", "preann", 1),
    ("PA_TYPE", "preann", 1),
    ("PA_REV", "preann", 1),
    ("PA_NEG_UNCERT", "preann", 1),
    ("PA_LEAD", "preann", 1),
    ("PA_JOR", "preann", 1),
    ("PA_CAR3", "preann", 1),
    ("PA_ABNVOL", "preann", 0),
    ("PA_NEG_AGE", "preann", 0),
)
NAMES = tuple(f[0] for f in PA_FEATURES)


def _reaction_arrays(pack, evt, elig):
    """Per-session cross-sectional stats computed once, then looked up at each stock's event session."""
    close = np.array(pack["close"], dtype=np.float64)
    opn = np.array(pack["open"], dtype=np.float64)
    amt = np.array(pack["amount"], dtype=np.float64)
    close = np.where(close > 0, close, np.nan)
    opn = np.where(opn > 0, opn, np.nan)
    amt = np.where(amt > 0, amt, np.nan)
    T, N = close.shape
    gap = np.full((T, N), np.nan)
    gap[1:] = opn[1:] / close[:-1] - 1.0
    car3 = np.full((T, N), np.nan)
    car3[3:] = close[3:] / close[:-3] - 1.0          # close(t)/close(t-3): at row t1+2 this is close(t1+2)/close(t1-1)
    # rolling 20-session mean amount ending at t-1
    cs = np.nancumsum(np.where(np.isfinite(amt), amt, 0.0), axis=0)
    cnt = np.cumsum(np.isfinite(amt), axis=0)
    mean20 = np.full((T, N), np.nan)
    n20 = cnt[20:-1] - cnt[:-21]
    mean20[21:] = np.where(n20 >= 10, (cs[20:-1] - cs[:-21]) / np.maximum(n20, 1), np.nan)
    abnvol = amt / mean20
    # cross-sectional means over eligible names per session
    def cs_mean(a):
        m = np.where(elig & np.isfinite(a), a, np.nan)
        with np.errstate(all="ignore"):
            return np.nanmean(m, axis=1)
    gap_m, car_m = cs_mean(gap), cs_mean(car3)
    jor = np.full((T, N), np.nan, dtype=np.float32)
    car = np.full((T, N), np.nan, dtype=np.float32)
    abv = np.full((T, N), np.nan, dtype=np.float32)
    age = np.full((T, N), np.nan, dtype=np.float32)
    for j in range(N):
        e = evt[:, j]
        idx = np.where(e >= 0)[0]
        if idx.size == 0:
            continue
        t1 = e[idx]
        jor[idx, j] = (gap[t1, j] - gap_m[t1]).astype(np.float32)
        t3 = t1 + 2
        ok3 = (t3 <= idx)  # visible only once t1+2 has closed
        v3 = np.where(ok3 & (t3 < T), car3[np.minimum(t3, T - 1), j] - car_m[np.minimum(t3, T - 1)], np.nan)
        car[idx, j] = v3.astype(np.float32)
        abv[idx, j] = abnvol[t1, j].astype(np.float32)
        age[idx, j] = (-(idx - t1)).astype(np.float32)
    return {"PA_JOR": jor, "PA_CAR3": car, "PA_ABNVOL": abv, "PA_NEG_AGE": age}


def build_features(pack, elig, force=False):
    ensure_v38l1()
    need = [n for n in ALL_ARRAYS if not os.path.isfile(os.path.join(NORM, n + ".npy"))]
    arrs, _ = compile_arrays(pack) if (need or force) else (load_arrays(), None)
    feats = {}
    for n in STATIC:
        feats[n] = arrs[n]
    feats.update(_reaction_arrays(pack, arrs["PA_EVT_INDEX"], elig))
    tb = np.where(np.isfinite(feats["PA_SURPRISE"]), np.clip(feats["PA_SURPRISE"], -500, 500) / 500.0, 0.0).astype(np.float32)
    feats["PA_TYPE"] = (feats["PA_TYPE"] + 1e-3 * tb).astype(np.float32)
    feats["PA_NEG_AGE"] = (feats["PA_NEG_AGE"] + 1e-3 * tb).astype(np.float32)
    for n in NAMES:
        np.save(os.path.join(FEAT_CACHE, n + ".npy"), feats[n])
    return feats
