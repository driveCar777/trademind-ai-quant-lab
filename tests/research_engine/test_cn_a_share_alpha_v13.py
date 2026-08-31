# -*- coding: utf-8 -*-
import unittest

from research_engine.cn_a_share_alpha import (
    DATASET_ID,
    FINAL_OOS_ACCESS,
    HOLD_DAYS,
    LIVE_API,
    LOOKBACKS,
    MAX_HYPOTHESES,
    NEW_PURCHASE,
    RESEARCH_END,
    RESEARCH_START,
    VALID_END,
    VALID_START,
)
from research_engine.cn_a_share_alpha.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_alpha.cost import stamp_duty_sell
from research_engine.cn_a_share.universe import listed_on


class TestV13(unittest.TestCase):
    def test_no_purchase_no_live(self):
        self.assertFalse(NEW_PURCHASE)
        self.assertFalse(LIVE_API)
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        self.assertEqual(DATASET_ID, "tm-ashare-EQUITY-D1-20260830-000002")

    def test_twelve_locked(self):
        self.assertEqual(len(HYPOTHESES), 12)
        self.assertLessEqual(len(HYPOTHESES), MAX_HYPOTHESES)
        self.assertEqual(LOOKBACKS, (20, 60, 120))
        self.assertEqual(HOLD_DAYS, 20)

    def test_contract_hash_stable(self):
        a = build_contract()
        b = build_contract()
        self.assertEqual(a["contract_hash"], b["contract_hash"])
        self.assertFalse(a["live_api"])
        self.assertFalse(a["factor_combination"])
        self.assertFalse(a["ml"])

    def test_stamp_pit(self):
        self.assertEqual(stamp_duty_sell("2023-08-27"), 0.0010)
        self.assertEqual(stamp_duty_sell("2023-08-28"), 0.0005)

    def test_splits_locked(self):
        self.assertEqual(RESEARCH_START, "2010-01-04")
        self.assertEqual(RESEARCH_END, "2021-08-24")
        self.assertEqual(VALID_START, "2021-08-25")
        self.assertEqual(VALID_END, "2024-02-29")

    def test_future_listing_not_in_2015(self):
        old = {"symbol": "sh.600000", "instrument_type": "EQUITY", "listing_date": "1999-11-10", "delisting_date": ""}
        nxt = {"symbol": "sh.999998", "instrument_type": "EQUITY", "listing_date": "2026-06-01", "delisting_date": ""}
        self.assertTrue(listed_on(old, "2015-06-01"))
        self.assertFalse(listed_on(nxt, "2015-06-01"))


if __name__ == "__main__":
    unittest.main()
