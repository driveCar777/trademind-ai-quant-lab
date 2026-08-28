import os
import tempfile
import unittest

from research_profile.research_probe import build_profile
from tests.research_profile.helpers import series, write_dataset


class TestProfileSchema(unittest.TestCase):
    def test_required_identity_fields(self):
        root, _sha = write_dataset(series(40), dataset_id="tm-test-GOLD-M15-000001")
        profile, _ = build_profile(root, "Xavier-01", os.path.abspath("research_profile/research_probe.py"))
        for key in (
            "dataset_id",
            "logical_symbol",
            "mt5_symbol",
            "timeframe",
            "row_count",
            "start_utc",
            "end_utc",
            "timezone",
            "sha256",
            "validation_status",
            "qualification",
            "profile_version",
            "profile_code_version",
            "xavier",
            "generated_at_utc",
        ):
            self.assertIn(key, profile)
        self.assertEqual(profile["timezone"], "UTC")
        self.assertEqual(profile["xavier"], "Xavier-01")
        self.assertFalse(profile["FINAL_OOS_LOCKED"])


if __name__ == "__main__":
    unittest.main()
