"""V25 feature stack. Every feature at row t uses only information knowable at close(t) (PIT already baked in upstream).

Features (fixed a priori; sign = direction literature says is 'long'; used only by the no-fit baseline ML0):
  price   : NEG_VOL_60, NEG_VOL_120, REV_20 (-20d ret), MOM_250_20 (250d ret minus last 20d), NEG_TURN_20, NEG_LOG_AMT_20
  margin  : NEG_NET_INFLOW_20_OVER_CAP, NEG_BALANCE_OVER_CAP, NEG_BALANCE_CHG_60 (V23 arrays, PIT lag 1)
  holders : NEG_QOQ_CHANGE, NEG_HOLDERS_PER_SHARE (V24 arrays, visible after HOLD_NOTICE_DATE)
  finance : ROE_ANNUAL, YOY_NET_PROFIT_ANNUAL (V16 annual rows, visible after announcement_date)
  index   : HS300_MEMBER (as-of monthly snapshot; ML1 only, no a-priori sign)
Cached as float32 (T x N) npy under alpha_cache/v25_features.
"""
from __future__ import print_function

import json
import os

import numpy as np

from research_engine.cn_a_share_alpha.features import _rolling_sum, daily_return
from research_engine.cn_a_share_index_v20.signals import load_index_rows, member_score
from research_engine.cn_a_share_information_v16.alpha import score_matrix
from research_engine.cn_a_share_margin_v23.compile import load_arrays as load_margin_arrays
from research_engine.cn_a_share_margin_v23.signals import build_scores as margin_scores
from research_engine.cn_a_share_holders_v24 import NORM as HOLDERS_NORM
from research_engine.cn_a_share_ml_v25 import FEAT_CACHE, ROOT, ensure_v25
from research_engine.cn_a_share_strategy_v14_1.scores import vol_score

FIN_JSONL = os.path.join(ROOT, "data", "market", "cn_a_share", "financial", "normalized", "FINANCIAL_ANNUAL.jsonl")

# (name, layer, a_priori_long_sign_for_ML0)  sign=0 -> excluded from ML0 baseline
FEATURES = (
    ("NEG_VOL_60", "price", 1),
    ("NEG_VOL_120", "price", 1),
    ("REV_20", "price", 1),
    ("MOM_250_20", "price", 1),
    ("NEG_TURN_20", "price", 1),
    ("NEG_LOG_AMT_20", "price", 1),
    ("NEG_NET_INFLOW_20_OVER_CAP", "margin", 1),
    ("NEG_BALANCE_OVER_CAP", "margin", 1),
    ("NEG_BALANCE_CHG_60", "margin", 1),
    ("NEG_QOQ_CHANGE", "holders", 1),
    ("NEG_HOLDERS_PER_SHARE", "holders", 1),
    ("ROE_ANNUAL", "finance", 1),
    ("YOY_NET_PROFIT_ANNUAL", "finance", 1),
    ("HS300_MEMBER", "index", 0),
)
NAMES = tuple(f[0] for f in FEATURES)


def _feat_dir():
    """Live pipeline sets TRADEMIND_V25_FEAT_CACHE after some modules already imported FEAT_CACHE."""
    return os.environ.get("TRADEMIND_V25_FEAT_CACHE") or FEAT_CACHE


def _fpath(name):
    return os.path.join(_feat_dir(), name + ".npy")


def _price_features(pack):
    close = np.array(pack["close"], dtype=np.float64)
    ret = daily_return(close)
    out = {}
    out["NEG_VOL_60"] = vol_score(pack["close"], 60)
    out["NEG_VOL_120"] = vol_score(pack["close"], 120)
    s20, c20 = _rolling_sum(ret, 20)
    r20 = np.where(c20 == 20, s20, np.nan)
    out["REV_20"] = -r20
    s250, c250 = _rolling_sum(ret, 250)
    r250 = np.where(c250 >= 230, s250, np.nan)
    out["MOM_250_20"] = r250 - r20
    turn = np.array(pack["turn"], dtype=np.float64)
    st, ct = _rolling_sum(turn, 20)
    out["NEG_TURN_20"] = -np.where(ct == 20, st / 20.0, np.nan)
    amt = np.array(pack["amount"], dtype=np.float64)
    amt = np.where(amt > 0, amt, np.nan)
    sa, ca = _rolling_sum(amt, 20)
    out["NEG_LOG_AMT_20"] = -np.log(np.where(ca >= 15, sa / np.maximum(ca, 1), np.nan))
    return out


