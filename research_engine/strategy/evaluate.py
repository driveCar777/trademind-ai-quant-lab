"""Evaluate locked strategies. State VOL cuts freeze on research."""
from __future__ import print_function

from research_engine.factors.compute import feature_at, target_at
from research_engine.regime.state import freeze_vol_cuts, state_at, vol_raw_at
from research_engine.statistics import (
    bootstrap_delta_ci,
    difference_of_means,
    effect_size_cohens_d,
    mean,
    median,
    moving_block_bootstrap_delta_ci,
    permutation_delta_p,
    proportion,
)
from research_engine.strategy import STRATEGY_BLOCK, STRATEGY_BOOT, STRATEGY_MIN_N, STRATEGY_PERM, STRATEGY_SEED
from research_engine.strategy.contract import assert_no_final_oos
from research_protocol.windows import window_guard


def match_filter(parts, filt):
    if not parts or not parts.get("complete"):
        return False
    filt = filt or {}
    for key in ("trend", "strength", "vol", "location", "momentum", "activity", "friction"):
        allowed = filt.get(key)
        if allowed and parts.get(key) not in allowed:
            return False
    blocked = filt.get("friction_not")
    if blocked and parts.get("friction") in blocked:
        return False
    return True


def signal_fire(bars, t, parts, signal):
    signal = signal or {"kind": "always"}
    kind = signal.get("kind") or "always"
    if kind == "always":
        return True, 1
    if kind == "momentum":
        if parts.get("momentum") != signal.get("equals"):
            return False, 0
        return True, 1
    if kind == "location":
        if parts.get("location") != signal.get("equals"):
            return False, 0
        if signal.get("fade"):
            z = feature_at(bars, t, "z_dist", {"n": 20})
            if z is None or z == 0:
                return False, 0
            return True, -1 if z > 0 else 1
        return True, 1
    raise ValueError("unknown signal %s" % kind)


def _stats(cond, base, seed, iters_boot, iters_perm, block_length):
    delta = difference_of_means(cond, base)
    return {
        "sample_size": len(cond),
        "baseline_n": len(base),
        "conditional_mean": mean(cond),
        "baseline_mean": mean(base),
        "delta": delta,
        "effect_size": effect_size_cohens_d(cond, base),
        "hit_rate": proportion(cond, lambda x: x > 0),
        "bootstrap_ci": bootstrap_delta_ci(cond, base, iterations=iters_boot, seed=seed),
        "block_bootstrap_ci": moving_block_bootstrap_delta_ci(cond, base, block_length=block_length, iterations=iters_boot, seed=seed),
        "permutation_p": None if not cond or not base else (permutation_delta_p(cond, base, iterations=iters_perm, seed=seed) or {}).get("p_value"),
        "economic_magnitude_return": delta,
        "economic_magnitude_bps": None if delta is None else delta * 10000.0,
    }


def collect_role(bars, window, role, states, strategy, seed, iters_boot, iters_perm, block_length):
    assert_no_final_oos(role)
    horizon = int(strategy.get("horizon") or 1)
    side = int(strategy.get("side") or 1)
    cond = []
    base = []
    spreads = []
    t = 0
    while t < len(bars):
        ok, _reason = window_guard(t, t + horizon, window, role)
        if ok:
            tgt = target_at(bars, t, strategy.get("target") or "future_return", horizon)
            parts = states[t] if t < len(states) else None
            if tgt is not None:
                base.append(tgt)
                close = bars[t].get("close")
                spr = bars[t].get("spread")
                if close and spr is not None and close != 0:
                    spreads.append(float(spr) / float(close))
                if match_filter(parts, strategy.get("state_filter")):
                    fired, fade_side = signal_fire(bars, t, parts, strategy.get("signal_rule"))
                    if fired:
                        signed = side * fade_side * tgt
                        if strategy.get("risk_rule") == "SKIP_IF_FRICTION_WIDE" and parts.get("friction") == "WIDE":
                            pass
                        else:
                            cond.append(signed)
        t += 1
    out = _stats(cond, base, seed, iters_boot, iters_perm, block_length)
    out["occupancy"] = len(cond)
    out["raw_spread_over_close"] = median(spreads)
    return out


def build_state_series(bars, window):
    raw = []
    t = 0
    while t < len(bars):
        ok, _reason = window_guard(t, t + 1, window, "research")
        if ok:
            raw.append(vol_raw_at(bars, t))
        t += 1
    cuts = freeze_vol_cuts(raw)
    states = []
    t = 0
    while t < len(bars):
        states.append(state_at(bars, t, cuts))
        t += 1
    return states, cuts


def evaluate_strategy(bars, window, strategy, states, seed=STRATEGY_SEED, iters_boot=STRATEGY_BOOT, iters_perm=STRATEGY_PERM, block_length=STRATEGY_BLOCK):
    research = collect_role(bars, window, "research", states, strategy, seed, iters_boot, iters_perm, block_length)
    validation = collect_role(bars, window, "validation", states, strategy, seed, iters_boot, iters_perm, block_length)
    rd = research.get("delta")
    vd = validation.get("delta")
    same_sign = None
    if rd is not None and vd is not None:
        same_sign = (rd == 0 and vd == 0) or (rd > 0 and vd > 0) or (rd < 0 and vd < 0)
    cost = research.get("raw_spread_over_close")
    cost_sensitive = None
    if rd is not None and cost is not None:
        cost_sensitive = abs(rd) < cost
    insufficient = (research.get("sample_size") or 0) < STRATEGY_MIN_N
    return {
        "candidate_id": strategy["strategy_id"],
        "strategy_id": strategy["strategy_id"],
        "name": strategy.get("name"),
        "family_id": strategy.get("family_id"),
        "state_filter": strategy.get("state_filter"),
        "signal_rule": strategy.get("signal_rule"),
        "horizon": strategy.get("horizon"),
        "side": strategy.get("side"),
        "research": research,
        "validation": validation,
        "sign_consistency": same_sign,
        "cost_sensitive": cost_sensitive,
        "insufficient_n": insufficient,
        "raw_p": None if insufficient else research.get("permutation_p"),
    }


def evaluate_job(bars, window, strategies, seed=STRATEGY_SEED, iters_boot=STRATEGY_BOOT, iters_perm=STRATEGY_PERM, block_length=STRATEGY_BLOCK):
    states, cuts = build_state_series(bars, window)
    rows = []
    for strat in strategies:
        rows.append(evaluate_strategy(bars, window, strat, states, seed, iters_boot, iters_perm, block_length))
    occupancy = {}
    for parts in states:
        if parts.get("complete"):
            key = "%s|%s|%s" % (parts.get("trend"), parts.get("strength"), parts.get("vol"))
            occupancy[key] = occupancy.get(key, 0) + 1
    return rows, cuts, occupancy
