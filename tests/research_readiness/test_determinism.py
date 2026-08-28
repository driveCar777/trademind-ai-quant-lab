import unittest

from research_readiness.engine import analyze_dataset
from tests.research_readiness.helpers import series, write_dataset


class TestDeterminism(unittest.TestCase):
    def test_twenty_repeats_match(self):
        root = write_dataset(series(120))
        hashes = []
        for _ in range(20):
            hashes.append(analyze_dataset(root)["fingerprint"]["profile_hash"])
        self.assertEqual(len(set(hashes)), 1)


if __name__ == "__main__":
    unittest.main()
