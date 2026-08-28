import unittest

from research_engine.errors import ContractMismatch
from research_engine.regime_interaction import CONTRACT_EVENTS, PARENTS
from research_engine.regime_interaction.contract import assert_search_space
from research_engine.regime_interaction.event_detector import fired_at
from research_engine.regime_interaction.space import build_search_space, canonical_search_space_hash


class TestRegimeInteraction(unittest.TestCase):
    def test_hash_locked(self):
        self.assertEqual(
            canonical_search_space_hash(),
            "c060a77e5c08e7c226f63878f6b105e9255b7dedebd5074aa5782dbc9b1fd321",
        )
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_v09"])
        self.assertTrue(space["not_v08"])

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_gold_cheap": True}, "ADX14_CROSS")
        self.assertEqual(
            CONTRACT_EVENTS,
            ("GOLD_RELVOL_CROSSES_CHEAP", "OIL_RELVOL_CROSSES_CHEAP", "JOINT_VOL_SHOCK"),
        )

    def test_parents_new_h1(self):
        self.assertTrue(all("20260828" in p for p in PARENTS))
        self.assertFalse(any("20260825" in p for p in PARENTS))
