import unittest

from research_engine.cross_asset import ALIGNED_N, CROSS_ID, LOCKED_HASH, PARENTS
from research_engine.cross_asset.align import build_alignment, load_parents, oos_exists
from research_engine.cross_asset.contract import assert_job_contract, assert_search_space, deny_final_oos
from research_engine.cross_asset.evaluate import evaluate_hypothesis, freeze_gate
from research_engine.cross_asset.jobs import make_job
from research_engine.cross_asset.space import build_search_space, canonical_search_space_hash, hypothesis_map
from research_engine.errors import ContractMismatch, FinalOosAccessDenied
from research_engine.holdout import final_oos_access


MARKET = r"D:\AGXXAIVER-4-WINDOWS-1-STOCK\data\market\immutable"


class TestCrossAssetV08(unittest.TestCase):
    def test_contract_hash(self):
        self.assertEqual(canonical_search_space_hash(), LOCKED_HASH)
        space = build_search_space()
        assert_search_space(space)
        self.assertEqual(space["search_space_hash"], LOCKED_HASH)
        self.assertEqual(space["discovery_id"], CROSS_ID)
        self.assertEqual(space["hypothesis_count"], 3)

    def test_alignment_1993(self):
        loaded, hashes = load_parents(MARKET, PARENTS)
        pack = build_alignment(loaded, hashes)
        self.assertEqual(pack["n"], ALIGNED_N)
        self.assertEqual(pack["start"], "2020-04-01")
        self.assertEqual(pack["end"], "2026-08-25")
        exists = oos_exists(pack)
        self.assertTrue(exists["exists"])
        self.assertEqual(exists["n"], 299)
        self.assertEqual(exists["start"], "2025-09-11")

    def test_worker_cannot_add(self):
        space = build_search_space()
        job = make_job("Xavier-01", {"hypothesis_ids": ["HYP-XA-0001"], "role": "PRIMARY"}, space)
        job["hypothesis_ids"] = ["HYP-XA-0001", "HYP-XA-0004"]
        job["hypothesis_count"] = 2
        with self.assertRaises(ContractMismatch):
            assert_job_contract(job, space)

    def test_oos_denied(self):
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access(reason="v08")
        with self.assertRaises(FinalOosAccessDenied):
            deny_final_oos("final_oos")

    def test_gate_freeze_research_only(self):
        loaded, hashes = load_parents(MARKET, PARENTS)
        pack = build_alignment(loaded, hashes)
        spec = hypothesis_map(build_search_space())["HYP-XA-0001"]
        info = freeze_gate(pack["rows"], spec)
        self.assertEqual(info["kind"], "Q3")
        self.assertIsNotNone(info["gate"])

    def test_local_eval_smoke(self):
        loaded, hashes = load_parents(MARKET, PARENTS)
        pack = build_alignment(loaded, hashes)
        spec = hypothesis_map(build_search_space())["HYP-XA-0001"]
        out = evaluate_hypothesis(pack, spec, iters_boot=20, iters_perm=20, block_length=5)
        self.assertEqual(out["hypothesis_id"], "HYP-XA-0001")
        self.assertIn("n_trade", out["research"])
        self.assertIn("delta", out["research"])
        self.assertNotIn("final_oos", out)


if __name__ == "__main__":
    unittest.main()
