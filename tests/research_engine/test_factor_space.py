import unittest

from research_engine.discovery.contract import assert_search_space, hash_search_space
from research_engine.factors.space import build_candidates, build_search_space


class TestFactorSpace(unittest.TestCase):
    def test_ids_reproducible_and_bounded(self):
        a = build_candidates()
        b = build_candidates()
        self.assertEqual([x["candidate_id"] for x in a], [x["candidate_id"] for x in b])
        self.assertGreaterEqual(len(a), 50)
        self.assertLessEqual(len(a), 250)
        ids = [x["candidate_id"] for x in a]
        self.assertEqual(len(ids), len(set(ids)))

    def test_search_space_hash_stable(self):
        space = build_search_space()
        assert_search_space(space)
        self.assertEqual(space["search_space_hash"], hash_search_space(space))
        self.assertEqual(space["FINAL_OOS_ACCESS"], "DENIED")
        self.assertEqual(space["seed"], 20260825)
        again = build_search_space()
        self.assertEqual(space["search_space_hash"], again["search_space_hash"])

    def test_volume_metadata(self):
        found = False
        for row in build_candidates():
            if row["family_id"] == "FAM-FD-VOLUME-0001":
                self.assertEqual(row.get("volume_type"), "tick_volume")
                found = True
        self.assertTrue(found)


if __name__ == "__main__":
    unittest.main()
