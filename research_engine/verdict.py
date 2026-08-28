"""Pre-registered verdicts. Thresholds are never chosen after seeing p-values."""
from __future__ import print_function


def ci_excludes_zero(low, high):
    if low is None or high is None:
        return False
    return (low > 0 and high > 0) or (low < 0 and high < 0)


def verdict_arm(compare_row, validation_arm, thresholds):
    min_n = thresholds.get("min_condition_n", 30)
    min_abs_delta = thresholds.get("min_abs_delta", 0.0)
    min_abs_d = thresholds.get("min_abs_effect_size", 0.10)
    max_p = thresholds.get("max_adjusted_p", 0.05)
    require_agree = thresholds.get("require_direction_agreement", True)
    require_ci = thresholds.get("require_ci_excludes_zero", True)

    n = validation_arm.get("condition_n") or 0
    vd = validation_arm.get("delta")
    effect = validation_arm.get("effect_size")
    adj = validation_arm.get("adjusted_p")
    if adj is None:
        adj = validation_arm.get("permutation_p")
    lo = validation_arm.get("block_bootstrap_ci_low")
    hi = validation_arm.get("block_bootstrap_ci_high")
    agree = compare_row.get("direction_agreement")

    if n < min_n or vd is None:
        return "INCONCLUSIVE"
    econ = (abs(vd) >= min_abs_delta) and (effect is None or abs(effect) >= min_abs_d)
    stat = adj is not None and adj <= max_p
    ci_ok = ci_excludes_zero(lo, hi)

    if require_agree and agree is False and econ:
        return "FALSIFIED"
    if (agree is True or not require_agree) and (ci_ok if require_ci else True) and stat and econ:
        return "SUPPORTED"
    if agree is True and (stat or ci_ok or econ):
        return "WEAK_SUPPORT"
    if agree is False and not econ:
        return "INCONCLUSIVE"
    return "INCONCLUSIVE"


def rollup_verdicts(statuses):
    if not statuses:
        return "INCONCLUSIVE"
    if all(s == "FALSIFIED" for s in statuses):
        return "FALSIFIED"
    if "SUPPORTED" in statuses and "FALSIFIED" not in statuses:
        if statuses.count("SUPPORTED") >= max(1, len(statuses) // 4):
            return "SUPPORTED"
        return "WEAK_SUPPORT"
    if "FALSIFIED" in statuses and "SUPPORTED" in statuses:
        return "INCONCLUSIVE"
    if "WEAK_SUPPORT" in statuses:
        return "WEAK_SUPPORT"
    if "FALSIFIED" in statuses:
        return "INCONCLUSIVE"
    return "INCONCLUSIVE"
