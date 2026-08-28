import unittest

from research_engine.alpha_program import V09_LOCKED_HASH
from research_engine.cross_asset.space import canonical_search_space_hash as xa_hash
from research_engine.cross_residual.space import canonical_search_space_hash as xr_hash
from research_engine.opportunity.contract_it import LOCKED_HASH as IT_HASH
from research_engine.opportunity.contract_it import canonical_search_space_hash as it_hash
from research_engine.regime_transition.space import CANONICAL_PAYLOAD, canonical_search_space_hash
from research_protocol.hashing import canonical_hash


class TestHash(unittest.TestCase):
    def test_v09_payload_hash(self):
        self.assertEqual(canonical_hash(CANONICAL_PAYLOAD), V09_LOCKED_HASH)
        self.assertEqual(canonical_search_space_hash(), V09_LOCKED_HASH)

    def test_v09_hash_stable(self):
        self.assertEqual(canonical_search_space_hash(), canonical_search_space_hash())

    def test_v08_untouched(self):
        self.assertEqual(xa_hash(), "787a37f93aae630e2530c6c416c3acf8c5ddd5a9470ae7f442a409f431749827")

    def test_v091_untouched(self):
        self.assertEqual(xr_hash(), "0ce685fe6442a1812700df2cde6daa4c9f4255d04a707710c367f5cb6afbdc57")

    def test_it_v10_hash_locked(self):
        self.assertEqual(it_hash(), IT_HASH)
        self.assertEqual(it_hash(), "1d3c4a1fb628465fed18b4af978d767c2ffbe3f8d6ea23233da01aed3d524457")

    def test_payload_key_order_does_not_matter(self):
        a = canonical_hash({"z": 1, "a": 2})
        b = canonical_hash({"a": 2, "z": 1})
        self.assertEqual(a, b)
