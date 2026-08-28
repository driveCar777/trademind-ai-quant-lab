import unittest

from research_engine.discovery import DISCOVERY_ID
from research_engine.discovery.evaluate import evaluate_job
from research_engine.discovery.jobs import make_job
from research_engine.factors.space import build_search_space
from research_engine.fixtures import fixture_a_independent
from research_protocol.windows import candidate_window


class TestFactorLineage(unittest.TestCase):
    def test_job_carries_lineage_fields(self):
        space = build_search_space()
        job = make_job("Xavier-01", "tm-market-GOLD-M15-20260825-000001", space)
        for key in ("job_id", "dataset_id", "candidate_ids", "search_space_hash", "seed", "node"):
            self.assertTrue(job.get(key))
        self.assertEqual(job["discovery_id"], DISCOVERY_ID)
        self.assertNotEqual(job["job_id"], "PENDING")

    def test_eval_row_traceable(self):
        bars = fixture_a_independent(140, 6)
        window = candidate_window({"dataset_id": "x"}, bars, lookback=8, holding=4, purge=4, embargo=1)
        cand = {
            "candidate_id": "FD-V01-TEST-RET3",
            "family_id": "FAM-FD-MOMENTUM-0001",
            "name": "RET_3_HIGH",
            "kind": "ret",
            "params": {"n": 3},
            "side": "high",
            "target": "future_return",
            "horizon": 1,
        }
        rows = evaluate_job(bars, window, [cand], seed=20260825, iters_boot=10, iters_perm=10)
        self.assertEqual(rows[0]["candidate_id"], "FD-V01-TEST-RET3")
        self.assertIn("research", rows[0])
        self.assertIn("validation", rows[0])
        self.assertIn("economic_magnitude_bps", rows[0]["research"])


if __name__ == "__main__":
    unittest.main()
