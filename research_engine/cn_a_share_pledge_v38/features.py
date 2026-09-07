"""V38-L7 feature stack: 6 pledge features, fixed a priori (no search). Layer alone.

  PL_NEG_RATIO   -(pledge ratio %)                                    (+)  high pledge = crash risk
  PL_NEG_D20     -(ratio_t - ratio_{t-20})                            (+)  rising pledge = controller liquidity stress
  PL_NEG_D60     -(ratio_t - ratio_{t-60})                            (+)
  PL_NEG_DEALS   -log1p(outstanding deals)                            (+)  many small deals = fragmented lenders
  PL_NEG_MCAP    -(pledged market cap / 20-session mean daily amount) (+)  pledge overhang relative to liquidity
  PL_STRESS      ratio% * min(ret60, 0) / 100                         (+)  more negative = closer to forced liquidation
Names without a snapshot state (layer not live) are NaN on all features.
"""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share_pledge_v38 import FEAT_CACHE, NORM, ensure_v38l7
from research_engine.cn_a_share_pledge_v38.compile import ARRAYS, compile_arrays, load_arrays

PL_FEATURES = (
    ("PL_NEG_RATIO", "pledge", 1),
    ("PL_NEG_D20", "pledge", 1),
    ("PL_NEG_D60", "pledge", 1),
    ("PL_NEG_DEALS", "pledge", 1),
    ("PL_NEG_MCAP", "pledge", 1),
    ("PL_STRESS", "pledge", 1),
)
NAMES = tuple(f[0] for f in PL_FEATURES)


def _mean20_amount(pack):
    amt = np.array(pack["amount"], dtype=np.float64)
    amt = np.where(amt > 0, amt, np.nan)
    cs = np.nancumsum(np.where(np.isfinite(amt), amt, 0.0), axis=0)
    cnt = np.cumsum(np.isfinite(amt), axis=0)
    m = np.full(amt.shape, np.nan)
    n20 = cnt[19:] - np.concatenate([np.zeros((1, amt.shape[1])), cnt[:-20]])
    s20 = cs[19:] - np.concatenate([np.zeros((1, amt.shape[1])), cs[:-20]])
    m[19:] = np.where(n20 >= 10, s20 / np.maximum(n20, 1), np.nan)
    return m


def _lag(a, k):
    out = np.full_like(a, np.nan)
    out[k:] = a[:-k]
    return out


def build_features(pack, force=False):
    ensure_v38l7()
    need = [n for n in ARRAYS if not os.path.isfile(os.path.join(NORM, n + ".npy"))]
    arrs, _ = compile_arrays(pack) if (need or force) else (load_arrays(), None)
    ratio = arrs["PL_RATIO_ST"].astype(np.float64)
    live = np.isfinite(arrs["PL_LIVE"])
    m20 = _mean20_amount(pack)
    scale = np.where(np.isfinite(m20) & (m20 > 0), m20, np.nan)
    close = np.array(pack["close"], dtype=np.float64)
    close = np.where(close > 0, close, np.nan)
    ret60 = close / _lag(close, 60) - 1.0
    feats = {
        "PL_NEG_RATIO": -ratio,
        "PL_NEG_D20": -(ratio - _lag(ratio, 20)),
        "PL_NEG_D60": -(ratio - _lag(ratio, 60)),
        "PL_NEG_DEALS": -np.log1p(np.maximum(arrs["PL_DEALS_ST"].astype(np.float64), 0.0)),
        "PL_NEG_MCAP": -(arrs["PL_MCAP_ST"].astype(np.float64) / scale),
        "PL_STRESS": ratio * np.minimum(np.where(np.isfinite(ret60), ret60, 0.0), 0.0) / 100.0,
    }
    for n in NAMES:
        a = np.where(live, feats[n], np.nan).astype(np.float32)
        feats[n] = a
        np.save(os.path.join(FEAT_CACHE, n + ".npy"), a)
    return feats, live
