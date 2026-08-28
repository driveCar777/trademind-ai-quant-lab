import unittest

from research_engine.discovery.evaluate import evaluate_candidate
from research_engine.discovery.nulls import null_controls_for_dataset, null_discovery_rate
from research_engine.discovery.rank import apply_fdr
from research_engine.fixtures import fixture_a_independent
from research_protocol.windows import candidate_window


class TestFactorNull(unittest.TestCase):
    def test_noise_does_not_mint_many_discoveries(self):
        bars = fixture_a_independent(220, 13)
        window = candidate_window({"dataset_id": "x"}, bars, lookback=10, holding=5, purge=5, embargo=1)
        rows = []
        i = 0
        while i < 24:
            cand = {
                "candidate_id": "FD-V01-NULL-%s" % i,
                "family_id": "FAM-FD-NULL",
                "name": "RAND_%s" % i,
                "kind": "random_null",
                "params": {"seed": 20260825 + i},
                "side": "high",
                "target": "future_return",
                "horizon": 1,
            }
            row = evaluate_candidate(bars, window, cand, {}, seed=20260825, iters_boot=30, iters_perm=30)
            rows.append(row)
            i += 1
        ranked, fdr = apply_fdr(rows, q=0.05)
        self.assertLessEqual(len(fdr["discoveries"]), 6)

    def test_explicit_nulls_run(self):
        bars = fixture_a_independent(160, 5)
        window = candidate_window({"dataset_id": "x"}, bars, lookback=10, holding=5, purge=5, embargo=1)
        template = {"kind": "ret", "params": {"n": 5}, "side": "high", "target": "future_return", "horizon": 1}
        out = null_controls_for_dataset(bars, window, template, seed=20260825, iters_boot=20, iters_perm=20)
        self.assertIn("permutation_p", out["null_permute_target"])
        self.assertIn("permutation_p", out["null_random_factor"])
        rate = null_discovery_rate([0.4, 0.6, 0.7, 0.8], q=0.05)
        self.assertEqual(rate["discoveries"], 0)


if __name__ == "__main__":
    unittest.main()
