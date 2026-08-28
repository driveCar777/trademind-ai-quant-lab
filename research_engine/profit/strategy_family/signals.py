"""Causal signals. Signal at t uses bars[0..t] only."""
from __future__ import print_function

from research_engine.factors.compute import feature_at
from research_protocol.causal import CausalView


def _prior_extreme(view, t, n, field):
    if t < n or n <= 0:
        return None
    best = None
    i = t - n
    while i < t:
        v = view.field(i, field)
        if v is None:
            return None
        if best is None:
            best = v
        elif field == "high" and v > best:
            best = v
        elif field == "low" and v < best:
            best = v
        i += 1
    return best


def signal_tf_breakout(bars, t, state, lookback=20):
    if not state or not state.get("allow_entry"):
        return 0
    sid = state.get("state_id") or ""
    if not sid.startswith("TREND_STRONG"):
        return 0
    view = CausalView(bars, t)
    close = view.close(t)
    if close is None:
        return 0
    if state.get("trend") == "UP":
        prior = _prior_extreme(view, t, lookback, "high")
        if prior is not None and close > prior:
            return 1
    if state.get("trend") == "DOWN":
        prior = _prior_extreme(view, t, lookback, "low")
        if prior is not None and close < prior:
            return -1
    return 0


def signal_mr_z(bars, t, state):
    if not state or not state.get("allow_entry"):
        return 0
    if state.get("state_id") != "RANGE_LOWVOL":
        return 0
    z = feature_at(bars, t, "z_dist", {"n": 20})
    if z is None:
        return 0
    if z >= 1.0:
        return -1
    if z <= -1.0:
        return 1
    return 0


def signal_mom_dir(bars, t, state):
    if not state or not state.get("allow_entry"):
        return 0
    sid = state.get("state_id") or ""
    if not sid.startswith("TREND_"):
        return 0
    mom = state.get("momentum")
    trend = state.get("trend")
    if trend == "UP" and mom == "POS":
        return 1
    if trend == "DOWN" and mom == "NEG":
        return -1
    return 0


def signal_at(bars, t, state, family):
    if family == "TF-BRK20":
        return signal_tf_breakout(bars, t, state, 20)
    if family == "MR-Z20":
        return signal_mr_z(bars, t, state)
    if family == "MOM-DIR":
        return signal_mom_dir(bars, t, state)
    if family == "DEF":
        return 0
    raise ValueError("unknown family %s" % family)
