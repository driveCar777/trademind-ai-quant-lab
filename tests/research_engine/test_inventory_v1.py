import unittest

from research_engine.errors import ContractMismatch
from research_engine.inventory import CONTRACT_EVENTS, FEATURE_PARENTS, PARENTS
from research_engine.inventory.contract import assert_search_space
from research_engine.inventory.event_detector import fired_at
from research_engine.inventory.space import build_search_space, canonical_search_space_hash


class TestInventoryV1(unittest.TestCase):
    def test_hash_locked(self):
        self.assertEqual(
            canonical_search_space_hash(),
            "944195090e6fb835aba35be30a7a13ffee437256b9ed3e5610b23fc7116b2c05",
        )
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_price_only"])
        self.assertEqual(space["inv_params"]["z_lookback"], 52)

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_inv_draw_cross": True}, "SPR_RELEASE")
        self.assertEqual(CONTRACT_EVENTS, ("INV_DRAW_CROSS", "INV_BUILD_CROSS"))

    def test_parents(self):
        self.assertTrue(all("20260828" in p for p in PARENTS))
        self.assertTrue(any("EIA" in p for p in FEATURE_PARENTS))
