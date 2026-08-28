import unittest

from research_engine.errors import ContractMismatch
from research_engine.usd_metal import CONTRACT_EVENTS, LOCKED_HASH, PARENTS
from research_engine.usd_metal.contract import assert_search_space
from research_engine.usd_metal.event_detector import fired_at
from research_engine.usd_metal.space import build_search_space, canonical_search_space_hash


class TestUsdMetalV1(unittest.TestCase):
    def test_hash_locked(self):
        self.assertEqual(
            canonical_search_space_hash(),
            "a39952f9dd4f3bcec04ce302ac9248b1dc5c2832cce762ee0ce16c0eec474f0b",
        )
        self.assertEqual(LOCKED_HASH, canonical_search_space_hash())
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_v08_fx_return"])
        self.assertTrue(space["not_cross_metal_ratio"])
        self.assertEqual(space["hypothesis_ids"][0], "HYP-UM-0001")

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_dxy_up_cross": True}, "RATIO_RICH_CROSS")
        self.assertEqual(CONTRACT_EVENTS, ("DXY_UP_CROSS", "DXY_DOWN_CROSS"))

    def test_parents_include_dxy_not_fx_pairs(self):
        self.assertTrue(any("DXY" in p for p in PARENTS))
        self.assertTrue(any("GOLD" in p for p in PARENTS))
        self.assertTrue(any("SILVER" in p for p in PARENTS))
        self.assertFalse(any("EURUSD" in p for p in PARENTS))
        self.assertFalse(any("20260825" in p for p in PARENTS))
