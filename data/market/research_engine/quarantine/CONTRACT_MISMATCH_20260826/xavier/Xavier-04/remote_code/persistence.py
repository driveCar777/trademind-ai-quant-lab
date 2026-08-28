"""HYP-0001 directional persistence. Predictive, not a trading strategy."""
from __future__ import print_function

from research_engine.holdout import assert_role_allowed
from research_engine.statistics import (
    bootstrap_delta_ci,
    difference_in_proportions,
    difference_of_means,
    effect_size_cohens_d,
    mean,
    moving_block_bootstrap_delta_ci,
    permutation_delta_p,
    proportion,
    summarize,
)
from research_protocol.windows import window_guard


def simple_returns(bars):
    out = [None]
    i = 1
    while i < len(bars):
        prev = bars[i - 1]["close"]
        cur = bars[i]["close"]
        if prev is None or cur is None or prev == 0:
            out.append(None)
        else:
            out.append(cur / float(prev) - 1.0)
        i += 1
    return out


def sign_of(value):
    if value is None:
        return 0
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def collect_samples(bars, window, role, streak_length, horizon):
    assert_role_allowed(role)
    rets = simple_returns(bars)
    cond_pos = []
    cond_neg = []
    baseline = []
    t = 0
    while t < len(bars):
        label_index = t + horizon
        ok, _reason = window_guard(t, label_index, window, role)
        if not ok:
            t += 1
            continue
        if label_index >= len(rets) or rets[label_index] is None:
            t += 1
            continue
        signs = []
        k = 0
        valid = True
        while k < streak_length:
            idx = t - streak_length + 1 + k
            if idx < 1 or rets[idx] is None:
                valid = False
                break
            signs.append(sign_of(rets[idx]))
            k += 1
        if not valid:
            t += 1
            continue
        outcome = rets[label_index]
        baseline.append(outcome)
        if all(s == 1 for s in signs):
            cond_pos.append(outcome)
        elif all(s == -1 for s in signs):
            cond_neg.append(outcome)
        t += 1
    return {"positive": cond_pos, "negative": cond_neg, "baseline": baseline}


def _arm(name, cond, baseline, seed, iters_boot, iters_perm, block_length):
    delta = difference_of_means(cond, baseline)
    boot = bootstrap_delta_ci(cond, baseline, iterations=iters_boot, seed=seed)
    block = moving_block_bootstrap_delta_ci(cond, baseline, block_length=block_length, iterations=iters_boot, seed=seed)
    perm = permutation_delta_p(cond, baseline, iterations=iters_perm, seed=seed)
    return {
        "arm": name,
        "condition_n": len(cond),
        "baseline_n": len(baseline),
        "conditional_mean": mean(cond),
        "baseline_mean": mean(baseline),
        "delta": delta,
        "prop_positive_cond": proportion(cond, lambda x: x > 0),
        "prop_positive_base": proportion(baseline, lambda x: x > 0),
        "prop_delta": difference_in_proportions(cond, baseline),
        "effect_size": effect_size_cohens_d(cond, baseline),
        "bootstrap_ci_low": None if boot is None else boot["low"],
        "bootstrap_ci_high": None if boot is None else boot["high"],
        "block_bootstrap_ci_low": None if block is None else block["low"],
        "block_bootstrap_ci_high": None if block is None else block["high"],
        "permutation_p": None if perm is None else perm["p_value"],
        "permutation_statistic": None if perm is None else perm["statistic"],
        "bootstrap": boot,
        "block_bootstrap": block,
        "permutation": perm,
        "condition_summary": summarize(cond),
        "baseline_summary": summarize(baseline),
    }


def _zeros(n):
    return [0.0] * n


def analyze_role(bars, window, role, streak_length, horizon, seed, iters_boot, iters_perm, block_length):
    samples = collect_samples(bars, window, role, streak_length, horizon)
    signed = list(samples["positive"])
    for value in samples["negative"]:
        signed.append(-value)
    zero = _zeros(len(signed)) if signed else [0.0]
    continuation = _arm("continuation_signed", signed, zero, seed + 31, iters_boot, iters_perm, block_length)
    continuation["continuation_mean"] = mean(signed)
    return {
        "role": role,
        "positive": _arm("positive_streak", samples["positive"], samples["baseline"], seed, iters_boot, iters_perm, block_length),
        "negative": _arm("negative_streak", samples["negative"], samples["baseline"], seed + 17, iters_boot, iters_perm, block_length),
        "continuation": continuation,
    }


def compare_roles(research, validation):
    out = {}
    for arm in ("positive", "negative"):
        r = research[arm]
        v = validation[arm]
        rd = r.get("delta")
        vd = v.get("delta")
        agree = None
        if rd is not None and vd is not None:
            agree = (rd == 0 and vd == 0) or (rd > 0 and vd > 0) or (rd < 0 and vd < 0)
        mag = None
        if rd not in (None, 0) and vd is not None:
            mag = vd / float(rd)
        out[arm] = {
            "research_delta": rd,
            "validation_delta": vd,
            "direction_agreement": agree,
            "magnitude_ratio": mag,
        }
    return out
