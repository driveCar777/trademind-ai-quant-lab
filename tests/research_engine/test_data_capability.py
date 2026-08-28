import unittest

from research_engine.alpha_program.data_capability import TARGETS, build_plan, inventory_disk
from research_engine.alpha_program.evidence.extract import coverage_status, years_between
from research_engine.errors import FinalOosAccessDenied
from research_engine.holdout import final_oos_access


class TestDataCapability(unittest.TestCase):
    def test_targets(self):
        self.assertEqual(TARGETS["D1"], 10.0)
        self.assertEqual(TARGETS["H1"], 3.0)
        self.assertEqual(TARGETS["M15"], 2.0)

    def test_years_and_status(self):
        self.assertAlmostEqual(years_between("2020-03-26T00:00:00Z", "2026-08-25T00:00:00Z"), 6.4, places=1)
        self.assertEqual(coverage_status(6.4, 10), "FAILED")
        self.assertEqual(coverage_status(10.0, 10), "DONE")
        self.assertEqual(coverage_status(None, 10), "UNKNOWN")

    def test_inventory_shortfall(self):
        rows = inventory_disk()
        self.assertGreaterEqual(len(rows), 16)
        d1 = [r for r in rows if r["timeframe"] == "D1"]
        self.assertTrue(d1)
        self.assertTrue(any(r["coverage"] == "SHORTFALL" for r in d1))
        m15 = [r for r in rows if r["timeframe"] == "M15"]
        self.assertTrue(any(r["coverage"] == "SHORTFALL" for r in m15))

    def test_plan_without_probe_is_blocked_or_possible(self):
        rows = inventory_disk()
        plan = build_plan(rows, {"ok": False, "status": "DATA_BLOCKED", "rows": []})
        self.assertIn(plan["status"], ("DATA_BLOCKED", "ACQUISITION_POSSIBLE", "MEETS_TARGET"))
        self.assertFalse(plan["FINAL_OOS_TOUCHED"])

    def test_no_oos(self):
        inventory_disk()
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access()
