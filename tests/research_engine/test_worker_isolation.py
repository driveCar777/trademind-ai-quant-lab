import unittest

from research_engine.cross_asset.contract import assert_job_contract as xa_job
from research_engine.cross_asset.jobs import make_job as xa_make
from research_engine.cross_asset.space import build_search_space as xa_space
from research_engine.errors import ContractMismatch
from research_engine.regime_transition.contract import assert_job_contract
from research_engine.regime_transition.jobs import PARTITION, allowed_ids, make_job
from research_engine.regime_transition.space import build_search_space


class TestWorkerIsolation(unittest.TestCase):
    def test_allowed_ids_are_exactly_three(self):
        self.assertEqual(allowed_ids(), ["HYP-RT-0001", "HYP-RT-0002", "HYP-RT-0003"])

    def test_partition_matches_contract(self):
        self.assertEqual(PARTITION["Xavier-01"]["hypothesis_ids"], ["HYP-RT-0001"])
        self.assertEqual(PARTITION["Xavier-02"]["hypothesis_ids"], ["HYP-RT-0002"])
        self.assertEqual(PARTITION["Xavier-03"]["hypothesis_ids"], ["HYP-RT-0003"])
        self.assertEqual(PARTITION["Xavier-04"]["hypothesis_ids"], ["HYP-RT-0001"])
        self.assertEqual(PARTITION["Xavier-04"]["role"], "CROSS_CHECK")

    def test_invented_flag_rejected(self):
        space = build_search_space()
        job = make_job("Xavier-01", PARTITION["Xavier-01"], space)
        job["invented_hypotheses"] = ["HYP-RT-0004"]
        with self.assertRaises(ContractMismatch):
            assert_job_contract(job, space)

    def test_v08_worker_still_isolated(self):
        space = xa_space()
        job = xa_make("Xavier-01", {"hypothesis_ids": ["HYP-XA-0001"], "role": "PRIMARY"}, space)
        job["hypothesis_ids"] = ["HYP-XA-0001", "HYP-RT-0001"]
        job["hypothesis_count"] = 2
        with self.assertRaises(ContractMismatch):
            xa_job(job, space)

    def test_v09_cannot_run_v08_id(self):
        space = build_search_space()
        job = make_job("Xavier-01", PARTITION["Xavier-01"], space)
        job["hypothesis_ids"] = ["HYP-XA-0001"]
        job["hypothesis_count"] = 1
        with self.assertRaises(ContractMismatch):
            assert_job_contract(job, space)
