import copy
import unittest

from research_engine.errors import ContractMismatch, FinalOosAccessDenied
from research_engine.fixtures import fixture_a_independent
from research_engine.holdout import final_oos_access
from research_engine.regime.adx import adx_at
from research_engine.regime.state import freeze_vol_cuts, state_at, state_contract_body
from research_engine.strategy.contract import assert_job_contract, assert_search_space
from research_engine.strategy.evaluate import evaluate_job
from research_engine.strategy.jobs import make_job
from research_engine.strategy.space import build_search_space
from research_protocol.windows import candidate_window


class TestRegimeState(unittest.TestCase):
    def test_future_close_does_not_change_state(self):
        bars = fixture_a_independent(120, 8)
        cuts = {"vol_high": 0.01, "vol_low": 0.001}
        t = 80
        before = state_at(bars, t, cuts)
        mutated = copy.deepcopy(bars)
        mutated[-1]["close"] = (mutated[-1]["close"] or 100) * 4
        mutated[-1]["high"] = mutated[-1]["close"] + 1
        after = state_at(mutated, t, cuts)
        self.assertEqual(before["state_id"], after["state_id"])
        self.assertEqual(before["trend"], after["trend"])
        self.assertEqual(before["strength"], after["strength"])

    def test_adx_period_locked(self):
        bars = fixture_a_independent(80, 3)
        with self.assertRaises(ValueError):
            adx_at(bars, 70, period=13)

    def test_state_contract_hash_stable(self):
        a = state_contract_body()
        b = state_contract_body()
        self.assertEqual(a["state_contract_hash"], b["state_contract_hash"])
        self.assertEqual(a["event"], "UNAVAILABLE")


class TestStrategyContract(unittest.TestCase):
    def test_space_bounded_and_locked(self):
        space = build_search_space()
        assert_search_space(space)
        self.assertGreaterEqual(space["strategy_count"], 8)
        self.assertLessEqual(space["strategy_count"], 30)
        self.assertEqual(space["FINAL_OOS_ACCESS"], "DENIED")

    def test_worker_cannot_add(self):
        space = build_search_space()
        job = make_job("Xavier-01", "tm-market-GOLD-M15-20260825-000001", space)
        job["strategy_ids"] = list(job["strategy_ids"]) + ["SD-V05-FAKE"]
        with self.assertRaises(ContractMismatch):
            assert_job_contract(job, space)

    def test_final_oos_denied(self):
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access(reason="v05")


class TestStrategyEval(unittest.TestCase):
    def test_deterministic(self):
        bars = fixture_a_independent(220, 9)
        window = candidate_window({"dataset_id": "x"}, bars, lookback=20, holding=5, purge=5, embargo=1)
        space = build_search_space()
        one = [space["strategies"][0]]
        a, cuts_a, _occ = evaluate_job(bars, window, one, seed=20260825, iters_boot=15, iters_perm=15)
        b, cuts_b, _occ = evaluate_job(bars, window, one, seed=20260825, iters_boot=15, iters_perm=15)
        self.assertEqual(cuts_a, cuts_b)
        self.assertEqual(a[0]["research"]["delta"], b[0]["research"]["delta"])
        self.assertEqual(a[0]["raw_p"], b[0]["raw_p"])

    def test_vol_cuts_need_values(self):
        cuts = freeze_vol_cuts([0.1, 0.2, 0.3, 0.4, 0.5])
        self.assertIsNotNone(cuts["vol_high"])
        self.assertGreaterEqual(cuts["vol_high"], cuts["vol_low"])


if __name__ == "__main__":
    unittest.main()
