import unittest

from research_engine.ledger import bump, empty_family_ledger, record_hypothesis


class TestMultipleTestingLedger(unittest.TestCase):
    def test_append(self):
        ledger = empty_family_ledger("FAM-X")
        ledger = record_hypothesis(ledger, "HYP-1")
        ledger = record_hypothesis(ledger, "HYP-2")
        ledger = bump(ledger, "experiment_count", 3)
        self.assertEqual(ledger["variant_count"], 2)
        self.assertEqual(ledger["experiment_count"], 3)
        self.assertFalse(ledger["oos_accessed"])


if __name__ == "__main__":
    unittest.main()
