"""V27 feature stack = V25's 14 frozen features + 10 deep-financial features (fixed a priori; no search)."""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share_findeep_v27 import FEAT_CACHE, NORM, ensure_v27
from research_engine.cn_a_share_findeep_v27.compile import ALL_ARRAYS, compile_arrays, load_arrays
from research_engine.cn_a_share_ml_v25.features import FEATURES as V25_FEATURES
from research_engine.cn_a_share_ml_v25.features import build_features as v25_build_features

# (name, layer, a_priori_long_sign_for_ML0). Signs from the accounting-anomaly literature (Sloan 1996; Cooper et al 2008;
# Ball & Brown 1968 PEAD; Novy-Marx 2013 profitability; Fama-French value). Fixed before the run.
FIN_FEATURES = (
    ("SUE_Q", "findeep", 1),            # standardized unexpected earnings, single quarter (PEAD)
    ("REV_YOY_Q", "findeep", 1),        # single-quarter revenue growth yoy
    ("NEG_ACCRUALS", "findeep", 1),     # -(EPS_ttm - CFOps_ttm)/BPS  (low accruals long)
    ("CFO_TTM_BP", "findeep", 1),       # cash flow from operations ttm / book
    ("ROE_TTM", "findeep", 1),          # EPS ttm / BPS
    ("GM_CHG", "findeep", 1),           # gross margin change yoy (pts)
    ("NEG_ASSET_GROWTH", "findeep", 1), # -(TA/TA_4q - 1)  (asset-growth anomaly)
    ("NEG_LEV_CHG", "findeep", 1),      # -(debt/asset ratio change yoy)
    ("EP_TTM", "findeep", 1),           # EPS_ttm / close  (daily price-scaled)
    ("BP", "findeep", 1),               # BPS / close      (daily price-scaled)
)
FEATURES_ML2 = V25_FEATURES + FIN_FEATURES  # 24 features: full stack
FEATURES_ML2F = FIN_FEATURES                # 10 features: financial layer alone
NAMES_ML2 = tuple(f[0] for f in FEATURES_ML2)


def build_features(pack, force=False):
    ensure_v27()
    feats = dict(v25_build_features(pack))
    need = [n for n in ALL_ARRAYS if not os.path.isfile(os.path.join(NORM, n + ".npy"))]
    if need or force:
        arrs, _ = compile_arrays(pack)
    else:
        arrs = load_arrays()
    close = np.array(pack["close"], dtype=np.float64)
    close = np.where(close > 0, close, np.nan)
    for n in ALL_ARRAYS:
        if n not in ("EPS_TTM", "BPS"):
            feats[n] = arrs[n]
    feats["EP_TTM"] = (arrs["EPS_TTM"].astype(np.float64) / close).astype(np.float32)
    feats["BP"] = (arrs["BPS"].astype(np.float64) / close).astype(np.float32)
    for n in [f[0] for f in FIN_FEATURES]:
        np.save(os.path.join(FEAT_CACHE, n + ".npy"), feats[n])
    return feats
