import unittest

from research_engine.controls import control_a_random_direction, control_b_no_prediction
from research_engine.fixtures import fixture_a_independent
from research_protocol.windows import candidate_window


class TestNullControl(unittest.TestCase):
    def test_random_and_never(self):
        bars = fixture_a_independent(120, 7)
        window = candidate_window({"dataset_id": "x"}, bars, lookback=8, holding=3, purge=3, embargo=1)
        a = control_a_random_direction(bars, window, "research", 1, 20260825)
        b = control_b_no_prediction(bars, window, "research", 1, 20260825)
        self.assertEqual(b["observed_effect"], 0.0)
        self.assertEqual(b["p_value"], 1.0)
        self.assertTrue(0 < a["p_value"] <= 1.0)


if __name__ == "__main__":
    unittest.main()
