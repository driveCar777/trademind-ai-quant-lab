# -*- coding: utf-8 -*-
import unittest

from research_engine.cn_a_share_alpha_v2 import (
    FINAL_OOS_ACCESS,
    HOLDS_ALLOWED,
    LOOKBACKS_ALLOWED,
    MAX_HYPOTHESES,
    NEW_H13,
    NEW_PURCHASE,
    REOPEN_H11_H12,
)
import numpy as np

from research_engine.cn_a_share_alpha_v2.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_alpha_v2.signals import _rolling_sum, neg_ret_amount_corr
from research_engine.cn_a_share_strategy_v14_1.capital_ref import run_synthetic


class TestV15(unittest.TestCase):
    def test_lock(self):
        self.assertEqual(len(HYPOTHESES), 9)
        self.assertEqual(MAX_HYPOTHESES, 9)
        self.assertFalse(NEW_PURCHASE)
        self.assertFalse(REOPEN_H11_H12)
        self.assertFalse(NEW_H13)
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        ids = [h["id"] for h in HYPOTHESES]
        self.assertEqual(len(ids), len(set(ids)))
        for hid in ids:
            self.assertFalse(hid.startswith("H11"))
            self.assertFalse(hid.startswith("H12"))
            self.assertFalse(hid.startswith("H13"))
        for h in HYPOTHESES:
            self.assertIn(h["lookback"], LOOKBACKS_ALLOWED)
            self.assertIn(h["hold_days"], HOLDS_ALLOWED)

    def test_contract_hash_stable(self):
        a = build_contract()
        b = build_contract()
        self.assertEqual(a["contract_hash"], b["contract_hash"])
        self.assertTrue(a["predictive_is_not_cagr"])
        self.assertEqual(a["cagr_only_from"], "CANONICAL_CAPITAL_ACCOUNT")
        self.assertEqual(a["predictive_metric_name"], "MEAN_FORWARD_RETURN")
        self.assertEqual(a["h11_h12"], "KEEP_LOW_PRIORITY")
        self.assertEqual(len(a["hypotheses"]), 9)

    def test_families(self):
        fams = set(h["family"] for h in HYPOTHESES)
        self.assertEqual(fams, {"CROSS_SECTIONAL_RESIDUAL", "MARKET_DISPERSION_STATE", "PRICE_ACTIVITY_DISAGREEMENT"})
        for fam in fams:
            self.assertLessEqual(sum(1 for h in HYPOTHESES if h["family"] == fam), 3)

    def test_capital_unfilled(self):
        r = run_synthetic(n=4, raw=0.10, fill_mask=[False, False, False, False], start=1000.0)
        self.assertAlmostEqual(r["end"], 1000.0)
        self.assertEqual(r["fees"], 0.0)

    def test_rolling_sum_int32_and_window(self):
        x = np.array([[1.0, np.nan], [3.0, 4.0], [5.0, 6.0]], dtype=np.float64)
        s, n = _rolling_sum(x, 2)
        self.assertEqual(n.dtype, np.int32)
        self.assertTrue(np.isnan(s[0, 0]))
        self.assertEqual(int(n[1, 0]), 2)
        self.assertAlmostEqual(float(s[1, 0]), 4.0)
        self.assertEqual(int(n[1, 1]), 1)

    def test_neg_corr_chunk_matches_full_window(self):
        rng = np.random.RandomState(0)
        ret = rng.normal(size=(40, 12))
        amt = np.exp(rng.normal(size=(40, 12)))
        a = neg_ret_amount_corr(ret, amt, 8, chunk=5)
        b = neg_ret_amount_corr(ret, amt, 8, chunk=12)
        self.assertTrue(np.allclose(a[8:], b[8:], equal_nan=True))


if __name__ == "__main__":
    unittest.main()
