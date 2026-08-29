import unittest

from research_engine.breadth import BASKET, CONTRACT_EVENTS, FEATURE_BASKET, LOCKED_HASH, PARENTS
from research_engine.breadth.contract import assert_search_space
from research_engine.breadth.event_detector import fired_at
from research_engine.breadth.space import build_search_space, canonical_search_space_hash
from research_engine.errors import ContractMismatch


class TestBreadthV1(unittest.TestCase):
    def test_hash_locked(self):
        digest = canonical_search_space_hash()
        self.assertEqual(LOCKED_HASH, digest)
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_xs_rev_rank"])
        self.assertTrue(space["not_buy_us500"])
        self.assertTrue(space["not_energy_crack"])
        self.assertEqual(space["breadth_params"]["lookback"], 20)
        self.assertEqual(list(FEATURE_BASKET), ["COTTON", "COCOA", "COFFEE", "CORN", "SOYBEAN", "SUGAR", "WHEAT"])
        self.assertIn("GOLD", BASKET)

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_breadth_thrust": True}, "BUY_US500")
        self.assertEqual(CONTRACT_EVENTS, ("BREADTH_THRUST", "BREADTH_CONTRACT"))

    def test_parents_ag_and_gold(self):
        self.assertTrue(any("WHEAT" in p for p in PARENTS))
        self.assertTrue(any("GOLD" in p for p in PARENTS))
        self.assertTrue(all("20260825" not in p for p in PARENTS))
        self.assertTrue(any("20260829" in p for p in PARENTS))
        self.assertFalse(any("EURUSD" in p for p in PARENTS))
