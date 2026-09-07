"""32 information features on the live pack: V27 findeep (10) + V38 preann (9) + insider (7) + pledge (6). No price features.
Layer packages must already be redirected by ml7_live.set_env(asof) (done in ml7_live.daily before import)."""
from __future__ import print_function

import json
import os

import numpy as np

from research_engine.ml7_live import FEATURES

TAG = "ML7_FEATURES"


def feature_list():
    from research_engine.cn_a_share_findeep_v27.features import FIN_FEATURES
    from research_engine.cn_a_share_insider_v38.features import INS_FEATURES
    from research_engine.cn_a_share_pledge_v38.features import PL_FEATURES
    from research_engine.cn_a_share_preann_v38.features import PA_FEATURES

    return tuple(FIN_FEATURES) + tuple(PA_FEATURES) + tuple(INS_FEATURES) + tuple(PL_FEATURES)


def _findeep(pack, force):
    from research_engine.cn_a_share_findeep_v27 import NORM, ensure_v27
    from research_engine.cn_a_share_findeep_v27.compile import ALL_ARRAYS, compile_arrays, load_arrays
    from research_engine.cn_a_share_findeep_v27.features import FIN_FEATURES

    ensure_v27()
    need = [n for n in ALL_ARRAYS if not os.path.isfile(os.path.join(NORM, n + ".npy"))]
    arrs = compile_arrays(pack)[0] if (need or force) else load_arrays()
    close = np.array(pack["close"], dtype=np.float64)
    close = np.where(close > 0, close, np.nan)
    feats = {}
    for n in ALL_ARRAYS:
        if n not in ("EPS_TTM", "BPS"):
            feats[n] = arrs[n]
    feats["EP_TTM"] = (arrs["EPS_TTM"].astype(np.float64) / close).astype(np.float32)
    feats["BP"] = (arrs["BPS"].astype(np.float64) / close).astype(np.float32)
    return dict((f[0], feats[f[0]]) for f in FIN_FEATURES)


def build_all(pack, elig, force):
    stamp = os.path.join(FEATURES, "PACK_STAMP.json")
    prev = json.load(open(stamp, encoding="utf-8")) if os.path.isfile(stamp) else {}
    cur = {"n_dates": len(pack["dates"]), "n_symbols": len(pack["symbols"]), "live_hash": pack["meta"]["live_hash"]}
    rebuild = force or prev != cur
    names = [f[0] for f in feature_list()]
    if not rebuild and all(os.path.isfile(os.path.join(FEATURES, n + ".npy")) for n in names):
        return dict((n, np.load(os.path.join(FEATURES, n + ".npy"))) for n in names), False
    from research_engine.cn_a_share_insider_v38.features import build_features as ins_build
    from research_engine.cn_a_share_pledge_v38.features import build_features as pl_build
    from research_engine.cn_a_share_preann_v38.features import build_features as pa_build

    feats = {}
    feats.update(_findeep(pack, force=True))
    feats.update(pa_build(pack, elig, force=True))
    feats.update(ins_build(pack, force=True))
    pl_feats, _live = pl_build(pack, force=True)
    feats.update(pl_feats)
    for n in names:
        np.save(os.path.join(FEATURES, n + ".npy"), np.asarray(feats[n], dtype=np.float32))
    json.dump(cur, open(stamp, "w", encoding="utf-8"))
    print(TAG, "rebuilt", len(names), "features", flush=True)
    return dict((n, feats[n]) for n in names), True
