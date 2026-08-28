"""Null / naive controls. Parameters are fixed, never optimized."""
from __future__ import print_function

from research_engine.persistence import collect_samples, simple_returns
from research_engine.statistics import LCG, difference_of_means, permutation_delta_p
from research_engine.holdout import assert_role_allowed
from research_protocol.windows import window_guard


def control_a_random_direction(bars, window, role, horizon, seed, n_cond=None):
    assert_role_allowed(role)
    samples = collect_samples(bars, window, role, 3, horizon)
    base = samples["baseline"]
    if n_cond is None:
        n_cond = max(1, len(base) // 8)
    rng = LCG(seed)
    cond = []
    i = 0
    while i < n_cond and base:
        cond.append(base[rng.randrange(len(base))])
        i += 1
    perm = permutation_delta_p(cond, base, seed=seed)
    return {
        "control": "A_RANDOM_DIRECTION",
        "observed_effect": difference_of_means(cond, base),
        "p_value": None if perm is None else perm["p_value"],
        "permutation": perm,
        "condition_n": len(cond),
        "baseline_n": len(base),
        "seed": seed,
    }


def control_b_no_prediction(bars, window, role, horizon, seed):
    assert_role_allowed(role)
    samples = collect_samples(bars, window, role, 3, horizon)
    return {
        "control": "B_NEVER_TRADE",
        "observed_effect": 0.0,
        "p_value": 1.0,
        "condition_n": 0,
        "baseline_n": len(samples["baseline"]),
        "note": "No prediction; effect defined as zero.",
        "seed": seed,
    }


def control_c_naive_momentum(bars, window, role, horizon, seed, iters_perm):
    """Last closed bar sign predicts next horizon return. streak_length=1, not tuned."""
    assert_role_allowed(role)
    samples = collect_samples(bars, window, role, 1, horizon)
    cond = samples["positive"] + [-x for x in samples["negative"]]
    # signed alignment: +streak uses raw outcome; -streak flips so "same direction" is positive
    aligned = list(samples["positive"])
    for x in samples["negative"]:
        aligned.append(-x)
    perm = permutation_delta_p(aligned, samples["baseline"], iterations=iters_perm, seed=seed)
    return {
        "control": "C_NAIVE_MOMENTUM",
        "parameters": {"streak_length": 1, "prediction_horizon": horizon},
        "observed_effect": difference_of_means(aligned, samples["baseline"]),
        "p_value": None if perm is None else perm["p_value"],
        "permutation": perm,
        "condition_n": len(aligned),
        "baseline_n": len(samples["baseline"]),
        "seed": seed,
    }
