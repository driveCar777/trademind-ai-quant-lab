# -*- coding: utf-8 -*-
import unittest

from research_engine.cn_a_share.pit import knowledge_ok, visible_financials
from research_engine.cn_a_share_information_v16 import (
    FINAL_OOS_ACCESS,
    MAX_FIN_HYP,
    MAX_IND_HYP,
    NEW_H13,
    NEW_PURCHASE,
    PRICE_ONLY_REOPEN,
    REOPEN_H11_H12,
)
from research_engine.cn_a_share_information_v16.contract import FIN_HYPOTHESES, IND_HYPOTHESES, build_financial_contract
from research_engine.cn_a_share_information_v16.financial_pit import constructed_ttm, future_announcement_mutation_stable
from research_engine.cn_a_share_information_v16.financial_schema import normalize_profit_row
from research_engine.cn_a_share_information_v16.readiness import industry_ready


class TestV16(unittest.TestCase):
    def test_locks(self):
        self.assertFalse(NEW_PURCHASE)
        self.assertFalse(REOPEN_H11_H12)
        self.assertFalse(NEW_H13)
        self.assertFalse(PRICE_ONLY_REOPEN)
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        self.assertEqual(len(FIN_HYPOTHESES), 6)
        self.assertEqual(len(FIN_HYPOTHESES), MAX_FIN_HYP)
        self.assertEqual(len(IND_HYPOTHESES), 3)
        self.assertEqual(MAX_IND_HYP, 3)

    def test_contract_hash_stable(self):
        a = build_financial_contract()
        b = build_financial_contract()
        self.assertEqual(a["contract_hash"], b["contract_hash"])
        self.assertTrue(a["predictive_is_not_cagr"])
        self.assertEqual(a["predictive_metric_name"], "MEAN_FORWARD_RETURN")

    def test_knowledge_time_not_period_end(self):
        self.assertFalse(knowledge_ok("2024-01-01", "2024-04-03"))
        self.assertTrue(knowledge_ok("2024-01-01", "2023-03-31"))
        rows = [
            {"symbol": "sh.600519", "report_period": "2022-12-31", "announcement_date": "2023-03-31", "net_profit": 1},
            {"symbol": "sh.600519", "report_period": "2023-12-31", "announcement_date": "2024-04-03", "net_profit": 2},
        ]
        vis = visible_financials(rows, "2024-01-01")
        self.assertEqual([r["report_period"] for r in vis], ["2022-12-31"])

    def test_normalize_requires_pubdate(self):
        raw = {"code": "sh.600519", "pubDate": "", "statDate": "2023-12-31", "netProfit": "1"}
        self.assertIsNone(normalize_profit_row(raw, 2023, 4))
        raw["pubDate"] = "2024-04-03"
        row = normalize_profit_row(raw, 2023, 4)
        self.assertEqual(row["announcement_date"], "2024-04-03")
        self.assertEqual(row["eps_kind"], "UNAVAILABLE")
        self.assertTrue(row["restatement_risk"])

    def test_no_future_ttm(self):
        rows = [
            {"symbol": "x", "announcement_date": "2024-04-01", "report_period": "2023-12-31", "net_profit": 10, "quarter": 4, "year": 2023},
            {"symbol": "x", "announcement_date": "2025-04-01", "report_period": "2024-12-31", "net_profit": 99, "quarter": 4, "year": 2024},
        ]
        val = constructed_ttm(rows, "x", "2024-03-31", "2024-03-31")
        self.assertIsNone(val)
        val2 = constructed_ttm(rows, "x", "2025-04-02", "2024-12-31")
        self.assertEqual(val2, 109.0)

    def test_future_announcement_mutation(self):
        rows = [
            {"symbol": "a", "report_period": "2017-12-31", "announcement_date": "2018-03-01", "net_profit": 1},
            {"symbol": "a", "report_period": "2025-12-31", "announcement_date": "2026-04-01", "net_profit": 9},
        ]
        self.assertTrue(future_announcement_mutation_stable(rows, "2018-12-31"))

    def test_industry_not_ready_without_effective_date(self):
        gate = industry_ready({"effective_dating": False, "historical_membership": False, "current_only": True, "pit_available": False})
        self.assertFalse(gate["INDUSTRY_ALPHA_READY"])
        self.assertEqual(gate["INDUSTRY_ALPHA_STATUS"], "INDUSTRY_PIT_BLOCKED")


if __name__ == "__main__":
    unittest.main()
