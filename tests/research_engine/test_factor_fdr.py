import unittest

from research_engine.discovery.rank import apply_fdr, rank_factors
from research_engine.statistics import benjamini_hochberg


class TestFactorFDR(unittest.TestCase):
    def test_bh_known_vector(self):
        p = [0.001, 0.008, 0.039, 0.2, 0.5]
        out = benjamini_hochberg(p, q=0.05)
        self.assertEqual(out["q"], 0.05)
        self.assertTrue(0 in out["discoveries"])
        self.assertEqual(out["m"], 5)

    def test_apply_fdr_marks_rows(self):
        rows = [{"raw_p": 0.0001, "candidate_id": "A"}, {"raw_p": 0.8, "candidate_id": "B"}]
        marked, fdr = apply_fdr(rows, q=0.05)
        self.assertTrue(marked[0]["fdr_discovery"])
        self.assertFalse(marked[1]["fdr_discovery"])
        self.assertIsNotNone(marked[0]["adjusted_p"])

    def test_no_useful_is_legal(self):
        rows = []
        i = 0
        while i < 8:
            rows.append(
                {
                    "candidate_id": "FD-%s" % i,
                    "family_id": "FAM-X",
                    "name": "X%s" % i,
                    "kind": "ret",
                    "params": {"n": 1},
                    "target": "future_return",
                    "horizon": 1,
                    "raw_p": 0.4,
                    "sign_consistency": False,
                    "cost_sensitive": True,
                    "insufficient_n": False,
                    "research": {"sample_size": 40, "effect_size": 0.01, "delta": 0.0001},
                    "validation": {"sample_size": 20, "effect_size": 0.0, "delta": -0.0001},
                }
            )
            i += 1
        out = rank_factors(rows)
        self.assertEqual(out["outcome"], "NO_USEFUL_FACTORS_FOUND")
        self.assertIn("rank_formula", out)


if __name__ == "__main__":
    unittest.main()
