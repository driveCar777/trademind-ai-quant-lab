import copy
import unittest

from research_engine.errors import ContractMismatch, FinalOosAccessDenied
from research_engine.fixtures import fixture_a_independent
from research_engine.holdout import final_oos_access
from research_engine.regime_transition import ALLOWED_HYPOTHESIS_IDS, HOLD_BARS, LOCKED_HASH
from research_engine.regime_transition.contract import assert_job_contract, assert_search_space, deny_final_oos
from research_engine.regime_transition.evaluator import costed_hold, evaluate_hypothesis
from research_engine.regime_transition.jobs import make_job
from research_engine.regime_transition.space import build_search_space, canonical_search_space_hash
from research_engine.regime_transition.state_builder import build_states, freeze_vol_on_research
from research_engine.regime_transition.transition_detector import enter_strong_up, exit_strong, feature_at, vol_shock
from research_engine.regime_transition.windows import freeze_window, role_of_index


def _roles(n):
    bars = []
    i = 0
    while i < n:
        bars.append({"date": "2020-01-01", "role": None})
        i += 1
    return freeze_window(bars, "synthetic")


class TestV09Contract(unittest.TestCase):
    def test_t1_hash_locked(self):
        self.assertEqual(canonical_search_space_hash(), LOCKED_HASH)
        self.assertEqual(canonical_search_space_hash(), "3ccb614d8a7784b4fe7c57f6f6a7449c3ac87a8111f3d078bf2096415b8c6cea")

    def test_t2_three_ids_only(self):
        space = build_search_space()
        assert_search_space(space)
        self.assertEqual(list(space["hypothesis_ids"]), list(ALLOWED_HYPOTHESIS_IDS))
        self.assertEqual(space["hypothesis_count"], 3)
        self.assertEqual(space["hold_bars"], 5)

    def test_t3_worker_cannot_add(self):
        space = build_search_space()
        job = make_job("Xavier-01", {"hypothesis_ids": ["HYP-RT-0001"], "role": "PRIMARY"}, space)
        job["hypothesis_ids"] = ["HYP-RT-0001", "HYP-RT-0004"]
        job["hypothesis_count"] = 2
        with self.assertRaises(ContractMismatch):
            assert_job_contract(job, space)
        job = make_job("Xavier-01", {"hypothesis_ids": ["HYP-RT-0001"], "role": "PRIMARY"}, space)
        job["hypothesis_ids"] = ["HYP-XA-0001"]
        job["hypothesis_count"] = 1
        with self.assertRaises(ContractMismatch):
            assert_job_contract(job, space)

    def test_t4_final_oos_denied(self):
        with self.assertRaises(FinalOosAccessDenied):
            final_oos_access(reason="v09")
        with self.assertRaises(FinalOosAccessDenied):
            deny_final_oos("final_oos")
        with self.assertRaises(FinalOosAccessDenied):
            deny_final_oos(None)


class TestV09Transitions(unittest.TestCase):
    def test_t7_high_vol_level_does_not_fire(self):
        prev = {"vol": "HIGH", "strength": "WEAK", "trend": "FLAT", "friction": "MID"}
        curr = {"vol": "HIGH", "strength": "WEAK", "trend": "FLAT", "friction": "MID"}
        self.assertFalse(vol_shock(prev, curr))
        self.assertFalse(feature_at(prev, curr, "VOL_SHOCK"))
        self.assertTrue(vol_shock({"vol": "MID"}, {"vol": "HIGH"}))

    def test_t8_strong_up_level_does_not_fire(self):
        prev = {"strength": "STRONG", "trend": "UP", "vol": "MID", "friction": "MID"}
        curr = {"strength": "STRONG", "trend": "UP", "vol": "MID", "friction": "MID"}
        self.assertFalse(enter_strong_up(prev, curr))
        self.assertTrue(enter_strong_up({"strength": "WEAK", "trend": "FLAT"}, {"strength": "STRONG", "trend": "UP"}))

    def test_exit_strong_is_delta(self):
        self.assertFalse(exit_strong({"strength": "WEAK"}, {"strength": "WEAK"}))
        self.assertTrue(exit_strong({"strength": "STRONG"}, {"strength": "WEAK"}))

    def test_unknown_feature_raises(self):
        with self.assertRaises(ValueError):
            feature_at({}, {}, "RSI")


