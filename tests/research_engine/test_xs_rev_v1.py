import unittest

from research_engine.errors import ContractMismatch, FinalOosAccessDenied
from research_engine.holdout import final_oos_access
from research_engine.xs_rev import BASKET, CONTRACT_EVENTS, LOCKED_HASH, PARENTS
from research_engine.xs_rev.contract import assert_search_space
from research_engine.xs_rev.event_detector import fired_at
from research_engine.xs_rev.rank import rank_program
from research_engine.xs_rev.space import build_search_space, canonical_search_space_hash


class TestXsRevV1(unittest.TestCase):
    def test_hash_locked(self):
        digest = canonical_search_space_hash()
        self.assertEqual(
            digest,
            "fe2a28755193a42c55469b8fe52390ced673581ef10239ebd5d9fcf145c9ede5",
        )
        self.assertEqual(LOCKED_HASH, digest)
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_single_asset_momentum"])
        self.assertTrue(space["not_v08_fx_return"])
        self.assertTrue(space["not_cross_metal_ratio"])
        self.assertTrue(space["not_hold_search"])
        self.assertTrue(space["not_zcut_search"])
        self.assertEqual(space["hypothesis_ids"], ["HYP-XS-0001", "HYP-XS-0002", "HYP-XS-0003"])
        self.assertEqual(space["xs_params"]["lookback"], 20)
        self.assertEqual(space["hold_bars"], 5)
        self.assertEqual(len(BASKET), 10)

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_xs_rebal": True}, "CS_MOMENTUM")
        self.assertEqual(CONTRACT_EVENTS, ("XS_REBAL", "XS_REBAL_WIDE"))

    def test_parents_are_ten_fx_not_metals(self):
        self.assertEqual(len(PARENTS), 10)
        self.assertTrue(all("20260825" not in p for p in PARENTS))
        self.assertTrue(all("20260828" in p for p in PARENTS))
        self.assertFalse(any("GOLD" in p for p in PARENTS))
        self.assertFalse(any("SILVER" in p for p in PARENTS))
        self.assertFalse(any("DXY" in p for p in PARENTS))
        self.assertTrue(any("EURUSD" in p for p in PARENTS))
        self.assertTrue(any("GBPJPY" in p for p in PARENTS))

    def test_final_oos_denied(self):
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access(reason="xs_rev_v1_test")

    def test_candidate_needs_two_hyps(self):
        def _row(hid, ok=True):
            tr = 0.02 if ok else -0.01
            return {
                "hypothesis_id": hid,
                "predicted_sign": 1,
                "research": {
                    "raw_p": 0.01 if ok else 0.80,
                    "total_return": tr,
                    "n_trade": 12,
                    "max_drawdown": -0.05,
                    "max_trade_share": 0.10,
                    "mean_signal": 0.001 if ok else -0.001,
                    "level_leak": False,
                },
                "validation": {
                    "total_return": tr,
                    "n_trade": 6,
                    "max_drawdown": -0.05,
                    "mean_signal": 0.001 if ok else -0.001,
                    "level_leak": False,
                },
            }

        one = rank_program([_row("HYP-XS-0001", True), _row("HYP-XS-0002", False), _row("HYP-XS-0003", False)])
        self.assertEqual(one["outcome"], "WEAK_EDGE")
        two = rank_program([_row("HYP-XS-0001", True), _row("HYP-XS-0002", True), _row("HYP-XS-0003", False)])
        self.assertEqual(two["outcome"], "CANDIDATE")
        none = rank_program([_row("HYP-XS-0001", False), _row("HYP-XS-0002", False), _row("HYP-XS-0003", False)])
        self.assertEqual(none["outcome"], "NO_CANDIDATE")
