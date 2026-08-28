import unittest

from research_engine.alt_market_structure import CONTRACT_EVENTS, PARENTS
from research_engine.alt_market_structure.contract import assert_search_space
from research_engine.alt_market_structure.event_detector import fired_at
from research_engine.alt_market_structure.space import build_search_space, canonical_search_space_hash
from research_engine.errors import ContractMismatch


class TestAltMarketStructure(unittest.TestCase):
    def test_hash_locked(self):
        self.assertEqual(
            canonical_search_space_hash(),
            "8e12e3b16eecb7095a2e7b22847e4be23ba7bd586506daf2cb2e12ea0ec0aad6",
        )
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_weekday"])

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_gap_reopen": True}, "MONDAY_DUMMY")
        self.assertEqual(CONTRACT_EVENTS, ("GAP_REOPEN_H1", "GAP_REOPEN_DOWN_H1"))

    def test_parents_new_h1(self):
        self.assertTrue(all("20260828" in p for p in PARENTS))
        self.assertFalse(any("20260825" in p for p in PARENTS))
