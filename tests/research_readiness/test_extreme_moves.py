import unittest

from research_readiness.engine import classify_extreme, simple_returns, top_n
from tests.research_readiness.helpers import bar


class TestExtremeMoves(unittest.TestCase):
    def test_legal_ohlc_is_market_extreme(self):
        bar_ok = bar(2, 100, 200, 90, 180)
        self.assertEqual(classify_extreme(bar_ok, {}), "MARKET_EXTREME")
        bad = dict(bar_ok)
        bad["high"] = 1
        bad["low"] = 10
        self.assertEqual(classify_extreme(bad, {}), "DATA_SUSPECT")

    def test_top_n(self):
        bars = [bar(1, 100, 100, 100, 100), bar(2, 100, 150, 100, 150), bar(3, 150, 151, 149, 149)]
        top = top_n(simple_returns(bars), "return", 1)
        self.assertGreater(top[0]["return"], 0)


if __name__ == "__main__":
    unittest.main()
