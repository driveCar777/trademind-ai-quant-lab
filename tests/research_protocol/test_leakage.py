import unittest

from research_protocol.leakage import purity_test, sentinel_future_index, synthetic_corpus


class TestLeakage(unittest.TestCase):
    def test_sentinel(self):
        self.assertTrue(sentinel_future_index(synthetic_corpus(20)))

    def test_purity_clean(self):
        result = purity_test(synthetic_corpus(80), split=50)
        self.assertFalse(result["LEAKAGE_DETECTED"])
        self.assertTrue(all(case["ok"] for case in result["cases"]))


if __name__ == "__main__":
    unittest.main()
