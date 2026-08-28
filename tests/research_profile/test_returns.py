import math
import os
import unittest

from research_profile.research_probe import return_series
from tests.research_profile.helpers import bar


class TestReturns(unittest.TestCase):
    def test_simple_and_log_return(self):
        bars = [
            bar(1000, 100, 101, 99, 100),
            bar(1900, 100, 111, 99, 110),
        ]
        out = return_series(bars)
        self.assertAlmostEqual(out["simple"][0], 0.10)
        self.assertAlmostEqual(out["log"][0], math.log(1.10))
        self.assertEqual(out["positive_return_count"], 1)
        self.assertEqual(out["negative_return_count"], 0)


if __name__ == "__main__":
    unittest.main()
