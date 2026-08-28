import unittest

from research_readiness.engine import atr14_at, true_ranges
from tests.research_readiness.helpers import bar


class TestATRProfile(unittest.TestCase):
    def test_tr_and_short_atr_unknown(self):
        bars = [bar(i, 10, 12, 9, 11) for i in range(5)]
        trs = true_ranges(bars)
        self.assertEqual(trs[0], 3)
        self.assertIsNone(atr14_at(trs, 4))


if __name__ == "__main__":
    unittest.main()
