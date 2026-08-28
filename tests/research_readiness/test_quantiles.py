import unittest

from research_readiness.engine import quantile, return_quantiles


class TestQuantiles(unittest.TestCase):
    def test_sorted_percentiles(self):
        xs = list(range(100))
        self.assertEqual(quantile(xs, 1), 0)
        self.assertEqual(quantile(xs, 50), 49)
        self.assertEqual(quantile(xs, 99), 98)
        q = return_quantiles([1.0, 2.0, 3.0, 4.0])
        self.assertIn("P50", q)
        self.assertEqual(q["P1"], 1.0)


if __name__ == "__main__":
    unittest.main()
