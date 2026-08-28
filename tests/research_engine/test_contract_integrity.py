import unittest

from research_engine.alpha_program.contracts.locks import assert_frozen_hashes
from research_engine.cross_asset import LOCKED_HASH as XA_HASH
from research_engine.cross_residual import LOCKED_HASH as XR_HASH
from research_engine.cross_residual.space import canonical_search_space_hash as xr_hash
from research_engine.errors import ContractMismatch
from research_engine.regime_transition import LOCKED_HASH as RT_HASH
from research_engine.regime_transition.contract import assert_job_contract, assert_search_space
from research_engine.regime_transition.jobs import make_job
from research_engine.regime_transition.space import build_search_space


class TestContractIntegrity(unittest.TestCase):
    def test_frozen_hashes_agree(self):
        locks = assert_frozen_hashes()
        self.assertEqual(locks["v09_constant"], RT_HASH)
        self.assertEqual(locks["v08_constant"], XA_HASH)
        self.assertEqual(locks["v091_constant"], XR_HASH)

    def test_residual_hash_matches_paper(self):
        self.assertEqual(xr_hash(), "0ce685fe6442a1812700df2cde6daa4c9f4255d04a707710c367f5cb6afbdc57")

    def test_v09_space_rejects_hold_change(self):
        space = build_search_space()
        space["hold_bars"] = 3
        with self.assertRaises(ContractMismatch):
            assert_search_space(space)

    def test_v09_job_rejects_empty(self):
        space = build_search_space()
        job = make_job("Xavier-01", {"hypothesis_ids": ["HYP-RT-0001"], "role": "PRIMARY"}, space)
        job["hypothesis_ids"] = []
        job["hypothesis_count"] = 0
        with self.assertRaises(ContractMismatch):
            assert_job_contract(job, space)

    def test_close_fill_forbidden(self):
        space = build_search_space()
        self.assertEqual(space["close_fill"], "FORBIDDEN")
        space["close_fill"] = "ALLOWED"
        with self.assertRaises(ContractMismatch):
            assert_search_space(space)
