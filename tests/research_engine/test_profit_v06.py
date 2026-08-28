import copy
import unittest

from research_engine.errors import ContractMismatch, FinalOosAccessDenied
from research_engine.fixtures import fixture_a_independent
from research_engine.holdout import final_oos_access
from research_engine.profit.backtest.engine import run_backtest
from research_engine.profit.contract import assert_job_contract, assert_search_space
from research_engine.profit.cost.model import fill_price, spread_price
from research_engine.profit.jobs import make_job
from research_engine.profit.market_state.labels import compact_state_id, state_series
from research_engine.profit.rank import classify_row
from research_engine.profit.risk.sizing import position_qty
from research_engine.profit.strategy_family.signals import signal_tf_breakout
from research_engine.profit.strategy_family.space import build_search_space
from research_protocol.windows import candidate_window


class TestProfitV06(unittest.TestCase):
    def test_space_locked(self):
        space = build_search_space()
        assert_search_space(space)
        self.assertEqual(space["fill"], "NEXT_BAR_OPEN")
        self.assertEqual(space["close_fill"], "FORBIDDEN")
        self.assertEqual(space["strategy_count"], 7)

    def test_worker_cannot_add(self):
        space = build_search_space()
        job = make_job("Xavier-01", "tm-market-GOLD-M15-20260825-000001", space)
        job["strategy_ids"] = list(job["strategy_ids"]) + ["PD-V06-FAKE"]
        with self.assertRaises(ContractMismatch):
            assert_job_contract(job, space)

    def test_oos_denied(self):
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access(reason="v06")

    def test_fill_not_close(self):
        bar = {"open": 100.0, "close": 110.0, "spread": 10, "high": 111, "low": 99}
        px = fill_price(bar, 1, False)
        self.assertNotEqual(px, 110.0)
        self.assertGreater(px, 100.0)

    def test_leverage_cap(self):
        qty = position_qty(10000.0, 0.5, 100.0, 0.01)
        self.assertLessEqual(qty * 100.0, 10000.0 + 1e-9)

    def test_compact_ids(self):
        self.assertEqual(compact_state_id("UP", "STRONG", "LOW", "MID"), "TREND_STRONG_LOWVOL")
        self.assertEqual(compact_state_id("FLAT", "WEAK", "LOW", "MID"), "RANGE_LOWVOL")
        self.assertEqual(compact_state_id("UP", "STRONG", "HIGH", "WIDE"), "FRIC_WIDE")

    def test_future_mutation_leaves_breakout_signal(self):
        bars = fixture_a_independent(80, 4)
        t = 40
        st = {"allow_entry": True, "state_id": "TREND_STRONG_LOWVOL", "trend": "UP"}
        before = signal_tf_breakout(bars, t, st, 20)
        mutated = copy.deepcopy(bars)
        mutated[-1]["close"] = (mutated[-1]["close"] or 100) * 5
        mutated[-1]["high"] = mutated[-1]["close"] + 1
        after = signal_tf_breakout(mutated, t, st, 20)
        self.assertEqual(before, after)

    def test_backtest_deterministic_and_no_close_role(self):
        bars = fixture_a_independent(220, 11)
        window = candidate_window({"dataset_id": "x"}, bars, lookback=20, holding=5, purge=5, embargo=1)
        states, _cuts = state_series(bars, window)
        strat = {
            "family": "MOM-DIR",
            "holding": 8,
            "risk": {"risk_frac": 0.005},
        }
        a = run_backtest(bars, window, "research", states, strat, "M15")
        b = run_backtest(bars, window, "research", states, strat, "M15")
        self.assertEqual(a["metrics"]["trade_count"], b["metrics"]["trade_count"])
        self.assertEqual(a["metrics"]["total_return"], b["metrics"]["total_return"])
        with self.assertRaises(FinalOosAccessDenied):
            run_backtest(bars, window, "final_oos", states, strat, "M15")

    def test_candidate_gate(self):
        good_r = {"total_return": 0.02, "trade_count": 10, "max_drawdown": -0.1, "max_trade_share": 0.2}
        good_v = {"total_return": 0.01, "trade_count": 5, "max_drawdown": -0.1, "max_trade_share": 0.2}
        st, _why = classify_row(good_r, good_v)
        self.assertEqual(st, "CANDIDATE")
        mixed, _why = classify_row({"total_return": -0.01, "trade_count": 20, "max_drawdown": -0.05, "max_trade_share": 0.1}, good_v)
        self.assertEqual(mixed, "WEAK_EDGE")
        none, _why = classify_row({"total_return": -0.01, "trade_count": 20, "max_drawdown": -0.05, "max_trade_share": 0.1}, {"total_return": -0.02, "trade_count": 8, "max_drawdown": -0.05, "max_trade_share": 0.1})
        self.assertEqual(none, "NO_EDGE")

    def test_spread_rule(self):
        self.assertAlmostEqual(spread_price({"close": 4000.0, "spread": 45}), 0.45)
        self.assertAlmostEqual(spread_price({"close": 1.17, "spread": 10}), 0.0001)


if __name__ == "__main__":
    unittest.main()
