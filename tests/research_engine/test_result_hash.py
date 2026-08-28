import unittest

from research_engine.catalog import hyp_0001_a
from research_engine.fixtures import fixture_a_independent, fixture_e_result_tamper
from research_engine.node_runner import run_variant
from research_protocol.hashing import canonical_hash
from research_protocol.windows import candidate_window


class TestResultHash(unittest.TestCase):
    def test_tamper_changes_hash(self):
        bars = fixture_a_independent(80, 2)
        window = candidate_window({"dataset_id": "x"}, bars, lookback=8, holding=3, purge=3, embargo=1)
        clean = run_variant(bars, window, hyp_0001_a(), 20260825, iters_boot=40, iters_perm=40, block_length=8)
        dirty = fixture_e_result_tamper(clean)
        dirty.pop("result_hash", None)
        self.assertNotEqual(canonical_hash(dirty), clean["result_hash"])


if __name__ == "__main__":
    unittest.main()
