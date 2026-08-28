import unittest

from research_engine.alpha_program.guards import assert_no_final_oos
from research_engine.cross_residual.residual import freeze_residual_cuts
from research_engine.errors import FinalOosAccessDenied
from research_engine.holdout import assert_role_allowed, final_oos_access
from research_engine.regime_transition.contract import deny_final_oos
from research_engine.regime_transition.windows import freeze_window
from research_engine.strategy.contract import assert_no_final_oos as strategy_no_oos


class TestNoOosAccess(unittest.TestCase):
    def test_direct_access_denied(self):
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access()

    def test_roles_denied(self):
        for role in ("final_oos", "final_oos_candidate", "holdout", "FINAL_OOS"):
            with self.assertRaises(FinalOosAccessDenied):
                assert_role_allowed(role)

    def test_pipeline_guard(self):
        self.assertTrue(assert_no_final_oos())

    def test_v09_deny(self):
        with self.assertRaises(FinalOosAccessDenied):
            deny_final_oos("final_oos")

    def test_window_records_oos_without_returns(self):
        bars = []
        i = 0
        while i < 20:
            bars.append({"date": "2020-01-%02d" % (i + 1), "close": 1.0 + i})
            i += 1
        window = freeze_window(bars, "x")
        self.assertEqual(window["final_oos"]["ACCESS"], "DENIED")
        self.assertNotIn("returns", window["final_oos"])

    def test_residual_freeze_ignores_oos_rows(self):
        cuts = freeze_residual_cuts([{"role": "final_oos", "resid": 9.0}] + [{"role": "research", "resid": float(i)} for i in range(10)])
        self.assertIn("p33", cuts)
        self.assertLess(cuts["p67"], 9.0)

    def test_strategy_guard_still_denies(self):
        with self.assertRaises(FinalOosAccessDenied):
            strategy_no_oos("final_oos")
