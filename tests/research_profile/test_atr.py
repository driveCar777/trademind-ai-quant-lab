import unittest

from research_profile.research_probe import atr_series, true_ranges
from tests.research_profile.helpers import bar


class TestATR(unittest.TestCase):
    def test_true_range_uses_prev_close(self):
        bars = [
            bar(1, 10, 12, 9, 11),
            bar(2, 11, 13, 8, 9),
        ]
        trs = true_ranges(bars)
        self.assertEqual(trs[0], 3)
        self.assertEqual(trs[1], 5)

    def test_atr14_unknown_if_short(self):
        bars = [bar(i, 10, 11, 9, 10.5) for i in range(5)]
        self.assertEqual(atr_series(true_ranges(bars), 14), [])


if __name__ == "__main__":
    unittest.main()
