# -*- coding: utf-8 -*-
import unittest

import numpy as np

from research_engine.cn_a_share_index_v20 import ADD_LOOKBACK, FINAL_OOS_ACCESS, MAX_HYPOTHESES, NEW_PURCHASE, REOPEN_H11_H12, REOPEN_V16
from research_engine.cn_a_share_index_v20.books import pick_set
from research_engine.cn_a_share_index_v20.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_index_v20.evaluate import decide
from research_engine.cn_a_share_index_v20.factory import month_grid
from research_engine.cn_a_share_index_v20.signals import add_drop_scores, member_score


class TestV20(unittest.TestCase):
    def test_locks(self):
        self.assertFalse(NEW_PURCHASE)
        self.assertFalse(REOPEN_H11_H12)
        self.assertFalse(REOPEN_V16)
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        self.assertEqual(len(HYPOTHESES), MAX_HYPOTHESES)
        self.assertEqual(ADD_LOOKBACK, 252)
        self.assertEqual(build_contract()["portfolio"], "MEMBERSHIP_SET")
        self.assertIsNone(build_contract()["quantile"])

    def test_contract_hash_stable(self):
        self.assertEqual(build_contract()["contract_hash"], build_contract()["contract_hash"])
        self.assertTrue(build_contract()["predictive_is_not_cagr"])

    def test_month_grid(self):
        days = month_grid()
        self.assertGreaterEqual(len(days), 170)
        self.assertEqual(days[0], "2009-12-15")
        self.assertEqual(days[-1], "2024-02-15")

    def test_pick_set_not_quantile(self):
        scores = np.zeros(20)
        scores[0:5] = 1.0
        mask = np.ones(20, dtype=bool)
        js = pick_set(scores, mask, min_n=3)
        self.assertEqual(int(js.size), 5)
        self.assertIsNone(pick_set(scores, mask, min_n=6))

    def test_member_and_reconstitution(self):
        symbols = ["sh.a", "sh.b", "sz.c"]
        dates = ["2010-01-04", "2010-01-05", "2010-01-06"]
        rows = [
            {"symbol": "sh.a", "index": "HS300", "effective_date": "2010-01-04"},
            {"symbol": "sh.b", "index": "HS300", "effective_date": "2010-01-06"},
        ]
        pack = {"symbols": symbols, "dates": dates}
        hs = member_score(pack, rows, "HS300")
        self.assertEqual(hs[0, 0], 1.0)
        self.assertEqual(hs[0, 1], 0.0)
        self.assertEqual(hs[2, 1], 1.0)
        add, drop = add_drop_scores(pack, hs, lookback=2)
        self.assertTrue(np.isnan(add[0, 0]))
        self.assertEqual(add[2, 1], 1.0)
        self.assertEqual(drop[2, 0], 1.0)

    def test_decide(self):
        d = decide([], True)
        self.assertEqual(d["OVERALL"], "A_SHARE_INDEX_MEMBERSHIP_V1_NO_CANDIDATE")
        self.assertEqual(d["STOP"], "STOP_B_FAMILY")


if __name__ == "__main__":
    unittest.main()
