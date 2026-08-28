import unittest

from research_engine.family import family_record, seal_family


class TestFamilyRegistry(unittest.TestCase):
    def test_counts(self):
        rec = seal_family(
            family_record(
                "FAM-PERSISTENCE-0001",
                "HYP-0001",
                [
                    {"hypothesis_id": "HYP-0001-A", "status": "FALSIFIED", "validated": True},
                    {"hypothesis_id": "HYP-0001-B", "status": "INCONCLUSIVE", "validated": True},
                ],
            )
        )
        self.assertEqual(rec["number_of_variants"], 2)
        self.assertEqual(rec["rejected_count"], 1)
        self.assertTrue(rec["family_hash"])


if __name__ == "__main__":
    unittest.main()
