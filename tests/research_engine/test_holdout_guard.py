import unittest

from research_engine.errors import FinalOosAccessDenied
from research_engine.holdout import assert_role_allowed, final_oos_access, final_oos_state
from research_engine.persistence import collect_samples
from research_protocol.windows import candidate_window


class TestHoldoutGuard(unittest.TestCase):
    def test_access_denied(self):
        state = final_oos_state()
        self.assertFalse(state["FINAL_OOS_LOCKED"])
        self.assertEqual(state["FINAL_OOS_STATE"], "CANDIDATE_LOCKED_ACCESS_DENIED")
        self.assertRaises(FinalOosAccessDenied, final_oos_access)
        self.assertRaises(FinalOosAccessDenied, assert_role_allowed, "final_oos_candidate")

    def test_collect_rejects_holdout_role(self):
        bars = [{"close": 1.0 + i * 0.01, "timestamp_utc": "2020-01-01T00:00:00Z"} for i in range(40)]
        window = candidate_window({"dataset_id": "x"}, bars, lookback=5, holding=2, purge=2, embargo=1)
        self.assertRaises(FinalOosAccessDenied, collect_samples, bars, window, "final_oos", 3, 1)


if __name__ == "__main__":
    unittest.main()