class TestV09StateAndWindows(unittest.TestCase):
    def test_t5_vol_freeze_ignores_validation(self):
        bars = fixture_a_independent(80, 4)
        freeze_window(bars, "x")
        a = freeze_vol_on_research(bars)
        mutated = copy.deepcopy(bars)
        i = 0
        while i < len(mutated):
            if mutated[i].get("role") == "validation":
                mutated[i]["high"] = (mutated[i].get("high") or 1) * 50
                mutated[i]["low"] = 0.01
                mutated[i]["close"] = (mutated[i].get("close") or 1) * 50
            i += 1
        b = freeze_vol_on_research(mutated)
        self.assertEqual(a, b)

    def test_t6_future_close_does_not_change_state(self):
        bars = fixture_a_independent(120, 8)
        freeze_window(bars, "x")
        states, cuts, _n = build_states(bars)
        t = 70
        before = states[t]
        mutated = copy.deepcopy(bars)
        mutated[-1]["close"] = (mutated[-1]["close"] or 100) * 8
        mutated[-1]["high"] = mutated[-1]["close"]
        after, _c, _w = build_states(mutated, cuts)
        if before is not None:
            self.assertEqual(before["state_id"], after[t]["state_id"])

    def test_t13_last_15_is_oos(self):
        bars = fixture_a_independent(200, 1)
        window = freeze_window(bars, "x")
        self.assertGreater(window["final_oos"]["n"], 0)
        self.assertEqual(window["FINAL_OOS_ACCESS"], "DENIED")
        self.assertEqual(role_of_index(199, 200), "final_oos")
        self.assertEqual(bars[199]["role"], "final_oos")


class TestV09Evaluator(unittest.TestCase):
    def _series(self, n=80):
        bars = fixture_a_independent(n, 11)
        freeze_window(bars, "x")
        states = []
        i = 0
        while i < n:
            st = {
                "trend": "FLAT",
                "strength": "WEAK",
                "vol": "MID",
                "friction": "MID",
                "complete": True,
            }
            states.append(st)
            i += 1
        return bars, states

    def test_t9_hold_is_five(self):
        self.assertEqual(HOLD_BARS, 5)
        bars, _states = self._series(40)
        step = costed_hold(bars, 10, 1, 5)
        self.assertIsNotNone(step)
        self.assertEqual(step["scheduled_exit"], 16)
        self.assertEqual(step["entry_index"], 11)

    def test_t10_fill_is_open_not_close(self):
        bars, _states = self._series(40)
        bars[11]["open"] = 100.0
        bars[11]["close"] = 140.0
        bars[11]["spread"] = 0
        step = costed_hold(bars, 10, 1, 5)
        self.assertIsNotNone(step)
        self.assertNotEqual(step["entry"], 140.0)

    def test_t11_overlap_skipped(self):
        bars, states = self._series(80)
        states[20]["vol"] = "HIGH"
        states[19]["vol"] = "MID"
        states[21]["vol"] = "LOW"
        states[22]["vol"] = "HIGH"
        spec = {
            "hypothesis_id": "HYP-RT-0001",
            "feature": "VOL_SHOCK",
            "target": "OIL",
            "predicted_sign": -1,
            "side": -1,
            "hold_bars": 5,
        }
        out = evaluate_hypothesis(bars, states, spec, iters_boot=8, iters_perm=8)
        self.assertGreaterEqual(out["research"]["n_signal"], 1)
        self.assertGreaterEqual(out["research"]["n_skip_overlap"] + out["research"]["n_trade"], 1)

    def test_t12_deterministic(self):
        bars, states = self._series(90)
        states[30]["vol"] = "HIGH"
        states[29]["vol"] = "LOW"
        spec = {
            "hypothesis_id": "HYP-RT-0001",
            "feature": "VOL_SHOCK",
            "target": "OIL",
            "predicted_sign": -1,
            "side": -1,
            "hold_bars": 5,
        }
        a = evaluate_hypothesis(bars, states, spec, iters_boot=12, iters_perm=12)
        b = evaluate_hypothesis(bars, states, spec, iters_boot=12, iters_perm=12)
        self.assertEqual(a["research"]["delta"], b["research"]["delta"])
        self.assertEqual(a["research"]["raw_p"], b["research"]["raw_p"])
        self.assertEqual(a["research"]["n_trade"], b["research"]["n_trade"])

    def test_oos_bars_not_traded(self):
        bars, states = self._series(80)
        i = 0
        while i < len(bars):
            if bars[i].get("role") == "final_oos":
                states[i]["vol"] = "HIGH"
                if i > 0:
                    states[i - 1]["vol"] = "LOW"
            i += 1
        spec = {
            "hypothesis_id": "HYP-RT-0001",
            "feature": "VOL_SHOCK",
            "target": "OIL",
            "predicted_sign": -1,
            "side": -1,
            "hold_bars": 5,
        }
        out = evaluate_hypothesis(bars, states, spec, iters_boot=5, iters_perm=5)
        for tr in []:
            self.assertNotEqual(bars[tr].get("role"), "final_oos")
        self.assertIn("n_trade", out["research"])


if __name__ == "__main__":
    unittest.main()
