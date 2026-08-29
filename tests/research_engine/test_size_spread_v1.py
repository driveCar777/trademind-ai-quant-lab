import unittest

from research_engine.errors import ContractMismatch
from research_engine.size_spread import BASKET, CONTRACT_EVENTS, LOCKED_HASH, PARENTS
from research_engine.size_spread.contract import assert_search_space
from research_engine.size_spread.event_detector import fired_at
from research_engine.size_spread.space import build_search_space, canonical_search_space_hash


class TestSizeSpreadV1(unittest.TestCase):
    def test_hash_locked(self):
        digest = canonical_search_space_hash()
        self.assertEqual(LOCKED_HASH, digest)
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_ag_breadth"])
        self.assertTrue(space["not_idx_async_single"])
        self.assertEqual(space["size_params"]["lookback"], 20)
        self.assertEqual(list(BASKET), ["US2000", "US500", "GOLD"])

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_size_lag": True}, "BUY_US500")
        self.assertEqual(CONTRACT_EVENTS, ("SIZE_LAG", "SIZE_LEAD"))

    def test_parents(self):
        self.assertTrue(any("US2000" in p for p in PARENTS))
        self.assertTrue(any("US500" in p for p in PARENTS))
        self.assertTrue(any("GOLD" in p for p in PARENTS))
        self.assertTrue(any("20260829" in p for p in PARENTS))
        self.assertTrue(all("20260825" not in p for p in PARENTS))
        self.assertFalse(any("WHEAT" in p for p in PARENTS))
