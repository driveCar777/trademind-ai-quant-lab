import unittest

from research_engine.catalog import hyp_0001_a
from research_engine.fixtures import fixture_b_positive_persistence, fixture_c_negative_persistence
from research_engine.node_runner import run_variant, sentinel_ok
from research_protocol.windows import candidate_window


class TestSyntheticSuite(unittest.TestCase):
    def test_persistence_fixtures(self):
        hyp = hyp_0001_a()
        pos_bars = fixture_b_positive_persistence(200)
        neg_bars = fixture_c_negative_persistence(200)
        wp = candidate_window({"dataset_id": "B"}, pos_bars, lookback=8, holding=3, purge=3, embargo=1)
        wn = candidate_window({"dataset_id": "C"}, neg_bars, lookback=8, holding=3, purge=3, embargo=1)
        pos = run_variant(pos_bars, wp, hyp, 20260825, iters_boot=40, iters_perm=40, block_length=8)
        neg = run_variant(neg_bars, wn, hyp, 20260825, iters_boot=40, iters_perm=40, block_length=8)
        self.assertGreater(pos["research"]["positive"]["delta"], 0)
        self.assertLess(neg["research"]["negative"]["delta"], 0)
        self.assertTrue(sentinel_ok(pos_bars))


if __name__ == "__main__":
    unittest.main()
