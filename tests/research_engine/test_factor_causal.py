import copy
import unittest

from research_engine.factors.compute import feature_at, feature_series
from research_engine.factors.space import build_candidates
from research_engine.fixtures import fixture_a_independent
from research_protocol.errors import FutureDataAccess
from research_protocol.causal import CausalView


class TestFactorCausal(unittest.TestCase):
    def test_future_close_mutation_does_not_change_factor(self):
        bars = fixture_a_independent(80, 11)
        t = 40
        kinds = []
        for row in build_candidates():
            if row["kind"] not in kinds:
                kinds.append((row["kind"], row.get("params") or {}))
        for kind, params in kinds:
            if kind == "random_null":
                continue
            before = feature_at(bars, t, kind, params)
            mutated = copy.deepcopy(bars)
            mutated[-1]["close"] = (mutated[-1]["close"] or 100) * 3.0
            mutated[-1]["high"] = mutated[-1]["close"] + 1
            after = feature_at(mutated, t, kind, params)
            self.assertEqual(before, after, kind)

    def test_causal_view_blocks_future(self):
        bars = fixture_a_independent(20, 3)
        view = CausalView(bars, 5)
        with self.assertRaises(FutureDataAccess):
            view.close(6)

    def test_series_length(self):
        bars = fixture_a_independent(30, 4)
        series = feature_series(bars, "ret", {"n": 3})
        self.assertEqual(len(series), 30)
        self.assertIsNone(series[2])
        self.assertIsNotNone(series[3])


if __name__ == "__main__":
    unittest.main()
