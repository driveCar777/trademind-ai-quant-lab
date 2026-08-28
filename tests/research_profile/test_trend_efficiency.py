import unittest

from research_profile.research_probe import trend_efficiency


class TestTrendEfficiency(unittest.TestCase):
    def test_straight_line_is_one(self):
        self.assertAlmostEqual(trend_efficiency([1.0, 2.0, 3.0]), 1.0)

    def test_round_trip_is_zero(self):
        self.assertAlmostEqual(trend_efficiency([1.0, 2.0, 1.0]), 0.0)

    def test_zero_path_unknown(self):
        self.assertIsNone(trend_efficiency([5.0, 5.0, 5.0]))


if __name__ == "__main__":
    unittest.main()
