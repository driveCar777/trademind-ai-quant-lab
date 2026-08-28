import unittest

from research_profile.research_probe import gap_profile
from tests.research_profile.helpers import bar


class TestGapDetection(unittest.TestCase):
    def test_m15_gap_and_normal(self):
        bars = [
            bar(0, 1, 2, 0.5, 1.1),
            bar(15 * 60, 1, 2, 0.5, 1.1),
            bar(15 * 60 * 3, 1, 2, 0.5, 1.1),
        ]
        gaps = gap_profile(bars, "M15")
        self.assertEqual(gaps["normal_interval_count"], 1)
        self.assertEqual(gaps["gap_count"], 1)
        self.assertEqual(gaps["overlap_count"], 0)

    def test_d1_weekend_not_overlap(self):
        bars = [
            bar(0, 1, 2, 0.5, 1.1),
            bar(3 * 86400, 1, 2, 0.5, 1.1),
        ]
        gaps = gap_profile(bars, "D1")
        self.assertEqual(gaps["overlap_count"], 0)
        self.assertEqual(gaps["normal_interval_count"], 1)


if __name__ == "__main__":
    unittest.main()
