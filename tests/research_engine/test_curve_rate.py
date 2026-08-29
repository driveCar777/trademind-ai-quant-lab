import unittest

from research_engine.curve_rate import LOCKED_HASH
from research_engine.curve_rate.contract import assert_search_space
from research_engine.curve_rate.events import fired_at
from research_engine.curve_rate.features import tag_book
from research_engine.curve_rate.rank import rank_program
from research_engine.curve_rate.space import sealed_contract
from research_engine.v6_external.curve import NotExchangeFuture
from research_engine.v6_external.novelty import novelty_decision


class TestCurveRate(unittest.TestCase):
    def test_hash_locks(self):
        space = sealed_contract()
        self.assertEqual(space["search_space_hash"], LOCKED_HASH)
        assert_search_space(space)
        self.assertEqual(space["family_id"], "CURVE_REALYIELD_V1")

    def test_novelty_real_yield_proxy(self):
        ok = novelty_decision(
            "UST10 yield change as a real yield proxy plus GC curve steepening. Not price momentum."
        )
        self.assertEqual(ok["decision"], "ACCEPT")
        killed = novelty_decision("anything", family_id="RATES_V1")
        self.assertEqual(killed["decision"], "REJECT")

    def test_yield_up_steepen_lags(self):
        curve = [
            {"root": "GC", "session_date": "2018-01-02", "front_open": "1300", "front_settle": "1300", "steepening": "0.0"},
            {"root": "GC", "session_date": "2018-01-03", "front_open": "1301", "front_settle": "1301", "steepening": "0.002"},
            {"root": "GC", "session_date": "2018-01-04", "front_open": "1302", "front_settle": "1302", "steepening": "0.001"},
        ]
        ust = [
            {"timestamp_utc": "2018-01-02T00:00:00Z", "close": "2.40"},
            {"timestamp_utc": "2018-01-03T00:00:00Z", "close": "2.50"},
        ]
        book, _ = tag_book(curve, ust)
        by = dict((b["date"], b) for b in book)
        self.assertFalse(fired_at(by["2018-01-03"], "YIELD_UP_STEEPEN", "GC"))
        self.assertTrue(fired_at(by["2018-01-04"], "YIELD_UP_STEEPEN", "GC"))

    def test_broker_cfd_rejected(self):
        with self.assertRaises(NotExchangeFuture):
            tag_book([{"root": "GOLD", "session_date": "2018-01-02"}], [])

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

        cand = rank_program(
            [fake("HYP-CURATE-0001", True), fake("HYP-CURATE-0002", True), fake("HYP-CURATE-0003", False)]
        )
        self.assertEqual(cand["outcome"], "CANDIDATE")


if __name__ == "__main__":
    unittest.main()
