# -*- coding: utf-8 -*-
import unittest

from research_engine.cn_a_share_div_v21 import FINAL_OOS_ACCESS, MAX_HYPOTHESES, NEW_PURCHASE, REOPEN_H11_H12, REOPEN_V16
from research_engine.cn_a_share_div_v21.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_div_v21.evaluate import decide
from research_engine.cn_a_share_div_v21.factory import announce_date, event_kind, parse_float
from research_engine.cn_a_share_div_v21.pit import visible
from research_engine.cn_a_share_div_v21.signals import event_score


class TestV21(unittest.TestCase):
    def test_locks(self):
        self.assertFalse(NEW_PURCHASE)
        self.assertFalse(REOPEN_H11_H12)
        self.assertFalse(REOPEN_V16)
        self.assertEqual(FINAL_OOS_ACCESS, "DENIED")
        self.assertEqual(len(HYPOTHESES), MAX_HYPOTHESES)
        self.assertIsNone(build_contract()["quantile"])
        self.assertEqual(build_contract()["pit_rule"], "announce_date_lt_signal")

    def test_contract_hash_stable(self):
        self.assertEqual(build_contract()["contract_hash"], build_contract()["contract_hash"])

    def test_parse_and_announce(self):
        self.assertEqual(parse_float("25.911"), 25.911)
        self.assertEqual(parse_float("23.3199或25.911"), 23.3199)
        self.assertEqual(announce_date({"dividPlanAnnounceDate": "2023-03-31", "dividPreNoticeDate": ""}), "2023-03-31")
        self.assertEqual(announce_date({"dividPlanAnnounceDate": "", "dividPreNoticeDate": "2023-03-01"}), "2023-03-01")
        self.assertIsNone(announce_date({"dividPlanAnnounceDate": "", "dividPreNoticeDate": ""}))
        self.assertEqual(event_kind(1.0, 0.0, 0.0), "CASH")
        self.assertEqual(event_kind(0.0, 0.1, 0.0), "STOCK")

    def test_pit_visibility(self):
        rows = [{"symbol": "sh.600519", "announce_date": "2023-03-31", "kind": "CASH"}]
        self.assertEqual(len(visible(rows, "sh.600519", "2023-03-31")), 0)
        self.assertEqual(len(visible(rows, "sh.600519", "2023-04-01")), 1)

    def test_event_window(self):
        pack = {"symbols": ["sh.a", "sh.b"], "dates": ["2010-01-04", "2010-01-05", "2010-01-06", "2010-01-07"]}
        rows = [{"symbol": "sh.a", "announce_date": "2010-01-04", "kind": "CASH"}]
        sc = event_score(pack, rows, ("CASH", "BOTH"), window=2)
        self.assertEqual(sc[0, 0], 0.0)
        self.assertEqual(sc[1, 0], 1.0)
        self.assertEqual(sc[2, 0], 1.0)
        self.assertEqual(sc[3, 0], 0.0)

    def test_decide(self):
        d = decide([], True)
        self.assertEqual(d["OVERALL"], "A_SHARE_DIVIDEND_EVENT_V1_NO_CANDIDATE")
        self.assertEqual(d["STOP"], "STOP_B_FAMILY")


if __name__ == "__main__":
    unittest.main()
