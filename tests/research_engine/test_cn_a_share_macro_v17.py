# -*- coding: utf-8 -*-
import unittest

import numpy as np

from research_engine.cn_a_share_macro_v17 import (
    FINAL_OOS_ACCESS,
    MAX_HYPOTHESES,
    NEW_H13,
    NEW_PURCHASE,
    PRICE_ONLY_REOPEN,
    REOPEN_H11_H12,
    REOPEN_V16,
)
from research_engine.cn_a_share_macro_v17.compile import REQUIRED
from research_engine.cn_a_share_macro_v17.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_macro_v17.evaluate import decide
from research_engine.cn_a_share_macro_v17.macro import asof_align, last_macro_date_used
from research_engine.cn_a_share_macro_v17.signals import rolling_beta_block


class TestV17(unittest.TestCase):
    def test_locks(self):
        self.assertFalse(NEW_PURCHASE)
        self.assertFalse(REOPEN_H11_H12)
        self.assertFalse(PRICE_ONLY_REOPEN)
        self.assertFalse(REOPEN_V16)
        self.assertFalse(NEW_H13)
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        self.assertEqual(len(HYPOTHESES), 6)
        self.assertEqual(len(HYPOTHESES), MAX_HYPOTHESES)
        self.assertTrue(all(h["hold_days"] == 20 for h in HYPOTHESES))
        self.assertFalse(any(h["id"].startswith("H11") or h["id"].startswith("F") for h in HYPOTHESES))

    def test_contract_hash_stable(self):
        a = build_contract()
        b = build_contract()
        self.assertEqual(a["contract_hash"], b["contract_hash"])
        self.assertTrue(a["predictive_is_not_cagr"])
        self.assertEqual(a["predictive_metric_name"], "MEAN_FORWARD_RETURN")
        self.assertEqual(a["pit_rule"], "MACRO_CALENDAR_DATE_STRICTLY_BEFORE_ASHARE_SIGNAL_DATE")
        self.assertIn("DXY", a["unused_short_macros"])

    def test_asof_no_same_day_leak(self):
        macro_dates = ["2010-01-04", "2010-01-05", "2010-01-06"]
        macro_vals = np.array([0.1, 0.2, 0.3], dtype=np.float64)
        cn = ["2010-01-05", "2010-01-06", "2010-01-07"]
        aligned = asof_align(cn, macro_dates, macro_vals)
        self.assertAlmostEqual(aligned[0], 0.1)
        self.assertAlmostEqual(aligned[1], 0.2)
        self.assertAlmostEqual(aligned[2], 0.3)
        self.assertEqual(last_macro_date_used("2010-01-05", macro_dates), "2010-01-04")
        self.assertNotEqual(last_macro_date_used("2010-01-05", macro_dates), "2010-01-05")

    def test_asof_empty_before_history(self):
        aligned = asof_align(["2009-01-01"], ["2010-01-04"], np.array([1.0]))
        self.assertTrue(np.isnan(aligned[0]))

    def test_rolling_beta_known(self):
        rng = np.random.RandomState(0)
        x = rng.normal(0.0, 1.0, size=80)
        y = (2.0 * x + rng.normal(0.0, 0.01, size=80)).reshape(80, 1)
        beta = rolling_beta_block(y, x, 40)
        self.assertTrue(np.isnan(beta[38, 0]))
        self.assertAlmostEqual(float(beta[-1, 0]), 2.0, places=1)

    def test_decide_no_candidate(self):
        d = decide([], True)
        self.assertEqual(d["STOP"], "STOP_B_FAMILY")
        self.assertEqual(d["NEW_INDEPENDENT_CANDIDATE"], 0)
        self.assertEqual(d["OVERALL"], "A_SHARE_MACRO_INFORMATION_V1_NO_CANDIDATE")
        self.assertEqual(d["CANDIDATE"], 2)

    def test_decide_independent_stops_a(self):
        d = decide([{"id": "M1_USD_DEF_60", "cluster_tag": "POTENTIALLY_INDEPENDENT"}], True)
        self.assertEqual(d["STOP"], "STOP_A")
        self.assertEqual(d["NEXT"], "CANDIDATE_REPRODUCTION")

    def test_required_reports(self):
        self.assertEqual(len(REQUIRED), 5)
        self.assertIn("V17_MACRO_DECISION.md", REQUIRED)


if __name__ == "__main__":
    unittest.main()
