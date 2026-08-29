import unittest

from research_engine.curve_eia import LOCKED_HASH
from research_engine.curve_eia.contract import assert_search_space
from research_engine.curve_eia.events import fired_at
from research_engine.curve_eia.features import tag_book
from research_engine.curve_eia.rank import rank_program
from research_engine.curve_eia.space import sealed_contract
from research_engine.v6_external.curve import NotExchangeFuture
from research_engine.v6_external.novelty import novelty_decision


class TestCurveEia(unittest.TestCase):
    def test_hash_locks(self):
        space = sealed_contract()
        self.assertEqual(space["search_space_hash"], LOCKED_HASH)
        assert_search_space(space)
        self.assertEqual(space["family_id"], "CURVE_EIA_REPRICE_V1")

    def test_novelty_inventory_change_curve(self):
        ok = novelty_decision(
            "EIA inventory change curve repricing: stocks wow plus CL curve steepening. Not inventory z-score."
        )
        self.assertEqual(ok["decision"], "ACCEPT")
        killed = novelty_decision("anything", family_id="INVENTORY_V1")
        self.assertEqual(killed["decision"], "REJECT")

    def test_wow_and_steep_after_wednesday(self):
        curve = [
            {
                "root": "CL",
                "session_date": "2018-01-02",
                "front_open": "50",
                "front_settle": "50",
                "steepening": "0.01",
                "settlement_knowledge_utc": "2018-01-02T21:00:00Z",
            },
            {
                "root": "CL",
                "session_date": "2018-01-04",
                "front_open": "51",
                "front_settle": "51",
                "steepening": "0.02",
                "settlement_knowledge_utc": "2018-01-04T21:00:00Z",
            },
        ]
        eia = [
            {"knowledge_time_utc": "2017-12-27T16:00:00Z", "value": "400"},
            {"knowledge_time_utc": "2018-01-03T16:00:00Z", "value": "410"},
        ]
        book, _ = tag_book(curve, eia)
        last = book[-1]
        self.assertTrue(fired_at(last, "INV_BUILD_STEEPEN", "CL"))
        self.assertEqual(last["roots"]["CL"]["eia_knowledge_utc"], "2018-01-03T16:00:00Z")

    def test_broker_cfd_rejected(self):
        with self.assertRaises(NotExchangeFuture):
            tag_book([{"root": "OIL", "session_date": "2018-01-02"}], [])

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

        cand = rank_program([fake("HYP-CUEIA-0001", True), fake("HYP-CUEIA-0002", True), fake("HYP-CUEIA-0003", False)])
        self.assertEqual(cand["outcome"], "CANDIDATE")


if __name__ == "__main__":
    unittest.main()
