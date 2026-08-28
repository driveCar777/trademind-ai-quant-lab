import unittest

from research_engine.catalog import hyp_0001_a
from research_engine.fixtures import fixture_a_independent
from research_engine.node_runner import run_variant
from research_protocol.windows import candidate_window


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_hash(self):
        bars = fixture_a_independent(90, 5)
        window = candidate_window({"dataset_id": "x"}, bars, lookback=8, holding=3, purge=3, embargo=1)
        a = run_variant(bars, window, hyp_0001_a(), 20260825, iters_boot=30, iters_perm=30, block_length=8)
        b = run_variant(bars, window, hyp_0001_a(), 20260825, iters_boot=30, iters_perm=30, block_length=8)
        self.assertEqual(a["result_hash"], b["result_hash"])


if __name__ == "__main__":
    unittest.main()
