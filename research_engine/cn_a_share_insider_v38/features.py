"""V38-L4 feature stack: 7 trailing-window insider/holder features, fixed a priori (no search). Layer alone.

Window = WINDOW_SESSIONS trailing sessions (inclusive of t). Amounts are scaled by the stock's own 20-session mean daily
traded amount at t (liquidity-relative intensity). Names with no event inside the window are NaN on all features.
  INS_NET_AMT     sum signed yuan / mean20 amount          (+)
  INS_BUY_AMT     sum buy yuan / mean20 amount             (+)
  INS_NEG_SELL    -(sum sell yuan / mean20 amount)         (+)
  INS_NET_CNT     #buy notices - #sell notices             (+)
  INS_NET_RATIO   sum signed % of float (HOLDER table)     (+)
  INS_NEG_AGE     -(sessions since last event)             (0)
  INS_LAST_DIR    sign of last event's yuan                (+)
Ties broken by 1e-3 * tanh(INS_NET_AMT).
"""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share_insider_v38 import FEAT_CACHE, NORM, WINDOW_SESSIONS, ensure_v38l4
from research_engine.cn_a_share_insider_v38.compile import ARRAYS, compile_arrays, load_arrays

INS_FEATURES = (
    ("INS_NET_AMT", "insider", 1),
    ("INS_BUY_AMT", "insider", 1),
    ("INS_NEG_SELL", "insider", 1),
    ("INS_NET_CNT", "insider", 1),
    ("INS_NET_RATIO", "insider", 1),
    ("INS_NEG_AGE", "insider", 0),
    ("INS_LAST_DIR", "insider", 1),
)
NAMES = tuple(f[0] for f in INS_FEATURES)


def _rolling_sum(a, w):
    cs = np.cumsum(a.astype(np.float64), axis=0)
    out = cs.copy()
    out[w:] = cs[w:] - cs[:-w]
    return out


def _mean20_amount(pack):
    amt = np.array(pack["amount"], dtype=np.float64)
    amt = np.where(amt > 0, amt, np.nan)
    T = amt.shape[0]
    cs = np.nancumsum(np.where(np.isfinite(amt), amt, 0.0), axis=0)
    cnt = np.cumsum(np.isfinite(amt), axis=0)
    m = np.full(amt.shape, np.nan)
    n20 = cnt[19:] - np.concatenate([np.zeros((1, amt.shape[1])), cnt[:-20]])
    s20 = cs[19:] - np.concatenate([np.zeros((1, amt.shape[1])), cs[:-20]])
    m[19:] = np.where(n20 >= 10, s20 / np.maximum(n20, 1), np.nan)
    return m


def build_features(pack, force=False):
    ensure_v38l4()
    need = [n for n in ARRAYS if not os.path.isfile(os.path.join(NORM, n + ".npy"))]
    arrs, _ = compile_arrays(pack) if (need or force) else (load_arrays(), None)
    T, N = arrs["INS_SIGNED_YUAN"].shape
    w = WINDOW_SESSIONS
    any_evt = (arrs["INS_BUY_CNT"] + arrs["INS_SELL_CNT"]) > 0
    cnt_w = _rolling_sum(any_evt.astype(np.float32), w)
    live = cnt_w > 0
    m20 = _mean20_amount(pack)
    scale = np.where(np.isfinite(m20) & (m20 > 0), m20, np.nan)
    net = _rolling_sum(arrs["INS_SIGNED_YUAN"], w) / scale
    buy = _rolling_sum(arrs["INS_BUY_YUAN"], w) / scale
    sell = _rolling_sum(arrs["INS_SELL_YUAN"], w) / scale
    ncnt = _rolling_sum(arrs["INS_BUY_CNT"], w) - _rolling_sum(arrs["INS_SELL_CNT"], w)
    ratio = _rolling_sum(arrs["INS_SIGNED_RATIO"], w)
    # last event index (forward fill) and last direction
    idx = np.where(any_evt, np.arange(T)[:, None], -1)
    last_idx = np.maximum.accumulate(idx, axis=0)
    age = np.where(last_idx >= 0, -(np.arange(T)[:, None] - last_idx), np.nan).astype(np.float64)
    sgn = np.sign(arrs["INS_SIGNED_YUAN"])
    sgn_ff = np.where(any_evt, sgn, np.nan)
    # forward-fill sign
    last_sgn = np.full((T, N), np.nan)
    cur = np.full(N, np.nan)
    for t in range(T):
        row = sgn_ff[t]
        m = np.isfinite(row)
        cur = np.where(m, row, cur)
        last_sgn[t] = cur
    nanmask = ~live
    tb = 1e-3 * np.tanh(np.where(np.isfinite(net), net, 0.0))
    feats = {
        "INS_NET_AMT": net, "INS_BUY_AMT": buy, "INS_NEG_SELL": -sell, "INS_NET_CNT": ncnt + tb, "INS_NET_RATIO": ratio + tb,
        "INS_NEG_AGE": age + tb, "INS_LAST_DIR": last_sgn + tb,
    }
    for n in NAMES:
        a = np.where(nanmask, np.nan, feats[n]).astype(np.float32)
        feats[n] = a
        np.save(os.path.join(FEAT_CACHE, n + ".npy"), a)
    return feats
