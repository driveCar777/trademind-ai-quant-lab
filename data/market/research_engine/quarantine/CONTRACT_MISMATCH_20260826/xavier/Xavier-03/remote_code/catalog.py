"""Frozen HYP-0001 family. Parameters are pre-registered, not optimized."""
from __future__ import print_function

from research_engine import BLOCK_LENGTH, BOOTSTRAP_ITERS, FDR_Q, PERMUTATION_ITERS, SEED
from research_engine.hypothesis import make_hypothesis

DATASETS = [
    "tm-market-GOLD-M15-20260825-000001",
    "tm-market-GOLD-H1-20260825-000001",
    "tm-market-GOLD-H4-20260825-000001",
    "tm-market-GOLD-D1-20260825-000001",
    "tm-market-EURUSD-M15-20260825-000001",
    "tm-market-EURUSD-H1-20260825-000001",
    "tm-market-EURUSD-H4-20260825-000001",
    "tm-market-EURUSD-D1-20260825-000001",
    "tm-market-USDJPY-M15-20260825-000001",
    "tm-market-USDJPY-H1-20260825-000001",
    "tm-market-USDJPY-H4-20260825-000001",
    "tm-market-USDJPY-D1-20260825-000001",
    "tm-market-OIL-M15-20260825-000001",
    "tm-market-OIL-H1-20260825-000001",
    "tm-market-OIL-H4-20260825-000001",
    "tm-market-OIL-D1-20260825-000001",
]

THRESHOLDS = {
    "min_condition_n": 30,
    "min_abs_delta": 0.0,
    "min_abs_effect_size": 0.10,
    "max_adjusted_p": 0.05,
    "require_direction_agreement": True,
    "require_ci_excludes_zero": True,
    "fdr_q": FDR_Q,
}


def _base(hid, parent, horizon, title_suffix):
    return make_hypothesis(
        {
            "hypothesis_id": hid,
            "title": "Short-Horizon Directional Persistence%s" % title_suffix,
            "statement": (
                "In the same timeframe, after three consecutive closed bars share a return sign, "
                "the return of the next closed bar at a fixed horizon is displaced from the unconditional mean."
            ),
            "rationale": "Tests a pre-registered persistence claim without RSI/MACD/Bollinger/MA/VWAP or V11.7 parameters.",
            "prediction": "Conditional mean return after a same-sign streak differs from the unconditional mean.",
            "direction": "unspecified_both_signs",
            "universe": list(DATASETS),
            "timeframes": ["M15", "H1", "H4", "D1"],
            "features": ["close_return_sign_streak"],
            "parameters": {"streak_length": 3, "prediction_horizon": horizon, "seed": SEED, "block_length": BLOCK_LENGTH},
            "parameter_source": "pre_registered_not_optimized",
            "entry_definition": "none_predictive",
            "exit_definition": "none_predictive",
            "target_definition": "simple_return_at_t_plus_horizon",
            "horizon": horizon,
            "research_metrics": ["delta", "effect_size", "permutation_p", "bootstrap_ci", "block_bootstrap_ci"],
            "validation_metrics": ["delta", "direction_agreement", "adjusted_p", "effect_size"],
            "rejection_criteria": dict(THRESHOLDS),
            "success_criteria": dict(THRESHOLDS),
            "stopping_rule": "one_research_one_validation_then_freeze_no_retune",
            "author": "TradeMind Research Engine V0.4",
            "status": "REGISTERED",
            "parent_hypothesis_id": parent,
            "family_id": "FAM-PERSISTENCE-0001",
            "experiment_budget": 16,
            "null_hypothesis": "P(next_return>0 | prior_3_same_sign) = P(next_return>0); conditional mean equals unconditional mean.",
            "alternative_hypothesis": "After three same-sign closed bars, next-bar (or +horizon) mean return is displaced from the unconditional mean.",
        }
    )


def hyp_0001_parent():
    return _base("HYP-0001", None, 1, "")


def hyp_0001_a():
    return _base("HYP-0001-A", "HYP-0001", 1, " (horizon=1)")


def hyp_0001_b():
    return _base("HYP-0001-B", "HYP-0001", 5, " (horizon=5)")


def all_hypotheses():
    return [hyp_0001_parent(), hyp_0001_a(), hyp_0001_b()]
