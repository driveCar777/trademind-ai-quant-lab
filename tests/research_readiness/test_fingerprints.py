import unittest

from research_readiness.engine import analyze_dataset, canonical_hash
from tests.research_readiness.helpers import series, write_dataset


class TestFingerprints(unittest.TestCase):
    def test_same_input_same_hash(self):
        root = write_dataset(series(80), dataset_id="tm-fp")
        a = analyze_dataset(root)
        b = analyze_dataset(root)
        self.assertEqual(a["fingerprint"]["profile_hash"], b["fingerprint"]["profile_hash"])
        self.assertEqual(len(a["fingerprint"]["profile_hash"]), 64)
        self.assertEqual(canonical_hash({"x": 1}), canonical_hash({"x": 1}))


if __name__ == "__main__":
    unittest.main()
