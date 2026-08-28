import unittest

from research_profile.research_probe import return_series
from tests.research_profile.helpers import bar


class TestExtremeMove(unittest.TestCase):
    def test_top_abs_return_labeled_not_bad_data(self):
        bars = [
            bar(1, 100, 100, 100, 100),
            bar(2, 100, 120, 100, 120),
            bar(3, 120, 121, 119, 119),
        ]
        out = return_series(bars)
        self.assertEqual(out["top_abs"][0]["label"], "EXTREME_MOVE")
        self.assertGreater(out["top_abs"][0]["return_pct"], 0)


if __name__ == "__main__":
    unittest.main()
