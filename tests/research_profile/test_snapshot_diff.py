import os
import unittest

from research_profile.snapshot_diff import compare_datasets
from tests.research_profile.helpers import series, write_dataset


class TestSnapshotDiff(unittest.TestCase):
    def test_identical_snapshots(self):
        bars = series(8)
        a, _ = write_dataset(bars, dataset_id="A")
        b, _ = write_dataset(bars, dataset_id="B")
        result = compare_datasets(a, b)
        self.assertEqual(result["same_rows"], 8)
        self.assertEqual(result["changed_rows"], 0)
        self.assertFalse(result["HISTORICAL_MUTATION"])

    def test_closed_ohlc_change_is_mutation(self):
        bars_a = series(6)
        bars_b = series(6)
        bars_b[1]["close"] = bars_b[1]["close"] + 5
        bars_b[1]["high"] = bars_b[1]["high"] + 5
        a, _ = write_dataset(bars_a, dataset_id="A")
        b, _ = write_dataset(bars_b, dataset_id="B")
        result = compare_datasets(a, b)
        self.assertTrue(result["HISTORICAL_MUTATION"])
        self.assertGreater(result["historical_mutation_count"], 0)

    def test_last_bar_change_is_not_mutation(self):
        bars_a = series(6)
        bars_b = series(6)
        bars_b[-1]["close"] = bars_b[-1]["close"] + 1
        bars_b[-1]["high"] = bars_b[-1]["high"] + 1
        a, _ = write_dataset(bars_a, dataset_id="A")
        b, _ = write_dataset(bars_b, dataset_id="B")
        result = compare_datasets(a, b)
        self.assertFalse(result["HISTORICAL_MUTATION"])
        self.assertEqual(result["changed_rows"], 1)


if __name__ == "__main__":
    unittest.main()
