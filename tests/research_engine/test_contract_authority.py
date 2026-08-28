import os
import unittest

from research_engine.contract_guard import (
    DRAFT_FAMILY,
    FORMAL_FAMILY,
    LOCKED_PREREG_HASH,
    assert_formal_contract,
    assert_formal_result,
    assert_locked_prereg_hash,
)
from research_engine.contract_load import (
    existing_experiments,
    existing_prereg_pairs,
    load_all_jobs,
    load_bundle,
    load_locked_prereg,
)
from research_engine.errors import ContractMismatch, FinalOosAccessDenied
from research_engine.holdout import final_oos_access, final_oos_state


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENGINE = os.path.join(ROOT, "data", "market", "research_engine")


class TestContractAuthority(unittest.TestCase):
    def test_1_locked_ab_load(self):
        pairs = existing_prereg_pairs(ENGINE)
        ids = sorted(p[1]["hypothesis_id"] for p in pairs)
        self.assertEqual(ids, ["HYP-0001-A", "HYP-0001-B"])

    def test_2_hashes_unchanged(self):
        self.assertEqual(load_locked_prereg("HYP-0001-A", ENGINE)["preregister_hash"], LOCKED_PREREG_HASH["HYP-0001-A"])
        self.assertEqual(load_locked_prereg("HYP-0001-B", ENGINE)["preregister_hash"], LOCKED_PREREG_HASH["HYP-0001-B"])

    def test_3_family_momentum(self):
        hyp_a = existing_prereg_pairs(ENGINE)[0][0]
        if hyp_a["hypothesis_id"] != "HYP-0001-A":
            hyp_a = [h for h, _p in existing_prereg_pairs(ENGINE) if h["hypothesis_id"] == "HYP-0001-A"][0]
        self.assertEqual(hyp_a["family_id"], FORMAL_FAMILY)
        self.assertNotEqual(hyp_a["family_id"], DRAFT_FAMILY)

    def test_4_reuse_32_experiments(self):
        exps = existing_experiments(ENGINE)
        self.assertEqual(len(exps), 32)
        ids = [e["experiment_id"] for e in exps]
        self.assertEqual(ids[0], "tm-exp-20260825-141158-001")
        self.assertEqual(ids[-1], "tm-exp-20260825-141158-032")

    def test_5_job_manifest_lineage(self):
        jobs = load_all_jobs(ENGINE)["Xavier-01"]
        job = jobs[0]
        self.assertEqual(job["experiment_id"], "tm-exp-20260825-141158-001")
        self.assertEqual(job["family_id"], FORMAL_FAMILY)
        self.assertEqual(job["preregister_hash"], LOCKED_PREREG_HASH["HYP-0001-A"])
        hyp, pre, exp = load_bundle(job, engine_root=ENGINE)
        self.assertEqual(exp["experiment_id"], job["experiment_id"])
        self.assertEqual(pre["preregister_hash"], job["preregister_hash"])
        self.assertEqual(hyp["family_id"], FORMAL_FAMILY)

    def test_6_worker_cannot_use_draft_family(self):
        job = load_all_jobs(ENGINE)["Xavier-01"][0]
        hyp, pre, exp = load_bundle(job, engine_root=ENGINE)
        dirty = dict(hyp)
        dirty["family_id"] = DRAFT_FAMILY
        self.assertRaises(ContractMismatch, assert_formal_contract, job, dirty, pre, exp)

    def test_7_pending_experiment_blocked(self):
        job = dict(load_all_jobs(ENGINE)["Xavier-01"][0])
        hyp, pre, exp = load_bundle(job, engine_root=ENGINE)
        job["experiment_id"] = "PENDING"
        self.assertRaises(ContractMismatch, assert_formal_contract, job, hyp, pre, exp)
        self.assertRaises(ContractMismatch, assert_formal_result, {"experiment_id": None, "lineage": {}})

    def test_8_metric_continuation_mean(self):
        pre = load_locked_prereg("HYP-0001-A", ENGINE)
        self.assertIn("continuation_mean = 0", pre["null_hypothesis"])
        job = load_all_jobs(ENGINE)["Xavier-01"][0]
        hyp, pre, exp = load_bundle(job, engine_root=ENGINE)
        self.assertIn("continuation_mean", hyp["target_definition"])

    def test_9_final_oos_denied(self):
        state = final_oos_state()
        self.assertFalse(state["FINAL_OOS_LOCKED"])
        self.assertEqual(state["FINAL_OOS_STATE"], "CANDIDATE_LOCKED_ACCESS_DENIED")
        self.assertRaises(FinalOosAccessDenied, final_oos_access)

    def test_10_wrong_contract_blocked(self):
        self.assertRaises(ContractMismatch, assert_locked_prereg_hash, "HYP-0001-A", "deadbeef")
        self.assertRaises(
            ContractMismatch,
            assert_formal_result,
            {
                "experiment_id": "tm-exp-20260825-141158-001",
                "hypothesis_id": "HYP-0001-A",
                "family_id": DRAFT_FAMILY,
                "research": {"continuation": {"continuation_mean": 0.0}},
            },
        )


if __name__ == "__main__":
    unittest.main()
