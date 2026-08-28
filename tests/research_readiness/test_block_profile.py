import unittest

from research_readiness.engine import BLOCK_COUNT, BLOCK_SIZE, analyze_dataset
from tests.research_readiness.helpers import series, write_dataset


class TestBlockProfile(unittest.TestCase):
    def test_eight_blocks(self):
        root = write_dataset(series(2000))
        analysis = analyze_dataset(root)
        self.assertEqual(len(analysis["blocks"]), BLOCK_COUNT)
        self.assertEqual(analysis["blocks"][0]["row_count"], BLOCK_SIZE)
        self.assertEqual(analysis["blocks"][-1]["end"], 1999)


if __name__ == "__main__":
    unittest.main()
