import unittest

from research_engine.discovery.contract import assert_job_contract, assert_search_space
from research_engine.discovery.jobs import make_job
from research_engine.errors import ContractMismatch
from research_engine.factors.space import build_search_space


class TestFactorContract(unittest.TestCase):
    def test_hash_tamper_fails(self):
        space = build_search_space()
        space["search_space_hash"] = "0" * 64
        with self.assertRaises(ContractMismatch):
            assert_search_space(space)

    def test_worker_cannot_add_candidate(self):
        space = build_search_space()
        job = make_job("Xavier-01", "tm-market-GOLD-M15-20260825-000001", space)
        job["candidate_ids"] = list(job["candidate_ids"]) + ["FD-V01-FAKE-INVENTED"]
        with self.assertRaises(ContractMismatch):
            assert_job_contract(job, space)

    def test_empty_candidates_fail(self):
        space = build_search_space()
        job = make_job("Xavier-01", "tm-market-GOLD-M15-20260825-000001", space)
        job["candidate_ids"] = []
        with self.assertRaises(ContractMismatch):
            assert_job_contract(job, space)

    def test_good_job_passes(self):
        space = build_search_space()
        job = make_job("Xavier-01", "tm-market-GOLD-M15-20260825-000001", space)
        self.assertTrue(assert_job_contract(job, space))
        self.assertGreater(job["candidate_count"], 0)


if __name__ == "__main__":
    unittest.main()
