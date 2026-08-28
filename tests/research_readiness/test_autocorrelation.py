import unittest

from research_readiness.engine import autocorrelation


class TestAutocorrelation(unittest.TestCase):
    def test_constant_is_unknown(self):
        self.assertIsNone(autocorrelation([1.0, 1.0, 1.0, 1.0], 1))

    def test_lag1_alternating(self):
        xs = [1.0, -1.0, 1.0, -1.0, 1.0, -1.0]
        val = autocorrelation(xs, 1)
        self.assertLess(val, 0)


if __name__ == "__main__":
    unittest.main()
