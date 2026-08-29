import unittest

from research_engine.energy_rv import BASKET, CONTRACT_EVENTS, LOCKED_HASH, PARENTS
from research_engine.energy_rv.contract import assert_search_space
from research_engine.energy_rv.event_detector import fired_at
from research_engine.energy_rv.space import build_search_space, canonical_search_space_hash
from research_engine.errors import ContractMismatch


class TestEnergyRvV1(unittest.TestCase):
    def test_hash_locked(self):
        digest = canonical_search_space_hash()
        self.assertEqual(
            digest,
            "b208c62352e973377968f274b87ebc6a7ce75b1dc70239a350b938436d50d5ef",
        )
        self.assertEqual(LOCKED_HASH, digest)
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_eia_weekly"])
        self.assertTrue(space["not_oil_sma60"])
        self.assertEqual(space["crack_params"]["ret_lookback"], 20)
        self.assertEqual(list(BASKET), ["OIL", "GASOLINE", "HEATOIL"])

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_crack_cheap_cross": True}, "PROD_DROP_CROSS")
        self.assertEqual(CONTRACT_EVENTS, ("CRACK_CHEAP_CROSS", "CRACK_RICH_CROSS"))

    def test_parents_energy_not_metals(self):
        self.assertTrue(any("OIL" in p for p in PARENTS))
        self.assertTrue(any("GASOLINE" in p for p in PARENTS))
        self.assertFalse(any("GOLD" in p for p in PARENTS))
        self.assertTrue(all("20260825" not in p for p in PARENTS))
