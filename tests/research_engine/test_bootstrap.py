import unittest

from research_engine.statistics import bootstrap_mean_ci, mean


class TestBootstrap(unittest.TestCase):
    def test_deterministic_and_covers_mean(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        a = bootstrap_mean_ci(xs, iterations=200, seed=20260825)
        b = bootstrap_mean_ci(xs, iterations=200, seed=20260825)
        self.assertEqual(a, b)
        m = mean(xs)
        self.assertLessEqual(a["low"], m)
        self.assertGreaterEqual(a["high"], m)


if __name__ == "__main__":
    unittest.main()
