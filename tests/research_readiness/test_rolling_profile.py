import unittest

from research_readiness.engine import analyze_dataset
from tests.research_readiness.helpers import series, write_dataset


class TestRollingProfile(unittest.TestCase):
    def test_nineteen_windows(self):
        root = write_dataset(series(2000))
        analysis = analyze_dataset(root)
        self.assertEqual(len(analysis["rolling"]), 19)


if __name__ == "__main__":
    unittest.main()
