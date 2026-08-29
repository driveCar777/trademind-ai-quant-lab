import unittest

from research_engine.fut_cfd import GAP, LOCKED_HASH
from research_engine.fut_cfd.contract import assert_search_space
from research_engine.fut_cfd.events import fired_at
from research_engine.fut_cfd.features import tag_book
from research_engine.fut_cfd.rank import rank_program
from research_engine.fut_cfd.space import sealed_contract
from research_engine.v6_external.novelty import novelty_decision


class TestFutCfd(unittest.TestCase):
    def test_hash_locks(self):
        space = sealed_contract()
        self.assertEqual(space["search_space_hash"], LOCKED_HASH)
        assert_search_space(space)

    def test_novelty_and_killed_family(self):
        ok = novelty_decision(
            "Official exchange settlement versus a parallel broker CFD quote is futures leadership / exchange basis, not price momentum."
        )
        self.assertEqual(ok["decision"], "ACCEPT")
        killed = novelty_decision("anything", family_id="FUTURES_OI_FLOW_V1")
        self.assertEqual(killed["decision"], "REJECT")

    def test_gap_events(self):
        curve = [
            {"root": "GC", "session_date": "2019-01-02", "front": "GCG19", "front_settle": "1300"},
            {"root": "GC", "session_date": "2019-01-03", "front": "GCG19", "front_settle": "1320"},
            {"root": "CL", "session_date": "2019-01-02", "front": "CLG19", "front_settle": "50"},
            {"root": "CL", "session_date": "2019-01-03", "front": "CLG19", "front_settle": "50.1"},
        ]
        cfd = {
            "GC": [
                {"date": "2019-01-02", "open": "1300", "close": "1300", "spread": "40"},
                {"date": "2019-01-03", "open": "1301", "close": "1301", "spread": "40"},
            ],
            "CL": [
                {"date": "2019-01-02", "open": "50", "close": "50", "spread": "3"},
                {"date": "2019-01-03", "open": "50", "close": "50.2", "spread": "3"},
            ],
        }
        book, _aligned = tag_book(curve, cfd)
        last = book[-1]
        self.assertTrue(fired_at(last, "FUT_LEAD", "GC"))
        self.assertGreater(last["roots"]["GC"]["gap"], GAP)

    def test_rank_two_and_fdr(self):
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

        cand = rank_program([fake("HYP-FUTCFD-0001", True), fake("HYP-FUTCFD-0002", True), fake("HYP-FUTCFD-0003", False)])
        self.assertEqual(cand["outcome"], "CANDIDATE")


if __name__ == "__main__":
    unittest.main()
