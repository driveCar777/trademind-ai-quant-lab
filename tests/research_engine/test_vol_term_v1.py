import unittest

from research_engine.errors import ContractMismatch
from research_engine.vol_term import BASKET, CONTRACT_EVENTS, LOCKED_HASH, PARENTS
from research_engine.vol_term.contract import assert_search_space
from research_engine.vol_term.event_detector import fired_at
from research_engine.vol_term.space import build_search_space, canonical_search_space_hash


class TestVolTermV1(unittest.TestCase):
    def test_hash_locked(self):
        digest = canonical_search_space_hash()
        self.assertEqual(
            digest,
            "4e5292b4422d214ecb7ee94a2369bb1b9409416f6b52b151b7d4e40a9289923d",
        )
        self.assertEqual(LOCKED_HASH, digest)
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_atr_level"])
        self.assertEqual(space["vol_params"]["d1_rv_lookback"], 20)
        self.assertEqual(list(BASKET), ["GOLD", "US500"])

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_vol_steep_cross": True}, "ATR_HIGH")
        self.assertEqual(CONTRACT_EVENTS, ("VOL_STEEP_CROSS", "VOL_FLAT_CROSS"))

    def test_parents_include_gold_h1(self):
        self.assertTrue(any("GOLD-H1" in p for p in PARENTS))
        self.assertTrue(any("GOLD-D1" in p for p in PARENTS))
        self.assertTrue(any("US500" in p for p in PARENTS))
        self.assertTrue(all("20260825" not in p for p in PARENTS))
