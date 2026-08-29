import unittest

from research_engine.futures_vol import LOCKED_HASH
from research_engine.futures_vol.contract import assert_search_space
from research_engine.futures_vol.events import fired_at
from research_engine.futures_vol.rank import rank_program
from research_engine.futures_vol.space import sealed_contract
from research_engine.v6_external.novelty import novelty_decision


class TestFuturesVol(unittest.TestCase):
    def test_hash_locks_after_seal(self):
        space = sealed_contract()
        self.assertEqual(space["search_space_hash"], LOCKED_HASH)
        assert_search_space(space)
        self.assertEqual(space["family_id"], "VOLUME_PRICE_FLOW_V1")
        self.assertEqual(len(space["hypothesis_ids"]), 3)

    def test_novelty_accepts_cleared_volume_rejects_oi_family(self):
        ok = novelty_decision(
            "Official cleared volume shock with a higher settlement is new participation. Not price momentum."
        )
        self.assertEqual(ok["decision"], "ACCEPT")
        killed = novelty_decision("anything", family_id="FUTURES_OI_FLOW_V1")
        self.assertEqual(killed["decision"], "REJECT")

    def test_events(self):
        bar = {
            "roots": {
                "GC": {"is_vol_confirm_up": True, "is_vol_fade_thin": False, "is_vol_pressure_down": False},
                "CL": {"is_vol_confirm_up": False, "is_vol_fade_thin": True, "is_vol_pressure_down": True},
            }
        }
        self.assertTrue(fired_at(bar, "VOL_CONFIRM_UP", "GC"))
        self.assertFalse(fired_at(bar, "VOL_CONFIRM_UP", "CL"))
        self.assertTrue(fired_at(bar, "VOL_FADE_THIN", "CL"))
        self.assertTrue(fired_at(bar, "VOL_PRESSURE_DOWN", "CL"))

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

        weak = rank_program([fake("HYP-FUTVOL-0001", True), fake("HYP-FUTVOL-0002", False), fake("HYP-FUTVOL-0003", False)])
        self.assertEqual(weak["outcome"], "WEAK_EDGE")
        cand = rank_program([fake("HYP-FUTVOL-0001", True), fake("HYP-FUTVOL-0002", True), fake("HYP-FUTVOL-0003", False)])
        self.assertEqual(cand["outcome"], "CANDIDATE")
        self.assertEqual(cand["fdr"]["m"], 3)


if __name__ == "__main__":
    unittest.main()
