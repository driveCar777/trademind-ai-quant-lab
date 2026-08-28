import os
import unittest

from research_profile.research_probe import build_profile, qualify
from tests.research_profile.helpers import bar, series, write_dataset


class TestQualification(unittest.TestCase):
    def test_warnings_for_real_volume_zero_and_gaps(self):
        bars = series(30)
        bars[-1]["timestamp_unix"] = bars[-2]["timestamp_unix"] + 15 * 60 * 5
        from data_layer.schema import unix_to_utc

        bars[-1]["timestamp_utc"] = unix_to_utc(bars[-1]["timestamp_unix"])
        root, _ = write_dataset(bars)
        profile, _ = build_profile(root, "Xavier-01", os.path.abspath("research_profile/research_probe.py"))
        self.assertEqual(profile["qualification"], "QUALIFIED_WITH_WARNINGS")
        self.assertFalse(profile["FINAL_OOS_LOCKED"])

    def test_invalid_on_hash_fail(self):
        status, hard, _ = qualify(False, [], [], {"overlap_count": 0}, {}, [], 10)
        self.assertEqual(status, "DATA_INVALID")
        self.assertIn("hash_mismatch", hard)

    def test_review_on_overlap(self):
        bars = [bar(1, 1, 2, 0.5, 1), bar(1, 1, 2, 0.5, 1)]
        status, _hard, review = qualify(True, bars, [], {"overlap_count": 2}, {"real_volume_row_count": 0}, [], 2)
        self.assertEqual(status, "DATA_REVIEW_REQUIRED")
        self.assertIn("interval_overlap", review)


if __name__ == "__main__":
    unittest.main()
