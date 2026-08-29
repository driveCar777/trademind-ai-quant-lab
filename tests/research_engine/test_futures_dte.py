import unittest

from research_engine.futures_dte import LOCKED_HASH
from research_engine.futures_dte.contract import assert_search_space
from research_engine.futures_dte.events import fired_at
from research_engine.futures_dte.rank import rank_program
from research_engine.futures_dte.space import sealed_contract
from research_engine.v6_external.novelty import novelty_decision


class TestFuturesDte(unittest.TestCase):
    def test_hash_locks_after_seal(self):
        space = sealed_contract()
        self.assertEqual(space["search_space_hash"], LOCKED_HASH)
        assert_search_space(space)
        self.assertEqual(space["family_id"], "DTE_ROLL_WINDOW_V1")

    def test_novelty_accepts_dte_rejects_volume_family(self):
        ok = novelty_decision(
            "Days to expiry near the official contract expiry is a calendar-structure roll window, not price momentum."
        )
        self.assertEqual(ok["decision"], "ACCEPT")
        killed = novelty_decision("anything", family_id="VOLUME_PRICE_FLOW_V1")
        self.assertEqual(killed["decision"], "REJECT")

    def test_events(self):
        bar = {
            "roots": {
                "GC": {"is_near_expiry": True, "is_front_roll": False, "is_post_roll": False},
                "CL": {"is_near_expiry": False, "is_front_roll": True, "is_post_roll": True},
            }
        }
        self.assertTrue(fired_at(bar, "NEAR_EXPIRY", "GC"))
        self.assertTrue(fired_at(bar, "FRONT_ROLL", "CL"))
        self.assertTrue(fired_at(bar, "POST_ROLL", "CL"))

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

        cand = rank_program([fake("HYP-FUTDTE-0001", True), fake("HYP-FUTDTE-0002", True), fake("HYP-FUTDTE-0003", False)])
        self.assertEqual(cand["outcome"], "CANDIDATE")
        self.assertEqual(cand["fdr"]["m"], 3)


if __name__ == "__main__":
    unittest.main()
