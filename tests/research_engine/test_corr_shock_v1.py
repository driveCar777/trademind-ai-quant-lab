import unittest

from research_engine.corr_shock import BASKET, CONTRACT_EVENTS, LOCKED_HASH, PARENTS
from research_engine.corr_shock.contract import assert_search_space
from research_engine.corr_shock.event_detector import fired_at
from research_engine.corr_shock.space import build_search_space, canonical_search_space_hash
from research_engine.errors import ContractMismatch, FinalOosAccessDenied
from research_engine.holdout import final_oos_access


class TestCorrShockV1(unittest.TestCase):
    def test_hash_locked(self):
        digest = canonical_search_space_hash()
        self.assertEqual(
            digest,
            "0d729861f138c5e974ec5b99cc308523e97ee4f12c04f17d51678a325ce1647d",
        )
        self.assertEqual(LOCKED_HASH, digest)
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_dxy_z"])
        self.assertTrue(space["not_cross_metal_ratio"])
        self.assertTrue(space["not_pctl_search"])
        self.assertEqual(space["corr_params"]["corr_lookback"], 60)
        self.assertEqual(space["hypothesis_ids"][0], "HYP-CS-0001")
        self.assertEqual(list(BASKET), ["GOLD", "US500"])

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_corr_break_cross": True}, "DXY_UP_CROSS")
        self.assertEqual(CONTRACT_EVENTS, ("CORR_BREAK_CROSS", "CORR_SPIKE_CROSS"))

    def test_parents_gold_us500_not_dxy(self):
        self.assertTrue(any("GOLD" in p for p in PARENTS))
        self.assertTrue(any("US500" in p for p in PARENTS))
        self.assertFalse(any("DXY" in p for p in PARENTS))
        self.assertFalse(any("SILVER" in p for p in PARENTS))
        self.assertTrue(all("20260825" not in p for p in PARENTS))

    def test_final_oos_denied(self):
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access(reason="corr_shock_v1_test")
