import unittest

from research_engine.statistics import permutation_delta_p


class TestPermutation(unittest.TestCase):
    def test_shifted_series_small_p(self):
        cond = [1.0] * 40
        base = [0.0] * 40
        out = permutation_delta_p(cond, base, iterations=300, seed=20260825)
        self.assertEqual(out, permutation_delta_p(cond, base, iterations=300, seed=20260825))
        self.assertLess(out["p_value"], 0.05)

    def test_identical_not_extreme(self):
        xs = [0.1, -0.1, 0.2, -0.2] * 10
        out = permutation_delta_p(xs, list(xs), iterations=200, seed=20260825)
        self.assertGreater(out["p_value"], 0.2)


if __name__ == "__main__":
    unittest.main()
