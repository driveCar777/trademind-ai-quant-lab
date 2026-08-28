import unittest

from research_readiness.engine import simple_returns
from tests.research_readiness.helpers import bar


class TestReturns(unittest.TestCase):
    def test_simple_return(self):
        bars = [bar(1, 100, 101, 99, 100), bar(2, 100, 111, 99, 110)]
        out = simple_returns(bars)
        self.assertAlmostEqual(out[0]["return"], 0.10)


if __name__ == "__main__":
    unittest.main()
