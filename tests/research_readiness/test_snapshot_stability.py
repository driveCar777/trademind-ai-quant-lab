import unittest

from research_profile.snapshot_diff import compare_datasets
from tests.research_readiness.helpers import series, write_dataset


class TestSnapshotStability(unittest.TestCase):
    def test_last_bar_only_is_pass(self):
        a = series(8)
        b = series(8)
        b[-1]["close"] += 1
        b[-1]["high"] += 1
        result = compare_datasets(write_dataset(a, dataset_id="A"), write_dataset(b, dataset_id="B"))
        self.assertFalse(result["HISTORICAL_MUTATION"])
        self.assertEqual(result["changed_rows"], 1)


if __name__ == "__main__":
    unittest.main()
