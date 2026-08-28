import unittest

from research_engine.alpha_program.scoring.catalog import all_mechanisms
from research_engine.alpha_program.scoring.classifier import classify, opportunity_score, rank_mechanisms


class TestMechanismEngine(unittest.TestCase):
    def test_catalog_covers_families(self):
        rows = all_mechanisms()
        families = set(r["family"] for r in rows)
        self.assertIn("Price Formation", families)
        self.assertIn("Market Structure", families)
        self.assertIn("Relative Value", families)
        self.assertIn("Risk Premium", families)

    def test_price_formation_failed(self):
        rows = {r["id"]: r for r in all_mechanisms()}
        for rid in ("PF-MOM", "PF-REV", "PF-BO", "PF-VOLC"):
            self.assertEqual(rows[rid]["status"], "FAILED")
            self.assertEqual(opportunity_score(rows[rid]), 0)

    def test_risk_premium_blocked(self):
        rows = {r["id"]: r for r in all_mechanisms()}
        for rid in ("RP-IV", "RP-OPT", "RP-CARRY", "RP-FUND"):
            self.assertEqual(rows[rid]["status"], "BLOCKED")
            self.assertEqual(classify(rows[rid])["score"], 0)
            self.assertFalse(classify(rows[rid])["implementable"])

    def test_v09_splits_present(self):
        ids = set(r["id"] for r in all_mechanisms())
        self.assertIn("MS-RT-LVH", ids)
        self.assertIn("MS-RT-HVL", ids)
        self.assertIn("MS-RT-WTS", ids)
        self.assertIn("MS-RT-STX", ids)
        self.assertIn("MS-RT-CORR", ids)

    def test_relative_value_not_v08(self):
        text = " ".join(r["mechanism"] + r["next_action"] for r in all_mechanisms() if r["family"] == "Relative Value")
        self.assertIn("residual", text.lower())
        self.assertNotIn("USDJPY -> GOLD", text)

    def test_score_multiplicative(self):
        row = {
            "id": "X",
            "economic_plausibility": 4,
            "data_availability": 5,
            "historical_coverage": 3,
            "existing_evidence": 2,
            "implementation_feasibility": 5,
            "status": "UNKNOWN",
        }
        self.assertEqual(opportunity_score(row), 4 * 5 * 3 * 2 * 5)

    def test_rank_puts_v09_ahead_of_blocked(self):
        scored, live = rank_mechanisms(all_mechanisms())
        live_ids = [r["id"] for r in live]
        self.assertIn("MS-RT-LVH", live_ids)
        self.assertNotIn("RP-IV", live_ids)
        self.assertGreater(len(live), 3)
        self.assertEqual(len(scored), len(all_mechanisms()))
