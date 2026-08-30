# -*- coding: utf-8 -*-
import os
import unittest

from research_engine.cn_a_share import ALPHA_RESEARCH, BACKTEST, NEW_PURCHASE, NEW_SUBSCRIPTION
from research_engine.cn_a_share.bars import price_integrity, to_raw_row
from research_engine.cn_a_share.calendar import is_trading_day, local_and_utc, weekday_name, write_calendar_csv
from research_engine.cn_a_share.corporate import verify_ex_date
from research_engine.cn_a_share.decision import decide
from research_engine.cn_a_share.pit import (
    future_financial_mutation_stable,
    future_price_mutation_stable,
    knowledge_ok,
    universe_excludes_future_ipo,
    universe_keeps_pre_delist,
    visible_financials,
)
from research_engine.cn_a_share.schema import DAILY_RAW_COLS, SESSION, dataset_id
from research_engine.cn_a_share.universe import is_equity, listed_on, normalize_basic
from research_protocol.hashing import canonical_hash


BASICS = [
    {"code": "sh.600005", "code_name": "Wugang", "ipoDate": "1999-08-03", "outDate": "2017-02-14", "type": "1", "status": "0"},
    {"code": "sz.000001", "code_name": "PAB", "ipoDate": "1991-04-03", "outDate": "", "type": "1", "status": "1"},
    {"code": "sh.688001", "code_name": "LateIPO", "ipoDate": "2024-06-01", "outDate": "", "type": "1", "status": "1"},
    {"code": "sh.000300", "code_name": "HS300", "ipoDate": "2005-04-08", "outDate": "", "type": "2", "status": "1"},
]

FINS = [
    {"symbol": "sh.600519", "report_period": "2022-12-31", "announcement_date": "2023-03-31", "net_profit": "100", "pubDate": "2023-03-31", "statDate": "2022-12-31"},
    {"symbol": "sh.600519", "report_period": "2023-12-31", "announcement_date": "2024-04-03", "net_profit": "200", "pubDate": "2024-04-03", "statDate": "2023-12-31"},
]


