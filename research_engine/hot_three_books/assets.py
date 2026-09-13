"""Shared frozen pack + ML1 scores. Read-only."""
from __future__ import annotations

import os
from typing import Any, Tuple

import numpy as np

from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.cn_a_share_ml_v25 import OUT
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix

SCORES = os.path.join(OUT, "SCORES_ML1_LGBM.npy")
_CACHE = None

SHELL = dict(
    capital=20000.0,
    boards="MAIN",
    max_price=100.0,
    eq_money=True,
    exposure=1.0,
    topup=True,
    monthly_contrib=2000.0,
    n_target=10,
)


def load_assets() -> Tuple[Any, Any, Any, Any]:
    global _CACHE
    if _CACHE is None:
        pack = load_pack()
        scores = np.load(SCORES, mmap_mode="r")
        elig, xok = eligible(pack, 20), exec_ok_matrix(pack)
        _CACHE = (pack, scores, elig, xok)
    return _CACHE
