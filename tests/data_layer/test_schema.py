import unittest

from tests.data_layer.helpers import make_bar, make_series
from data_layer.schema import required_columns
from data_layer.validation import validate_bars


class TestSchema(unittest.TestCase):
    def test_required_columns_include_ohlc_and_volumes(self):
        cols = required_columns()
        for name in ("timestamp_utc", "open", "high", "low", "close", "tick_volume", "real_volume"):
            self.assertIn(name, cols)
        self.assertNotIn("volume", cols)

    def test_missing_open_fails(self):
        bar = make_bar(1_700_000_000, 1, 2, 0.5, 1.2)
        del bar["open"]
        quality = validate_bars([bar], "M15")
        self.assertEqual(quality["validation_status"], "FAIL")
        self.assertTrue(
            "missing_columns" in quality["fail_reasons"] or quality["missing_column_count"] > 0
        )

    def test_null_not_filled_as_zero(self):
        bar = make_bar(1_700_000_000, 1, 2, 0.5, 1.2)
        bar["spread"] = None
        quality = validate_bars([bar], "M15")
        self.assertEqual(quality["spread_zero_count"], 0)
        self.assertTrue(quality["spread_present"] is False or quality["spread_zero_count"] == 0)


if __name__ == "__main__":
    unittest.main()
