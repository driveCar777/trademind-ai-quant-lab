import unittest

from research_engine.errors import ContractMismatch
from research_engine.supply import CONTRACT_EVENTS, FEATURE_PARENTS, PARENTS
from research_engine.supply.contract import assert_search_space
from research_engine.supply.event_detector import fired_at
from research_engine.supply.space import build_search_space, canonical_search_space_hash


class TestSupplyV1(unittest.TestCase):
    def test_hash_locked(self):
        self.assertEqual(
            canonical_search_space_hash(),
            "4f6548b39376eb773f772d739a06a8f0d436e52b02d5366b49aeacc61dbb16f1",
        )
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_inventory_stocks"])
        self.assertEqual(space["hypothesis_ids"][0], "HYP-SUP-0001")

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_prod_drop_cross": True}, "INV_DRAW_CROSS")
        self.assertEqual(CONTRACT_EVENTS, ("PROD_DROP_CROSS", "UTIL_UP_CROSS"))

    def test_parents(self):
        self.assertTrue(all("20260828" in p for p in PARENTS))
        self.assertTrue(any("PROD" in p for p in FEATURE_PARENTS))
        self.assertTrue(any("UTIL" in p for p in FEATURE_PARENTS))
        self.assertFalse(any("STXSPR" in p for p in FEATURE_PARENTS))
