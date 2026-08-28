import unittest

from research_protocol.causal import CausalSeries
from research_protocol.errors import FutureDataAccess


class TestCausal(unittest.TestCase):
    def test_future_blocked(self):
        bars = [{"close": i} for i in range(10)]
        view = CausalSeries(bars).visible_until(3)
        self.assertEqual(view.close(3), 3)
        with self.assertRaises(FutureDataAccess):
            view.close(4)


if __name__ == "__main__":
    unittest.main()
