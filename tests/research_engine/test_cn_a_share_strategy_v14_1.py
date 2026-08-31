# -*- coding: utf-8 -*-
import inspect
import unittest

from research_engine.cn_a_share_alpha.contract import build_contract
from research_engine.cn_a_share_strategy_v14_1 import (
    CAGR_TARGET,
    CANDIDATES,
    FINAL_OOS_ACCESS,
    HOLD_DAYS,
    NEW_FACTOR,
    NEW_PURCHASE,
    PARENT_CONTRACT_HASH,
    QUANTILE,
)
from research_engine.cn_a_share_strategy_v14_1 import capital_ref as cap_mod
from research_engine.cn_a_share_strategy_v14_1 import candidate_b as cand_b_mod
from research_engine.cn_a_share_strategy_v14_1.reload import reload_contract
from research_engine.cn_a_share_strategy_v14_1.synthetic import synthetic_suite


class TestV141(unittest.TestCase):
    def test_no_new_search(self):
        self.assertFalse(NEW_FACTOR)
        self.assertFalse(NEW_PURCHASE)
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        self.assertEqual(HOLD_DAYS, 20)
        self.assertEqual(QUANTILE, 0.20)
        self.assertEqual(len(CANDIDATES), 2)
        self.assertEqual(CAGR_TARGET, 0.10)

    def test_contract_hash(self):
        live = build_contract()
        self.assertEqual(live["contract_hash"], PARENT_CONTRACT_HASH)
        rec = reload_contract()
        self.assertTrue(rec["all_ok"])
        self.assertIn("DAILY_OVERLAPPING_H_DAY", rec["candidate_statistic_is"])
        self.assertIn("NON_OVERLAPPING_EVERY_HOLD", rec["canonical_strategy_is"])

    def test_synthetic_engine(self):
        syn = synthetic_suite()
        self.assertTrue(syn["all_ok"], syn)

    def test_capital_ref_is_independent(self):
        src = inspect.getsource(cap_mod)
        self.assertNotIn("from research_engine.cn_a_share_strategy_v14.engine import simulate", src)
        self.assertNotIn("feature_matrix", cap_mod.__dict__)
        self.assertNotIn("overlapping_series", cap_mod.__dict__)

    def test_candidate_b_is_independent(self):
        self.assertNotIn("overlapping_series", cand_b_mod.__dict__)
        self.assertNotIn("day_book", cand_b_mod.__dict__)
        self.assertNotIn("feature_matrix", cand_b_mod.__dict__)
        src = inspect.getsource(cand_b_mod)
        self.assertNotIn("from research_engine.cn_a_share_alpha.replay", src)
        self.assertNotIn("from research_engine.cn_a_share_alpha.features", src)

    def test_unfilled_is_cash(self):
        r = cap_mod.run_synthetic(n=4, raw=0.10, fill_mask=[False, False, False, False], start=1000.0)
        self.assertAlmostEqual(r["end"], 1000.0)
        self.assertEqual(r["fees"], 0.0)


if __name__ == "__main__":
    unittest.main()
