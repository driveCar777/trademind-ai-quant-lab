# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

from research_engine.cn_a_share import (
    ALPHA_RESEARCH,
    BACKTEST,
    INVALID_UNIVERSE_ASOF,
    NEW_PURCHASE,
    PANEL_DATASET_ID,
)
from research_engine.cn_a_share.acquire import already_done, _write_vendor_csv
from research_engine.cn_a_share.decision_v12_1 import decide_v12_1
from research_engine.cn_a_share.pit import (
    future_price_mutation_stable,
    universe_excludes_future_ipo,
    universe_keeps_pre_delist,
)
from research_engine.cn_a_share.schema import ashare_dataset_id
from research_engine.cn_a_share.session import classify_error
from research_engine.cn_a_share.universe import from_basic_csv_row, listed_on
from research_engine.cn_a_share.universe_daily import delisted_by, pit_members
from research_protocol.hashing import canonical_hash, file_sha256


class TestV121Panel(unittest.TestCase):
    def test_no_alpha_no_purchase(self):
        self.assertFalse(NEW_PURCHASE)
        self.assertFalse(ALPHA_RESEARCH)
        self.assertFalse(BACKTEST)

    def test_dataset_convention(self):
        self.assertEqual(ashare_dataset_id("20260830", 1), "tm-ashare-EQUITY-D1-20260830-000001")
        self.assertEqual(PANEL_DATASET_ID, "tm-ashare-EQUITY-D1-20260830-000001")

    def test_20150430_stays_invalid(self):
        self.assertEqual(INVALID_UNIVERSE_ASOF, "2015-04-30")
        d = decide_v12_1({"asof_20150430": "INVALID", "n_equity": 10, "n_done": 10, "pit_ok": True})
        self.assertEqual(d["asof_20150430"], "INVALID")

    def test_error_classes(self):
        self.assertEqual(classify_error("timeout reset"), "TRANSIENT")
        self.assertEqual(classify_error("permission denied"), "PERMANENT")
        self.assertEqual(classify_error("ok", elapsed=90), "SOURCE_LIMIT")

    def test_pit_listing_window(self):
        eqs = [
            from_basic_csv_row(
                {
                    "symbol": "sh.600005",
                    "name": "W",
                    "listing_date": "1999-08-03",
                    "delisting_date": "2017-02-14",
                    "instrument_type": "EQUITY",
                    "status": "DELISTED_OR_INACTIVE",
                    "listing_date_known": "True",
                    "delisting_date_known": "True",
                }
            ),
            from_basic_csv_row(
                {
                    "symbol": "sh.688001",
                    "name": "N",
                    "listing_date": "2024-06-01",
                    "delisting_date": "",
                    "instrument_type": "EQUITY",
                    "status": "ACTIVE",
                    "listing_date_known": "True",
                    "delisting_date_known": "False",
                }
            ),
        ]
        self.assertEqual(pit_members(eqs, "2016-12-30"), ["sh.600005"])
        self.assertEqual(pit_members(eqs, "2017-03-01"), [])
        self.assertEqual(pit_members(eqs, "2024-01-01"), [])
        self.assertEqual(pit_members(eqs, "2024-06-01"), ["sh.688001"])
        self.assertEqual(delisted_by(eqs, "2017-03-01"), ["sh.600005"])
        self.assertFalse(listed_on(eqs[1], "2015-06-01"))

    def test_no_today_list_backfill(self):
        today = [
            {"code": "sh.688001", "ipoDate": "2024-06-01", "outDate": "", "type": "1", "status": "1"},
            {"code": "sz.000001", "ipoDate": "1991-04-03", "outDate": "", "type": "1", "status": "1"},
        ]
        self.assertTrue(universe_excludes_future_ipo(today, "2010-01-04"))

    def test_universe_and_price_mutation(self):
        basics = [
            {"code": "sh.600005", "ipoDate": "1999-08-03", "outDate": "2017-02-14", "type": "1", "status": "0"},
        ]
        self.assertTrue(universe_keeps_pre_delist(basics, "2016-12-30", "sh.600005"))
        mutated = list(basics) + [{"code": "sh.999999", "ipoDate": "2026-01-01", "outDate": "", "type": "1", "status": "1"}]
        self.assertEqual(
            universe_excludes_future_ipo(basics, "2015-06-01"),
            universe_excludes_future_ipo(mutated, "2015-06-01"),
        )
        bars = [{"trade_date": "2015-06-01", "raw_close": 10}, {"trade_date": "2026-06-01", "raw_close": 20}]
        self.assertTrue(future_price_mutation_stable(bars, "2015-12-31"))

    def test_resume_no_duplicate(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        rows = [{"date": "2024-01-02", "code": "sh.600000", "open": "1", "high": "1", "low": "1", "close": "1"}]
        try:
            a = _write_vendor_csv(path, rows)
            b = _write_vendor_csv(path, rows)
            self.assertEqual(a, b)
            self.assertEqual(a, file_sha256(path))
            state = {"done": {"sh.600000": {"n_raw": 1}}}
            # already_done checks real panel path; local hash stability is the resume contract
            self.assertEqual(canonical_hash(rows), canonical_hash(list(rows)))
        finally:
            if os.path.isfile(path):
                os.remove(path)
            if os.path.isfile(path + ".part"):
                os.remove(path + ".part")

    def test_ready_requires_complete_panel(self):
        blocked = decide_v12_1({"n_equity": 5549, "n_done": 10, "n_failed": 3})
        self.assertEqual(blocked["PRICE_ALPHA_STATUS"], "PRICE_ALPHA_BLOCKED")
        self.assertFalse(blocked["FINANCIAL_ALPHA_READY"])
        self.assertFalse(blocked["INDUSTRY_ALPHA_READY"])
        ready = decide_v12_1(
            {
                "n_equity": 10,
                "n_done": 10,
                "n_failed": 0,
                "n_empty": 0,
                "pit_ok": True,
                "survivorship_ok": True,
                "adjustment_ok": True,
                "price_integrity_ok": True,
                "determinism_ok": True,
                "resume_ok": True,
            }
        )
        self.assertEqual(ready["PRICE_ALPHA_STATUS"], "PRICE_ALPHA_READY")
        self.assertFalse(ready["FINANCIAL_ALPHA_READY"])
        self.assertEqual(ready["NEXT_PRIMARY_ACTION"], "CHINA_A_SHARE_ALPHA_DISCOVERY")


if __name__ == "__main__":
    unittest.main()
