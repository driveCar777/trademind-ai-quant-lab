import math
import unittest

from research_engine.cross_residual import LOCKED_HASH, SMA_N
from research_engine.cross_residual.rank import rank_residual
from research_engine.cross_residual.residual import adf_like_stat, build_residual, log_ratio, signal_at
from research_engine.cross_residual.space import build_search_space, canonical_search_space_hash
from research_engine.errors import FinalOosAccessDenied
from research_engine.holdout import final_oos_access


class TestCrossResidual(unittest.TestCase):
    def test_hash(self):
        self.assertEqual(canonical_search_space_hash(), LOCKED_HASH)
        space = build_search_space()
        self.assertEqual(space["residual"], "LOG_GOLD_OVER_OIL_MINUS_SMA60")
        self.assertEqual(space["hold_bars"], 5)
        self.assertEqual(SMA_N, 60)

    def test_log_ratio(self):
        self.assertAlmostEqual(log_ratio(math.e, 1.0), 1.0)
        self.assertIsNone(log_ratio(0, 1))
        self.assertIsNone(log_ratio(1, 0))

    def test_residual_mean_reverts_on_flat_spread(self):
        rows = []
        i = 0
        while i < 80:
            rows.append({"GOLD_close": 2000.0, "OIL_close": 80.0, "role": "research"})
            i += 1
        out = build_residual(rows, sma_n=10)
        self.assertIsNone(out[5]["resid"])
        self.assertAlmostEqual(out[20]["resid"], 0.0, places=9)

    def test_signals(self):
        cuts = {"p33": -1.0, "p67": 1.0}
        rich = {"resid": 1.5, "GOLD_ret": 0.01, "OIL_ret": 0.01}
        cheap = {"resid": -1.5, "GOLD_ret": 0.01, "OIL_ret": 0.01}
        crash = {"resid": 2.0, "GOLD_ret": -0.02, "OIL_ret": -0.03}
        self.assertEqual(signal_at(rich, {"kind": "RICH"}, cuts), -1)
        self.assertEqual(signal_at(cheap, {"kind": "CHEAP"}, cuts), 1)
        self.assertEqual(signal_at(crash, {"kind": "JOINT_RISKOFF"}, cuts), -1)
        self.assertEqual(signal_at(rich, {"kind": "JOINT_RISKOFF"}, cuts), 0)

    def test_adf_like(self):
        xs = [1.0]
        i = 0
        while i < 40:
            xs.append(xs[-1] * 0.2)
            i += 1
        stat = adf_like_stat(xs)
        self.assertIsNotNone(stat)
        self.assertLess(stat["ar1_delta_beta"], 0.0)

    def test_rank_no_candidate_on_empty(self):
        ranking = rank_residual([])
        self.assertEqual(ranking["outcome"], "NO_CANDIDATE")

    def test_no_oos(self):
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access(reason="residual")

    def test_not_v08_ids(self):
        space = build_search_space()
        self.assertNotIn("HYP-XA-0001", space["hypothesis_ids"])
        self.assertNotIn("HYP-RT-0001", space["hypothesis_ids"])
