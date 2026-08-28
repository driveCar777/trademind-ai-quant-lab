import unittest

from research_engine.alpha_program import MIN_BACKLOG, V09_LOCKED_HASH
from research_engine.alpha_program.backlog_data import all_questions
from research_engine.alpha_program.guards import assert_no_final_oos, xa_hash_untouched
from research_engine.alpha_program.pipeline import run
from research_engine.alpha_program.score import item_score, rank_implementable
from research_engine.cross_asset import LOCKED_HASH as XA_HASH
from research_engine.errors import FinalOosAccessDenied


class TestAlphaProgramPipeline(unittest.TestCase):
    def test_backlog_size_and_ids(self):
        rows = all_questions()
        self.assertGreaterEqual(len(rows), MIN_BACKLOG)
        ids = [r["id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(i.startswith("RB-") for i in ids))

    def test_killed_and_blocked_score_zero(self):
        rows = {r["id"]: r for r in all_questions()}
        self.assertEqual(item_score(rows["RB-0024"]), 0)
        self.assertEqual(item_score(rows["RB-0015"]), 0)
        self.assertGreater(item_score(rows["RB-0001"]), 0)

    def test_oos_denied(self):
        self.assertTrue(assert_no_final_oos())
        with self.assertRaises(FinalOosAccessDenied):
            from research_engine.holdout import final_oos_access
            final_oos_access()

    def test_frozen_hashes_untouched(self):
        self.assertEqual(V09_LOCKED_HASH, "3ccb614d8a7784b4fe7c57f6f6a7449c3ac87a8111f3d078bf2096415b8c6cea")
        self.assertEqual(xa_hash_untouched(), XA_HASH)

    def test_run_deterministic_and_top_cluster(self):
        a, _ = run(write=False)
        b, _ = run(write=False)
        self.assertEqual(a["content_hash"], b["content_hash"])
        names = [r["cluster"] for r in a["top3_clusters"]]
        self.assertEqual(names[0], "REGIME_TRANSITION")
        self.assertTrue(a["top3_clusters"][0]["keep_v09"])
        self.assertIn("RESIDUAL", names)
        self.assertIn("CALENDAR", names)
        self.assertFalse(a["FINAL_OOS_TOUCHED"])
        scored, live = rank_implementable(all_questions())
        self.assertEqual(len(scored), a["n_questions"])
        self.assertGreaterEqual(len(live), 10)
