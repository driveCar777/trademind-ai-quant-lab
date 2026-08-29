import unittest

from research_engine.oi_cot import LOCKED_HASH
from research_engine.oi_cot.contract import assert_search_space
from research_engine.oi_cot.events import fired_at
from research_engine.oi_cot.features import tag_book
from research_engine.oi_cot.rank import rank_program
from research_engine.oi_cot.space import sealed_contract
from research_engine.v6_external.curve import NotExchangeFuture
from research_engine.v6_external.novelty import novelty_decision


class TestOiCot(unittest.TestCase):
    def test_hash_locks(self):
        space = sealed_contract()
        self.assertEqual(space["search_space_hash"], LOCKED_HASH)
        assert_search_space(space)
        self.assertEqual(space["family_id"], "OI_COT_BUILD_V1")

    def test_novelty_weekly_positioning_not_extreme(self):
        ok = novelty_decision(
            "Daily official open interest flow plus weekly positioning change is a position build, not a COT extreme."
        )
        self.assertEqual(ok["decision"], "ACCEPT")
        killed = novelty_decision("anything", family_id="POSITIONING_V1")
        self.assertEqual(killed["decision"], "REJECT")
        weekly = novelty_decision("weekly cot extreme into gold")
        self.assertEqual(weekly["decision"], "REJECT")

    def test_build_align_after_friday_knowledge(self):
        curve = [
            {
                "root": "GC",
                "session_date": "2018-01-08",
                "front_open": "1300",
                "front_settle": "1300",
                "front_oi_change": "10",
                "oi_knowledge_utc": "2018-01-09T21:00:00Z",
            },
            {
                "root": "GC",
                "session_date": "2018-01-15",
                "front_open": "1310",
                "front_settle": "1310",
                "front_oi_change": "20",
                "oi_knowledge_utc": "2018-01-16T21:00:00Z",
            },
            {
                "root": "CL",
                "session_date": "2018-01-08",
                "front_open": "50",
                "front_settle": "50",
                "front_oi_change": "5",
                "oi_knowledge_utc": "2018-01-09T21:00:00Z",
            },
            {
                "root": "CL",
                "session_date": "2018-01-15",
                "front_open": "51",
                "front_settle": "51",
                "front_oi_change": "6",
                "oi_knowledge_utc": "2018-01-16T21:00:00Z",
            },
        ]
        cot = {
            "GC": [
                {"knowledge_time_utc": "2018-01-05T21:00:00Z", "mm_net": "100"},
                {"knowledge_time_utc": "2018-01-12T21:00:00Z", "mm_net": "150"},
            ],
            "CL": [
                {"knowledge_time_utc": "2018-01-05T21:00:00Z", "mm_net": "80"},
                {"knowledge_time_utc": "2018-01-12T21:00:00Z", "mm_net": "70"},
            ],
        }
        book, _ = tag_book(curve, cot)
        by = dict((b["date"], b) for b in book)
        self.assertTrue(fired_at(by["2018-01-15"], "BUILD_ALIGN", "GC"))
        self.assertTrue(fired_at(by["2018-01-15"], "SPEED_GAP", "CL"))
        self.assertEqual(by["2018-01-15"]["roots"]["GC"]["week_knowledge_utc"], "2018-01-12T21:00:00Z")

    def test_broker_cfd_rejected(self):
        with self.assertRaises(NotExchangeFuture):
            tag_book([{"root": "GOLD", "session_date": "2018-01-08"}], {"GC": [], "CL": []})

    def test_rank_needs_two_and_fdr(self):
        def fake(hid, ok):
            return {
                "hypothesis_id": hid,
                "predicted_sign": 1,
                "research": {
                    "n_trade": 10 if ok else 2,
                    "total_return": 0.1 if ok else -0.1,
                    "max_drawdown": -0.05,
                    "max_trade_share": 0.1,
                    "mean_signal": 0.01 if ok else -0.01,
                    "raw_p": 0.001 if ok else 0.8,
                    "level_leak": False,
                },
                "validation": {
                    "n_trade": 5 if ok else 1,
                    "total_return": 0.05 if ok else -0.05,
                    "max_drawdown": -0.05,
                    "mean_signal": 0.01 if ok else -0.01,
                    "level_leak": False,
                },
            }

        cand = rank_program([fake("HYP-OICOT-0001", True), fake("HYP-OICOT-0002", True), fake("HYP-OICOT-0003", False)])
        self.assertEqual(cand["outcome"], "CANDIDATE")


if __name__ == "__main__":
    unittest.main()
