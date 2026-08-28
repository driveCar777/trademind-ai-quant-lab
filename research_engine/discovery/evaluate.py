"""Evaluate locked candidates. Thresholds freeze on research only."""
from __future__ import print_function

from research_engine.discovery import DISCOVERY_BLOCK, DISCOVERY_BOOT, DISCOVERY_MIN_N, DISCOVERY_PERM, DISCOVERY_SEED
from research_engine.discovery.contract import assert_no_final_oos
from research_engine.factors.compute import feature_series, target_at
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
from research_protocol.windows import window_guard


def percentile(xs, q):
    vals = []
    for x in xs:
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            vals.append(float(x))
    vals.sort()
    if not vals:
        return None
    if q <= 0:
        return vals[0]
    if q >= 1:
        return vals[-1]
    idx = q * (len(vals) - 1)
    lo = int(idx)
    hi = lo + 1
    if hi >= len(vals):
        return vals[lo]
    frac = idx - lo
    return vals[lo] * (1.0 - frac) + vals[hi] * frac


def _cache_key(kind, params):
    items = []
    for key in sorted((params or {}).keys()):
        items.append("%s=%s" % (key, (params or {})[key]))
    return kind + "|" + ",".join(items)


def collect_pairs(bars, features, window, role, target, horizon):
    assert_no_final_oos(role)
    pairs = []
    spreads = []
    t = 0
    while t < len(bars):
        ok, _reason = window_guard(t, t + horizon, window, role)
        if ok:
            feat = features[t] if t < len(features) else None
            tgt = target_at(bars, t, target, horizon)
            if feat is not None and tgt is not None:
                pairs.append((float(feat), float(tgt), t))
                close = bars[t].get("close")
                spr = bars[t].get("spread")
                if close and spr is not None and close != 0:
                    spreads.append(float(spr) / float(close))
        t += 1
    return pairs, spreads


def split_condition(pairs, side, high_cut, low_cut):
    cond = []
    base = []
    for feat, tgt, _t in pairs:
        base.append(tgt)
        if side == "high" and high_cut is not None and feat >= high_cut:
            cond.append(tgt)
        elif side == "low" and low_cut is not None and feat <= low_cut:
            cond.append(tgt)
    return cond, base


def _stats(cond, base, seed, iters_boot, iters_perm, block_length):
    delta = difference_of_means(cond, base)
    effect = effect_size_cohens_d(cond, base)
    boot = bootstrap_delta_ci(cond, base, iterations=iters_boot, seed=seed)
    block = moving_block_bootstrap_delta_ci(cond, base, block_length=block_length, iterations=iters_boot, seed=seed)
    perm = permutation_delta_p(cond, base, iterations=iters_perm, seed=seed)
    hit = proportion(cond, lambda x: x > 0)
    raw_spread = None
    return {
        "sample_size": len(cond),
        "baseline_n": len(base),
        "conditional_mean": mean(cond),
        "baseline_mean": mean(base),
        "delta": delta,
        "effect_size": effect,
        "hit_rate": hit,
        "bootstrap_ci": boot,
        "block_bootstrap_ci": block,
        "permutation_p": None if perm is None else perm.get("p_value"),
        "permutation_statistic": None if perm is None else perm.get("statistic"),
        "economic_magnitude_return": delta,
        "economic_magnitude_bps": None if delta is None else delta * 10000.0,
        "raw_spread_over_close": raw_spread,
    }


def evaluate_candidate(bars, window, candidate, cache, seed=DISCOVERY_SEED, iters_boot=DISCOVERY_BOOT, iters_perm=DISCOVERY_PERM, block_length=DISCOVERY_BLOCK):
    kind = candidate["kind"]
    params = candidate.get("params") or {}
    key = _cache_key(kind, params)
    if key not in cache:
        cache[key] = feature_series(bars, kind, params)
    features = cache[key]
    target = candidate.get("target") or "future_return"
    horizon = int(candidate.get("horizon") or 1)
    side = candidate.get("side") or "high"
    research_pairs, research_spreads = collect_pairs(bars, features, window, "research", target, horizon)
    feats = [p[0] for p in research_pairs]
    high_cut = percentile(feats, 0.67)
    low_cut = percentile(feats, 0.33)
    r_cond, r_base = split_condition(research_pairs, side, high_cut, low_cut)
    research = _stats(r_cond, r_base, seed, iters_boot, iters_perm, block_length)
    research["threshold_high"] = high_cut
    research["threshold_low"] = low_cut
    research["side"] = side
    research["raw_spread_over_close"] = median(research_spreads)
    validation_pairs, validation_spreads = collect_pairs(bars, features, window, "validation", target, horizon)
    v_cond, v_base = split_condition(validation_pairs, side, high_cut, low_cut)
    validation = _stats(v_cond, v_base, seed, iters_boot, iters_perm, block_length)
    validation["threshold_high"] = high_cut
    validation["threshold_low"] = low_cut
    validation["side"] = side
    validation["raw_spread_over_close"] = median(validation_spreads)
    rd = research.get("delta")
    vd = validation.get("delta")
    same_sign = None
    if rd is not None and vd is not None:
        same_sign = (rd == 0 and vd == 0) or (rd > 0 and vd > 0) or (rd < 0 and vd < 0)
    cost = research.get("raw_spread_over_close")
    cost_sensitive = None
    if rd is not None and cost is not None:
        cost_sensitive = abs(rd) < cost
    insufficient = (research.get("sample_size") or 0) < DISCOVERY_MIN_N
    return {
        "candidate_id": candidate["candidate_id"],
        "family_id": candidate.get("family_id"),
        "name": candidate.get("name"),
        "kind": kind,
        "params": params,
        "side": side,
        "target": target,
        "horizon": horizon,
        "volume_type": candidate.get("volume_type"),
        "combo": bool(candidate.get("combo")),
        "research": research,
        "validation": validation,
        "sign_consistency": same_sign,
        "cost_sensitive": cost_sensitive,
        "insufficient_n": insufficient,
        "raw_p": None if insufficient else research.get("permutation_p"),
    }


def evaluate_job(bars, window, candidates, seed=DISCOVERY_SEED, iters_boot=DISCOVERY_BOOT, iters_perm=DISCOVERY_PERM, block_length=DISCOVERY_BLOCK):
    cache = {}
    rows = []
    for cand in candidates:
        rows.append(evaluate_candidate(bars, window, cand, cache, seed, iters_boot, iters_perm, block_length))
    return rows
