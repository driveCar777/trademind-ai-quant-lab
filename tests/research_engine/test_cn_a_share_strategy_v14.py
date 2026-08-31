# -*- coding: utf-8 -*-
import inspect
import unittest

from research_engine.cn_a_share_alpha.contract import build_contract
from research_engine.cn_a_share_strategy_v14 import (
    CAGR_TARGET,
    FINAL_OOS_ACCESS,
    HOLD_DAYS,
    LEVERAGE,
    LONG_ONLY,
    NEW_FACTOR,
    NEW_PURCHASE,
    PARENT_CONTRACT_HASH,
    QUANTILE,
    STRATEGIES,
)
from research_engine.cn_a_share_strategy_v14 import engine as engine_mod
from research_engine.cn_a_share_strategy_v14.reload import reload_contract
from research_engine.cn_a_share_strategy_v14.spec import build_spec


class TestV14(unittest.TestCase):
    def test_no_new_search(self):
        self.assertFalse(NEW_FACTOR)
        self.assertFalse(NEW_PURCHASE)
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        self.assertEqual(HOLD_DAYS, 20)
        self.assertEqual(QUANTILE, 0.20)
        self.assertEqual(LEVERAGE, 1.0)
        self.assertTrue(LONG_ONLY)
        self.assertEqual(len(STRATEGIES), 2)
        self.assertEqual(CAGR_TARGET, 0.10)

    def test_contract_hash_is_authority(self):
        live = build_contract()
        self.assertEqual(live["contract_hash"], PARENT_CONTRACT_HASH)
        rec = reload_contract()
        self.assertTrue(rec["checks"]["all_ok"])
        self.assertEqual(rec["translation"]["strategy_accounting"], "NON_OVERLAPPING_EVERY_HOLD")

    def test_spec_locks_cluster(self):
        spec = build_spec()
        self.assertEqual(spec["canonical_per_candidate"], 1)
        self.assertTrue(spec["no_h11_h12_blend"])
        self.assertEqual(spec["unfilled"], "WEIGHT_STAYS_CASH")
        self.assertIn("delist_contract_gap", spec)

    def test_engine_is_independent(self):
        src = inspect.getsource(engine_mod)
        self.assertNotIn("from research_engine.cn_a_share_alpha.features", src)
        self.assertNotIn("from research_engine.cn_a_share_alpha.replay", src)
        self.assertNotIn("feature_matrix", engine_mod.__dict__)
        self.assertNotIn("day_book", engine_mod.__dict__)

    def test_level2_does_not_use_10pct(self):
        spec = build_spec()
        self.assertIn("cagr_target_not_a_gate", spec)
        self.assertNotIn("cagr >= 0.10", spec["level2_gate"])


if __name__ == "__main__":
    unittest.main()
