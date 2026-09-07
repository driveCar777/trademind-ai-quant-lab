# -*- coding: utf-8 -*-
import unittest

import numpy as np

from research_engine.cn_a_share_altinfo_v18 import (
    FINAL_OOS_ACCESS,
    MAX_HYPOTHESES,
    NEW_PURCHASE,
    REOPEN_H11_H12,
    REOPEN_V16,
    REOPEN_V17,
)
from research_engine.cn_a_share_altinfo_v18.compile import REQUIRED
from research_engine.cn_a_share_altinfo_v18.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_altinfo_v18.evaluate import decide
from research_engine.cn_a_share_altinfo_v18.signals import age_days, month_end_mask, quarter_end_mask, streak_true


class TestV18(unittest.TestCase):
    def test_locks(self):
        self.assertFalse(NEW_PURCHASE)
        self.assertFalse(REOPEN_H11_H12)
        self.assertFalse(REOPEN_V16)
        self.assertFalse(REOPEN_V17)
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        self.assertEqual(len(HYPOTHESES), MAX_HYPOTHESES)
        self.assertEqual(MAX_HYPOTHESES, 6)

    def test_contract_hash_stable(self):
        a = build_contract()
        b = build_contract()
        self.assertEqual(a["contract_hash"], b["contract_hash"])
        self.assertTrue(a["predictive_is_not_cagr"])

    def test_age_shape(self):
        from datetime import datetime

        listed = float(datetime(2008, 1, 1).toordinal())
        age = age_days(["2010-01-04", "2010-06-01"], np.array([listed]))
        self.assertEqual(age.shape, (2, 1))
        self.assertGreater(age[1, 0], age[0, 0])

    def test_age_negative_hidden(self):
        from datetime import datetime

        later = float(datetime(2012, 1, 1).toordinal())
        age = age_days(["2010-01-04"], np.array([later]))
        self.assertTrue(np.isnan(age[0, 0]))

    def test_month_end_last_two(self):
        dates = ["2010-01-04", "2010-01-05", "2010-01-29", "2010-02-01", "2010-02-26"]
        m = month_end_mask(dates, 2)
        self.assertTrue(m[1] and m[2])
        self.assertTrue(m[3] and m[4])
        self.assertFalse(m[0])

    def test_quarter_end(self):
        dates = ["2010-03-01", "2010-03-30", "2010-03-31", "2010-04-01", "2010-04-02"]
        q = quarter_end_mask(dates, 2)
        self.assertFalse(q[0])
        self.assertTrue(q[1] and q[2])
        self.assertTrue(q[3] and q[4])

    def test_streak_reset(self):
        flag = np.array([[True, False], [True, True], [False, True]], dtype=bool)
        s = streak_true(flag)
        self.assertEqual(s[0, 0], 1)
        self.assertEqual(s[1, 0], 2)
        self.assertEqual(s[2, 0], 0)
        self.assertEqual(s[2, 1], 2)

    def test_decide_no_candidate(self):
        d = decide([], True)
        self.assertEqual(d["OVERALL"], "A_SHARE_ALTINFO_V1_NO_CANDIDATE")
        self.assertEqual(d["STOP"], "STOP_B_FAMILY")

    def test_required(self):
        self.assertIn("V18_ALTINFO_DECISION.md", REQUIRED)


if __name__ == "__main__":
    unittest.main()
