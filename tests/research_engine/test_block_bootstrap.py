import unittest

from research_engine.statistics import mean, moving_block_bootstrap_mean_ci


class TestBlockBootstrap(unittest.TestCase):
    def test_deterministic(self):
        xs = [float(i % 7) for i in range(80)]
        a = moving_block_bootstrap_mean_ci(xs, block_length=20, iterations=200, seed=20260825)
        b = moving_block_bootstrap_mean_ci(xs, block_length=20, iterations=200, seed=20260825)
        self.assertEqual(a, b)
        self.assertEqual(a["block_length"], 20)
        m = mean(xs)
        self.assertTrue(a["low"] <= m <= a["high"] or abs(a["low"] - m) < 1)


if __name__ == "__main__":
    unittest.main()
