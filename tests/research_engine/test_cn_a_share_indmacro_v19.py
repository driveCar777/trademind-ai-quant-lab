# -*- coding: utf-8 -*-
import unittest

from research_engine.cn_a_share_indmacro_v19 import FINAL_OOS_ACCESS, MAX_HYPOTHESES, NEW_PURCHASE, REOPEN_V16, REOPEN_V17
from research_engine.cn_a_share_indmacro_v19.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_indmacro_v19.evaluate import decide


class TestV19(unittest.TestCase):
    def test_locks(self):
        self.assertFalse(NEW_PURCHASE)
        self.assertFalse(REOPEN_V16)
        self.assertFalse(REOPEN_V17)
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        self.assertEqual(len(HYPOTHESES), MAX_HYPOTHESES)

    def test_contract_hash_stable(self):
        self.assertEqual(build_contract()["contract_hash"], build_contract()["contract_hash"])
        self.assertTrue(build_contract()["predictive_is_not_cagr"])

    def test_decide(self):
        d = decide([], True)
        self.assertEqual(d["OVERALL"], "A_SHARE_INDUSTRY_MACRO_V1_NO_CANDIDATE")
        self.assertEqual(d["STOP"], "STOP_B_FAMILY")


if __name__ == "__main__":
    unittest.main()
