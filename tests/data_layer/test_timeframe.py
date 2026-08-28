import unittest

from data_layer.timeframes import mt5_timeframe, normalize_timeframe, timeframe_minutes


class _FakeMT5(object):
    TIMEFRAME_M15 = object()
    TIMEFRAME_H1 = object()
    TIMEFRAME_H4 = object()
    TIMEFRAME_D1 = object()


class TestTimeframe(unittest.TestCase):
    def test_minutes(self):
        self.assertEqual(timeframe_minutes("M15"), 15)
        self.assertEqual(timeframe_minutes("H1"), 60)
        self.assertEqual(timeframe_minutes("H4"), 240)
        self.assertEqual(timeframe_minutes("D1"), 1440)

    def test_uses_mt5_constants_not_raw_ints(self):
        mt5 = _FakeMT5()
        self.assertIs(mt5_timeframe(mt5, "M15"), mt5.TIMEFRAME_M15)
        self.assertIs(mt5_timeframe(mt5, "H1"), mt5.TIMEFRAME_H1)
        self.assertIs(mt5_timeframe(mt5, "H4"), mt5.TIMEFRAME_H4)
        self.assertIs(mt5_timeframe(mt5, "D1"), mt5.TIMEFRAME_D1)

    def test_unknown_rejected(self):
        with self.assertRaises(ValueError):
            normalize_timeframe("M5")


if __name__ == "__main__":
    unittest.main()
