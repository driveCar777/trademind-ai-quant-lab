import unittest

from research_engine.discovery.evaluate import evaluate_candidate
from research_engine.fixtures import fixture_a_independent
from research_protocol.hashing import canonical_hash
from research_protocol.windows import candidate_window


class TestFactorDeterminism(unittest.TestCase):
    def test_same_seed_same_result(self):
        bars = fixture_a_independent(160, 9)
        window = candidate_window({"dataset_id": "x"}, bars, lookback=10, holding=5, purge=5, embargo=1)
        cand = {
            "candidate_id": "FD-V01-TEST-RET5",
            "family_id": "FAM-FD-MOMENTUM-0001",
            "name": "RET_5_HIGH",
            "kind": "ret",
            "params": {"n": 5},
            "side": "high",
            "target": "future_return",
            "horizon": 1,
        }
        a = evaluate_candidate(bars, window, cand, {}, seed=20260825, iters_boot=20, iters_perm=20)
        b = evaluate_candidate(bars, window, cand, {}, seed=20260825, iters_boot=20, iters_perm=20)
        self.assertEqual(a["research"]["delta"], b["research"]["delta"])
        self.assertEqual(a["research"]["permutation_p"], b["research"]["permutation_p"])
        self.assertEqual(a["validation"]["delta"], b["validation"]["delta"])
        self.assertEqual(a["raw_p"], b["raw_p"])

    def test_cross_node_content_hash_ignores_job_id(self):
        body = {"dataset_id": "D", "search_space_hash": "h", "seed": 20260825, "candidates": [{"raw_p": 0.2}]}
        a = dict(body)
        a["job_id"] = "FD-V01-Xavier-01-D"
        b = dict(body)
        b["job_id"] = "FD-V01-Xavier-04-D"
        ha = canonical_hash({k: a[k] for k in ("dataset_id", "search_space_hash", "seed", "candidates")})
        hb = canonical_hash({k: b[k] for k in ("dataset_id", "search_space_hash", "seed", "candidates")})
        self.assertEqual(ha, hb)


if __name__ == "__main__":
    unittest.main()