class TestCnAShareFoundation(unittest.TestCase):
    def test_no_alpha_no_purchase(self):
        self.assertFalse(NEW_PURCHASE)
        self.assertFalse(NEW_SUBSCRIPTION)
        self.assertFalse(ALPHA_RESEARCH)
        self.assertFalse(BACKTEST)

    def test_schema_and_ids(self):
        self.assertIn("raw_close", DAILY_RAW_COLS)
        self.assertIn("raw_open", DAILY_RAW_COLS)
        self.assertTrue(dataset_id("BASIC", "20260830", 1).startswith("tm-cn-a-BASIC-"))
        self.assertEqual(SESSION["timezone"], "Asia/Shanghai")
        self.assertEqual(SESSION["morning"]["open"], "09:30")

    def test_equity_filter(self):
        self.assertTrue(is_equity("sh.600519"))
        self.assertTrue(is_equity("sz.000001"))
        self.assertTrue(is_equity("sz.300001"))
        self.assertFalse(is_equity("sh.000300"))
        self.assertFalse(is_equity("sz.159915"))

    def test_listing_delisting(self):
        wugang = normalize_basic(BASICS[0])
        live = normalize_basic(BASICS[1])
        late = normalize_basic(BASICS[2])
        self.assertTrue(listed_on(wugang, "2016-12-30"))
        self.assertFalse(listed_on(wugang, "2017-03-01"))
        self.assertTrue(listed_on(live, "2026-08-28"))
        self.assertFalse(listed_on(late, "2024-01-01"))
        self.assertTrue(listed_on(late, "2024-06-01"))
        self.assertFalse(live["delisting_date_known"])
        self.assertIsNone(live["delisting_date"])

    def test_calendar_not_utc_plus_one(self):
        rows = [
            {"calendar_date": "2024-01-01", "is_trading_day": 0, "weekday": "Monday", "session_tz": "Asia/Shanghai"},
            {"calendar_date": "2024-01-02", "is_trading_day": 1, "weekday": "Tuesday", "session_tz": "Asia/Shanghai"},
        ]
        self.assertFalse(is_trading_day(rows, "2024-01-01"))
        self.assertTrue(is_trading_day(rows, "2024-01-02"))
        self.assertEqual(weekday_name(__import__("datetime").date(2024, 1, 1)), "Monday")
        ts = local_and_utc("2024-01-02")
        self.assertIn("+08:00", ts["timestamp_local"])
        self.assertTrue(ts["timestamp_utc"].endswith("Z"))

    def test_calendar_hash_stable(self):
        import tempfile

        rows = [
            {"calendar_date": "2024-01-01", "is_trading_day": 0, "weekday": "Monday", "session_tz": "Asia/Shanghai"},
            {"calendar_date": "2024-01-02", "is_trading_day": 1, "weekday": "Tuesday", "session_tz": "Asia/Shanghai"},
        ]
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        try:
            a = write_calendar_csv(path, rows)
            b = write_calendar_csv(path, rows)
            self.assertEqual(a, b)
        finally:
            os.remove(path)

    def test_knowledge_time(self):
        self.assertFalse(knowledge_ok("2024-01-01", "2024-04-03"))
        self.assertTrue(knowledge_ok("2024-01-01", "2023-03-31"))
        vis = visible_financials(FINS, "2024-01-01")
        self.assertEqual(len(vis), 1)
        self.assertEqual(vis[0]["report_period"], "2022-12-31")

    def test_future_mutations(self):
        self.assertTrue(future_financial_mutation_stable(FINS, "2024-01-01", "2024-04-01"))
        bars = [
            {"trade_date": "2024-12-31", "raw_close": 10.0},
            {"trade_date": "2025-06-03", "raw_close": 11.0},
        ]
        self.assertTrue(future_price_mutation_stable(bars, "2024-12-31"))
        self.assertTrue(universe_excludes_future_ipo(BASICS, "2024-01-01"))
        self.assertTrue(universe_keeps_pre_delist(BASICS, "2016-12-30", "sh.600005"))
        self.assertFalse(universe_keeps_pre_delist(BASICS, "2017-03-01", "sh.600005"))

    def test_price_integrity_and_suspension(self):
        raw = to_raw_row(
            {
                "date": "2024-01-02",
                "code": "sh.600000",
                "open": "10",
                "high": "11",
                "low": "9",
                "close": "10.5",
                "volume": "1000",
                "amount": "10000",
                "turn": "1.2",
                "preclose": "10",
                "tradestatus": "1",
                "isST": "0",
                "adjustflag": "3",
            }
        )
        self.assertEqual(raw["raw_close"], 10.5)
        self.assertFalse(raw["suspended"])
        issues = price_integrity([raw, dict(raw, trade_date="2024-01-02")])
        kinds = [i["kind"] for i in issues]
        self.assertIn("duplicate", kinds)
        susp = to_raw_row(
            {
                "date": "2024-01-03",
                "code": "sh.600000",
                "open": "",
                "high": "",
                "low": "",
                "close": "",
                "volume": "",
                "amount": "",
                "turn": "",
                "preclose": "10",
                "tradestatus": "0",
                "isST": "0",
                "adjustflag": "3",
            }
        )
        self.assertTrue(susp["suspended"])
        self.assertEqual(price_integrity([susp]), [])

    def test_adjustment_verify(self):
        raw = [{"date": "2023-06-29", "close": "100"}, {"date": "2023-06-30", "close": "100"}]
        qfq = [{"date": "2023-06-29", "close": "98"}, {"date": "2023-06-30", "close": "97"}]
        v = verify_ex_date(raw, qfq, "2023-06-30")
        self.assertTrue(v["ok"])
        same = verify_ex_date(raw, raw, "2023-06-30")
        self.assertFalse(same["ok"])

    def test_determinism(self):
        a = canonical_hash({"x": 1, "y": [2, 3]})
        b = canonical_hash({"y": [2, 3], "x": 1})
        self.assertEqual(a, b)

    def test_survivorship_blocks_when_census_empty(self):
        art = _art_base()
        art["delist_census"] = {"done": True, "n": 337, "n_empty": 200, "n_with_bars": 137}
        v = decide(art)
        self.assertEqual(v["A_SHARE_DATA_STATUS"], "BLOCKED")
        self.assertEqual(v["A_SHARE_RESEARCH_LABEL"], "A_SHARE_UNIVERSE_NOT_READY")
        self.assertEqual(v["NEXT_PRIMARY_ACTION"], "COMPLETE_DELISTED_BAR_CENSUS")

    def test_conditional_when_sample_only(self):
        art = _art_base()
        art["delist_census"] = {"done": True, "n": 337, "n_empty": 0, "n_with_bars": 337}
        art["universe_history"] = {"n_asof": 20}
        v = decide(art)
        self.assertEqual(v["A_SHARE_DATA_STATUS"], "CONDITIONAL")
        self.assertEqual(v["NEXT_PRIMARY_ACTION"], "FREEZE_FULL_EQUITY_DAILY_PANEL")
        self.assertFalse(v["ALPHA_RESEARCH"])

    def test_census_pending_blocks(self):
        art = _art_base()
        art["delist_census"] = {"done": False, "n": 337, "n_empty": None, "n_with_bars": None}
        v = decide(art)
        self.assertEqual(v["A_SHARE_DATA_STATUS"], "BLOCKED")


def _art_base():
    return {
        "pit": {"asof_membership_ok": True},
        "universe_history": {"n_asof": 20},
        "corporate_action": {"dividend_ok": True, "adjust_factor_ok": True},
        "adjustment": {"raw_ne_qfq": True},
        "calendar": {"has_holiday": True, "has_trading_day": True, "tz": "Asia/Shanghai"},
        "timezone_ok": True,
        "price_integrity": {"sample_ok": True, "sample_only": True},
        "basics": {"has_ipo_date": True, "has_out_date_field": True},
        "industry_pit": False,
        "financial_research_ready": False,
        "akshare_http_ok": False,
    }


if __name__ == "__main__":
    unittest.main()
