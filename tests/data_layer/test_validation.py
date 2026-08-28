import math
import unittest

from tests.data_layer.helpers import make_bar, make_series
from data_layer.validation import validate_bars


class TestValidation(unittest.TestCase):
    def test_high_below_close_fails(self):
        bar = make_bar(1_700_000_000, 1.0, 1.05, 0.9, 1.2)
        quality = validate_bars([bar], "M15")
        self.assertEqual(quality["validation_status"], "FAIL")
        self.assertGreater(quality["invalid_ohlc_count"], 0)

    def test_duplicate_timestamp_fails(self):
        bars = make_series(3)
        bars[2]["timestamp_unix"] = bars[1]["timestamp_unix"]
        bars[2]["timestamp_utc"] = bars[1]["timestamp_utc"]
        quality = validate_bars(bars, "M15")
        self.assertEqual(quality["validation_status"], "FAIL")
        self.assertGreater(quality["duplicate_count"], 0)

    def test_out_of_order_fails(self):
        bars = make_series(3)
        bars[2]["timestamp_unix"] = bars[0]["timestamp_unix"] - 60
        quality = validate_bars(bars, "M15")
        self.assertEqual(quality["validation_status"], "FAIL")
        self.assertGreater(quality["out_of_order_count"], 0)

    def test_nan_fails(self):
        bar = make_bar(1_700_000_000, 1.0, 1.2, 0.9, float("nan"))
        quality = validate_bars([bar], "M15")
        self.assertEqual(quality["validation_status"], "FAIL")
        self.assertGreater(quality["nan_count"], 0)

    def test_inf_fails(self):
        bar = make_bar(1_700_000_000, 1.0, float("inf"), 0.9, 1.1)
        quality = validate_bars([bar], "M15")
        self.assertEqual(quality["validation_status"], "FAIL")
        self.assertGreater(quality["inf_count"], 0)

    def test_zero_price_fails(self):
        bar = make_bar(1_700_000_000, 0.0, 1.2, 0.0, 1.1)
        quality = validate_bars([bar], "M15")
        self.assertEqual(quality["validation_status"], "FAIL")
        self.assertGreater(quality["zero_price_count"], 0)

    def test_real_volume_all_zero_does_not_fail(self):
        bars = make_series(5, real=0)
        quality = validate_bars(bars, "M15")
        self.assertNotEqual(quality["validation_status"], "FAIL")
        self.assertEqual(quality["volume_policy"], "tick_volume_only")
        self.assertEqual(quality["real_volume_zero_count"], 5)

    def test_weekend_gap_is_warn_not_fail(self):
        bars = make_series(2)
        bars[1]["timestamp_unix"] = bars[0]["timestamp_unix"] + 3 * 86400
        from data_layer.schema import unix_to_utc

        bars[1]["timestamp_utc"] = unix_to_utc(bars[1]["timestamp_unix"])
        quality = validate_bars(bars, "M15")
        self.assertNotEqual(quality["validation_status"], "FAIL")
        self.assertGreater(quality["gap_count"], 0)
        self.assertEqual(quality["validation_status"], "WARN")


if __name__ == "__main__":
    unittest.main()
