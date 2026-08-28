import unittest

from research_engine.cross_metal import CONTRACT_EVENTS, PARENTS
from research_engine.cross_metal.contract import assert_search_space
from research_engine.cross_metal.event_detector import fired_at
from research_engine.cross_metal.space import build_search_space, canonical_search_space_hash
from research_engine.errors import ContractMismatch


class TestCrossMetalV1(unittest.TestCase):
    def test_hash_locked(self):
        from research_engine.cross_metal import LOCKED_HASH

        digest = canonical_search_space_hash()
        self.assertTrue(digest)
        if LOCKED_HASH:
            self.assertEqual(digest, LOCKED_HASH)
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_oil_residual"])
        self.assertTrue(space["not_sma60"])
        self.assertTrue(space["not_price_only"])
        self.assertEqual(space["hypothesis_ids"][0], "HYP-CM-0001")
        self.assertEqual(space["cm_params"]["z_lookback"], 252)

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_ratio_rich_cross": True}, "PROD_DROP_CROSS")
        self.assertEqual(CONTRACT_EVENTS, ("RATIO_RICH_CROSS", "RATIO_CHEAP_CROSS"))

    def test_parents_are_gold_silver_not_oil(self):
        self.assertTrue(any("GOLD" in p for p in PARENTS))
        self.assertTrue(any("SILVER" in p for p in PARENTS))
        self.assertFalse(any("OIL" in p for p in PARENTS))
        self.assertTrue(all("20260825" not in p for p in PARENTS))