def _fin_rows():
    rows = []
    with open(FIN_JSONL, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_features(pack, force=False):
    ensure_v25()
    T, N = len(pack["dates"]), len(pack["symbols"])
    missing = []
    for n in NAMES:
        if force or not os.path.isfile(_fpath(n)):
            missing.append(n)
            continue
        if np.load(_fpath(n), mmap_mode="r").shape != (T, N):
            missing.append(n)
    if not missing:
        return load_features()
    built = {}
    if any(n.startswith(("NEG_VOL", "REV_", "MOM_", "NEG_TURN", "NEG_LOG_AMT")) for n in missing):
        print("V25_FEAT price", flush=True)
        built.update(_price_features(pack))
    if any(n in ("NEG_NET_INFLOW_20_OVER_CAP", "NEG_BALANCE_OVER_CAP", "NEG_BALANCE_CHG_60") for n in missing):
        print("V25_FEAT margin", flush=True)
        built.update(margin_scores(load_margin_arrays()))
    if any(n in ("NEG_QOQ_CHANGE", "NEG_HOLDERS_PER_SHARE") for n in missing):
        print("V25_FEAT holders", flush=True)
        for n in ("NEG_QOQ_CHANGE", "NEG_HOLDERS_PER_SHARE"):
            built[n] = np.load(os.path.join(HOLDERS_NORM, n + ".npy"))
    if any(n in ("ROE_ANNUAL", "YOY_NET_PROFIT_ANNUAL") for n in missing):
        print("V25_FEAT finance", flush=True)
        rows = _fin_rows()
        for n in ("ROE_ANNUAL", "YOY_NET_PROFIT_ANNUAL"):
            built[n] = score_matrix(pack, rows, n)
    if "HS300_MEMBER" in missing:
        print("V25_FEAT index", flush=True)
        built["HS300_MEMBER"] = member_score(pack, load_index_rows(), "HS300")
    for n in missing:
        arr = np.asarray(built[n], dtype=np.float32)
        if arr.shape != (T, N):
            raise RuntimeError("FEATURE_SHAPE %s %r" % (n, arr.shape))
        np.save(_fpath(n), arr)
        print("V25_FEAT saved", n, "finite_frac=%.3f" % float(np.isfinite(arr).mean()), flush=True)
    return load_features()


def load_features():
    return dict((n, np.load(_fpath(n), mmap_mode="r")) for n in NAMES)


def cs_rank_row(x, mask):
    """Cross-sectional rank in [0,1] over mask & finite; NaN elsewhere."""
    out = np.full(x.shape, np.nan, dtype=np.float32)
    idx = np.where(mask & np.isfinite(x))[0]
    if idx.size < 2:
        return out
    order = np.argsort(x[idx], kind="stable")
    ranks = np.empty(idx.size, dtype=np.float64)
    ranks[order] = np.arange(idx.size, dtype=np.float64)
    out[idx] = (ranks / float(idx.size - 1)).astype(np.float32)
    return out


BINARY = ("HS300_MEMBER",)


def ranked_row(feats, t, mask, names=NAMES):
    """(N x F) ranked feature block for session t."""
    cols = []
    for n in names:
        x = np.array(feats[n][t], dtype=np.float64)
        if n in BINARY:
            r = np.where(mask & np.isfinite(x), x, np.nan).astype(np.float32)
        else:
            r = cs_rank_row(x, mask)
        cols.append(r)
    return np.stack(cols, axis=1)
