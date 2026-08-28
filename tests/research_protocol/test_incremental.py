import unittest

from research_protocol.causal import CausalSeries
from research_protocol.features import (
    atr_at,
    bollinger_at,
    compute_feature_series,
    ema_at,
    macd_at,
    rsi_at,
    sma_at,
    vwap_at,
)
from research_protocol.leakage import synthetic_corpus


class TestIncrementalMatchesPointwise(unittest.TestCase):
    def test_series_matches_at(self):
        bars = synthetic_corpus(40)
        series = CausalSeries(bars)
        sma = compute_feature_series(bars, "sma")
        ema = compute_feature_series(bars, "ema")
        rsi = compute_feature_series(bars, "rsi")
        atr = compute_feature_series(bars, "atr")
        macd = compute_feature_series(bars, "macd")
        boll = compute_feature_series(bars, "bollinger")
        vwap = compute_feature_series(bars, "vwap")
        t = 0
        while t < len(bars):
            view = series.visible_until(t)
            self.assertEqual(sma[t], sma_at(view, 20))
            self.assertEqual(ema[t], ema_at(view, 20))
            self.assertEqual(rsi[t], rsi_at(view, 14))
            self.assertEqual(atr[t], atr_at(view, 14))
            self.assertEqual(macd[t], macd_at(view, 12, 26, 9))
            self.assertEqual(boll[t], bollinger_at(view, 20, 2.0))
            self.assertEqual(vwap[t], vwap_at(view, 20, "tick_volume"))
            t += 1


if __name__ == "__main__":
    unittest.main()
