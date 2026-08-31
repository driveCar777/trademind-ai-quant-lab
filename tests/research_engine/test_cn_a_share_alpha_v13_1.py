# -*- coding: utf-8 -*-
import inspect
import unittest

import numpy as np

from research_engine.cn_a_share_alpha.contract import build_contract
from research_engine.cn_a_share_alpha.features import feature_matrix
from research_engine.cn_a_share_alpha_v13_1 import (
    CANDIDATES,
    FINAL_OOS_ACCESS,
    HOLD_DAYS,
    NEW_FACTOR,
    NEW_PURCHASE,
    PARENT_CONTRACT_HASH,
    QUANTILE,
)
from research_engine.cn_a_share_alpha_v13_1 import path_b as path_b_mod
from research_engine.cn_a_share_alpha_v13_1.path_b import vol_score_b
from research_engine.cn_a_share_alpha_v13_1.reload import reload_contract


class TestV131(unittest.TestCase):
    def test_no_new_search(self):
        self.assertFalse(NEW_FACTOR)
        self.assertFalse(NEW_PURCHASE)
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        self.assertEqual(len(CANDIDATES), 2)
        self.assertEqual(HOLD_DAYS, 20)
        self.assertEqual(QUANTILE, 0.20)

    def test_contract_hash_is_authority(self):
        live = build_contract()
        self.assertEqual(live["contract_hash"], PARENT_CONTRACT_HASH)
        rec = reload_contract()
        self.assertTrue(rec["checks"]["hash_match"])
        self.assertTrue(rec["checks"]["all_ok"])
        self.assertTrue(rec["checks"]["candidates"]["H11_VOL_60"]["lookback"])
        self.assertTrue(rec["checks"]["candidates"]["H12_VOL_120"]["lookback"])

    def test_path_b_does_not_call_v13_book(self):
        imported = getattr(path_b_mod, "__dict__", {})
        self.assertNotIn("feature_matrix", imported)
        self.assertNotIn("overlapping_series", imported)
        self.assertNotIn("day_book", imported)
        self.assertNotIn("round_trip_cost", imported)
        src = inspect.getsource(path_b_mod)
        self.assertNotIn("from research_engine.cn_a_share_alpha.features", src)
        self.assertNotIn("from research_engine.cn_a_share_alpha.replay", src)

    def test_path_b_vol_matches_path_a_on_toy(self):
        rng = np.random.RandomState(20260831)
        close = 10.0 + np.cumsum(rng.randn(180, 40) * 0.01, axis=0)
        pack = {"close": close, "turn": np.ones_like(close)}
        a = feature_matrix(pack, "CROSS_SECTIONAL_VOLATILITY", 60)
        b = vol_score_b(close, 60)
        both = np.isfinite(a) & np.isfinite(b)
        self.assertTrue(np.any(both))
        self.assertLess(float(np.max(np.abs(a[both] - b[both]))), 1e-10)


if __name__ == "__main__":
    unittest.main()
