import os
import unittest

from research_profile.research_probe import build_profile, comparable
from tests.research_profile.helpers import series, write_dataset


class TestNodeDeterminism(unittest.TestCase):
    def test_same_input_same_metrics(self):
        root, _ = write_dataset(series(80), dataset_id="tm-det-GOLD-M15-000001")
        probe = os.path.abspath("research_profile/research_probe.py")
        a, _ = build_profile(root, "Xavier-01", probe)
        b, _ = build_profile(root, "Xavier-04", probe)
        self.assertEqual(comparable(a), comparable(b))
        self.assertNotEqual(a["xavier"], b["xavier"])


if __name__ == "__main__":
    unittest.main()
