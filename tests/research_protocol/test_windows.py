import unittest

from research_protocol.windows import candidate_window, window_guard


class TestWindows(unittest.TestCase):
    def test_timestamps_not_just_index(self):
        bars = []
        for i in range(200):
            bars.append({"timestamp_utc": "2024-01-01T00:00:00Z", "timestamp_unix": i})
        bars[0]["timestamp_utc"] = "2024-01-01T00:00:00Z"
        bars[139]["timestamp_utc"] = "2024-06-01T00:00:00Z"
        win = candidate_window({"dataset_id": "x"}, bars, lookback=10, holding=5, purge=5, embargo=1)
        self.assertIn("start_timestamp_utc", win["research"])
        self.assertFalse(win["FINAL_OOS_LOCKED"])
        self.assertEqual(win["role"], "CANDIDATE_WINDOW")
        ok, reason = window_guard(win["research_label_usable_end_index"] + 1, None, win, "research")
        self.assertFalse(ok)
        self.assertEqual(reason, "PURGE")


if __name__ == "__main__":
    unittest.main()
