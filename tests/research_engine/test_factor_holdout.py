import unittest

from research_engine.discovery.contract import assert_no_final_oos
from research_engine.discovery.evaluate import collect_pairs
from research_engine.errors import FinalOosAccessDenied
from research_engine.factors.compute import feature_series
from research_engine.fixtures import fixture_a_independent
from research_engine.holdout import final_oos_access
from research_protocol.windows import candidate_window


class TestFactorHoldout(unittest.TestCase):
    def test_final_oos_access_denied(self):
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access(reason="factor_discovery")

    def test_role_blocked(self):
        with self.assertRaises(FinalOosAccessDenied):
            assert_no_final_oos("final_oos")
        with self.assertRaises(FinalOosAccessDenied):
            assert_no_final_oos("holdout")

    def test_collect_rejects_holdout_role(self):
        bars = fixture_a_independent(80, 2)
        window = candidate_window({"dataset_id": "x"}, bars, lookback=8, holding=3, purge=3, embargo=1)
        feats = feature_series(bars, "ret", {"n": 3})
        with self.assertRaises(FinalOosAccessDenied):
            collect_pairs(bars, feats, window, "final_oos", "future_return", 1)


if __name__ == "__main__":
    unittest.main()
