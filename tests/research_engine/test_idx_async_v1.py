import unittest

from research_engine.errors import ContractMismatch
from research_engine.idx_async import BASKET, CONTRACT_EVENTS, LOCKED_HASH, PARENTS
from research_engine.idx_async.contract import assert_search_space
from research_engine.idx_async.event_detector import fired_at
from research_engine.idx_async.space import build_search_space, canonical_search_space_hash


class TestIdxAsyncV1(unittest.TestCase):
    def test_hash_locked(self):
        digest = canonical_search_space_hash()
        self.assertEqual(
            digest,
            "2e4c5c14fea78e7fc1e2afbdc3ac75f6684ebef42eb152104c182cd590828cb8",
        )
        self.assertEqual(LOCKED_HASH, digest)
        space = build_search_space()
        assert_search_space(space)
        self.assertTrue(space["not_v08_fx_return"])
        self.assertTrue(space["not_xs_rank_book"])
        self.assertEqual(list(BASKET), ["GER40", "US500"])

    def test_invented_rejected(self):
        with self.assertRaises(ContractMismatch):
            fired_at({"is_ger_up_cross": True}, "USDJPY_UP")
        self.assertEqual(CONTRACT_EVENTS, ("GER_UP_CROSS", "GER_DOWN_CROSS"))

    def test_parents_ger40_us500(self):
        self.assertTrue(any("GER40" in p for p in PARENTS))
        self.assertTrue(any("US500" in p for p in PARENTS))
        self.assertFalse(any("EURUSD" in p for p in PARENTS))
        self.assertTrue(all("20260825" not in p for p in PARENTS))
