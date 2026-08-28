import unittest

from research_engine.errors import ContractMismatch
from research_engine.rates import CONTRACT_EVENTS, FEATURE_PARENTS, PARENTS
from research_engine.rates.contract import assert_search_space
from research_engine.rates.event_detector import fired_at
from research_engine.rates.space import build_search_space, canonical_search_space_hash


class TestRatesV1(unittest.TestCase):
    def test_hash_locked(self):
        self.assertEqual(
            canonical_search_space_hash(),
            "4bbbab85b281b6890b7b38342a82ea649fb56b6ac523b8a28cd6cac854fd54ef",
        )
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_price_only"])
        self.assertEqual(space["hypothesis_ids"][0], "HYP-RATES-0001")

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_rate_up_cross": True}, "REAL_RATE")
        self.assertEqual(CONTRACT_EVENTS, ("RATE_UP_CROSS", "RATE_DOWN_CROSS"))

    def test_parents(self):
        self.assertTrue(all("20260828" in p for p in PARENTS))
        self.assertTrue(any("UST-DGS10" in p for p in FEATURE_PARENTS))
