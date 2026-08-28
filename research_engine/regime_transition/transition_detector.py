"""Delta-state features. Level occupancy is not a signal."""
from __future__ import print_function


def vol_shock(prev, curr):
    if prev is None or curr is None:
        return False
    if prev.get("vol") is None or curr.get("vol") is None:
        return False
    return prev.get("vol") != "HIGH" and curr.get("vol") == "HIGH"


def enter_strong_up(prev, curr):
    if prev is None or curr is None:
        return False
    if prev.get("strength") != "WEAK":
        return False
    if curr.get("strength") != "STRONG":
        return False
    return curr.get("trend") == "UP"


def exit_strong(prev, curr):
    if prev is None or curr is None:
        return False
    return prev.get("strength") == "STRONG" and curr.get("strength") == "WEAK"


def feature_at(prev, curr, feature):
    if feature == "VOL_SHOCK":
        return vol_shock(prev, curr)
    if feature == "ENTER_STRONG_UP":
        return enter_strong_up(prev, curr)
    if feature == "EXIT_STRONG":
        return exit_strong(prev, curr)
    raise ValueError("UNKNOWN_FEATURE:%s" % feature)


def level_still(curr, feature):
    """Diagnostic only. Not a gate. Not a fourth hypothesis."""
    if curr is None:
        return False
    if feature == "VOL_SHOCK":
        return curr.get("vol") == "HIGH"
    if feature == "ENTER_STRONG_UP":
        return curr.get("strength") == "STRONG" and curr.get("trend") == "UP"
    if feature == "EXIT_STRONG":
        return curr.get("strength") == "WEAK"
    return False


def is_wide(state):
    if state is None:
        return True
    return state.get("friction") == "WIDE"
