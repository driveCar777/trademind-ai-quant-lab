# -*- coding: utf-8 -*-
import unittest

from research_engine.cn_a_share import (
    ALPHA_RESEARCH,
    INVALID_UNIVERSE_ASOF,
    NEW_PURCHASE,
    PANEL_DATASET_ID,
    PANEL_DATASET_ID_V12_2,
)
from research_engine.cn_a_share.decision_v12_1 import decide_v12_1
from research_engine.cn_a_share.guard import STOP_IF_FREE_GB, HALT_IF_FREE_GB
from research_engine.cn_a_share.pit import future_delist_mutation_stable
from research_engine.cn_a_share.session import classify_error


class TestV122(unittest.TestCase):
    def test_no_purchase_no_alpha(self):
        self.assertFalse(NEW_PURCHASE)
        self.assertFalse(ALPHA_RESEARCH)

    def test_new_dataset_id(self):
        self.assertNotEqual(PANEL_DATASET_ID_V12_2, PANEL_DATASET_ID)
        self.assertTrue(PANEL_DATASET_ID_V12_2.startswith("tm-ashare-EQUITY-D1-"))

    def test_20150430_still_invalid(self):
        self.assertEqual(INVALID_UNIVERSE_ASOF, "2015-04-30")

    def test_disk_thresholds(self):
        self.assertEqual(STOP_IF_FREE_GB, 30.0)
        self.assertEqual(HALT_IF_FREE_GB, 20.0)

    def test_price_ready_needs_full_panel(self):
        d = decide_v12_1({"n_equity": 5549, "n_done": 100, "n_failed": 0, "pit_ok": True})
        self.assertEqual(d["PRICE_ALPHA_STATUS"], "PRICE_ALPHA_CONDITIONAL")
        self.assertFalse(d["FINANCIAL_ALPHA_READY"])
        ready = decide_v12_1(
            {
                "n_equity": 5549,
                "n_done": 5549,
                "n_failed": 0,
                "n_empty": 2,
                "pit_ok": True,
                "survivorship_ok": True,
                "adjustment_ok": True,
                "price_integrity_ok": True,
                "determinism_ok": True,
                "resume_ok": True,
            }
        )
        self.assertEqual(ready["PRICE_ALPHA_STATUS"], "PRICE_ALPHA_READY")
        self.assertEqual(ready["NEXT_PRIMARY_ACTION"], "CHINA_A_SHARE_ALPHA_DISCOVERY")
        self.assertFalse(ready["INDUSTRY_ALPHA_READY"])

    def test_delist_mutation_leaves_2015(self):
        names = [
            {"symbol": "sh.600000", "instrument_type": "EQUITY", "listing_date": "1999-11-10", "delisting_date": ""},
            {"symbol": "sh.600005", "instrument_type": "EQUITY", "listing_date": "1998-01-01", "delisting_date": "2017-02-14"},
        ]
        self.assertTrue(future_delist_mutation_stable(names, "2015-06-01"))

    def test_error_classes(self):
        self.assertEqual(classify_error("payment required"), "PERMANENT")
        self.assertEqual(classify_error("login failed"), "SOURCE_ERROR")
        self.assertEqual(classify_error("timeout 10054"), "TRANSIENT")


if __name__ == "__main__":
    unittest.main()
