import unittest

from research_protocol.causal import CausalSeries
from research_protocol.features import atr_at, bollinger_at, ema_at, macd_at, rsi_at, sma_at, vwap_at


def bars_from_closes(closes):
    out = []
    prev = closes[0]
    for i, c in enumerate(closes):
        out.append(
            {
                "open": prev,
                "high": max(prev, c) + 1,
                "low": min(prev, c) - 1,
                "close": float(c),
                "tick_volume": 10,
                "real_volume": 0,
                "spread": 1,
                "timestamp_unix": i,
            }
        )
        prev = c
    return out


class TestFeatureGolden(unittest.TestCase):
    def test_sma(self):
        bars = bars_from_closes([1, 2, 3, 4, 5])
        view = CausalSeries(bars).visible_until(4)
        self.assertAlmostEqual(sma_at(view, 3), 4.0)

    def test_ema(self):
        bars = bars_from_closes([10, 20])
        view = CausalSeries(bars).visible_until(1)
        self.assertAlmostEqual(ema_at(view, 2), 10 * (1 - 2.0 / 3) + 20 * (2.0 / 3))

    def test_rsi_all_gains(self):
        closes = list(range(10, 25))
        bars = bars_from_closes(closes)
        view = CausalSeries(bars).visible_until(len(closes) - 1)
        self.assertAlmostEqual(rsi_at(view, 14), 100.0)

    def test_atr_first_window(self):
        bars = bars_from_closes([10, 10, 10, 10])
        view = CausalSeries(bars).visible_until(3)
        self.assertGreaterEqual(atr_at(view, 3), 0)

    def test_vwap(self):
        bars = bars_from_closes([10, 20])
        bars[0]["high"] = bars[0]["low"] = bars[0]["close"] = 10
        bars[1]["high"] = bars[1]["low"] = bars[1]["close"] = 20
        bars[0]["tick_volume"] = 1
        bars[1]["tick_volume"] = 3
        view = CausalSeries(bars).visible_until(1)
        self.assertAlmostEqual(vwap_at(view, 2), (10 * 1 + 20 * 3) / 4.0)

    def test_macd_and_boll_warmup(self):
        bars = bars_from_closes([100] * 5)
        view = CausalSeries(bars).visible_until(4)
        self.assertIsNone(macd_at(view, 12, 26, 9))
        self.assertIsNone(bollinger_at(view, 20, 2))


if __name__ == "__main__":
    unittest.main()
