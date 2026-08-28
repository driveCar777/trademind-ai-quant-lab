"""Null controls. A trustworthy pipeline must not mint many FDR hits on noise."""
from __future__ import print_function

from research_engine.discovery import DISCOVERY_BLOCK, DISCOVERY_BOOT, DISCOVERY_PERM, DISCOVERY_SEED
from research_engine.discovery.evaluate import _stats, collect_pairs, percentile, split_condition
from research_engine.factors.compute import feature_series
from research_engine.statistics import LCG, benjamini_hochberg


def _shuffle(xs, seed):
    out = list(xs)
    rng = LCG(seed)
    k = len(out) - 1
    while k > 0:
        j = rng.randrange(k + 1)
        tmp = out[k]
        out[k] = out[j]
        out[j] = tmp
        k -= 1
    return out


def _pairs_from_features(bars, features, window, target, horizon, role="research"):
    return collect_pairs(bars, features, window, role, target, horizon)[0]


def evaluate_shuffled_pairs(pairs, side, seed, iters_boot, iters_perm, block_length, shuffle_what):
    feats = [p[0] for p in pairs]
    tgts = [p[1] for p in pairs]
    idx = [p[2] for p in pairs]
    if shuffle_what == "target":
        tgts = _shuffle(tgts, seed)
    elif shuffle_what == "signal":
        feats = _shuffle(feats, seed)
    else:
        raise ValueError(shuffle_what)
    new_pairs = []
    i = 0
    while i < len(feats):
        new_pairs.append((feats[i], tgts[i], idx[i]))
        i += 1
    high_cut = percentile(feats, 0.67)
    low_cut = percentile(feats, 0.33)
    cond, base = split_condition(new_pairs, side, high_cut, low_cut)
    return _stats(cond, base, seed, iters_boot, iters_perm, block_length)


def null_controls_for_dataset(bars, window, template_candidate, seed=DISCOVERY_SEED, iters_boot=50, iters_perm=50, block_length=DISCOVERY_BLOCK):
    """Three diagnostics. Not part of the discovery FDR family."""
    kind = template_candidate["kind"]
    params = template_candidate.get("params") or {}
    features = feature_series(bars, kind, params)
    target = template_candidate.get("target") or "future_return"
    horizon = int(template_candidate.get("horizon") or 1)
    side = template_candidate.get("side") or "high"
    pairs = _pairs_from_features(bars, features, window, target, horizon, "research")
    n1 = evaluate_shuffled_pairs(pairs, side, seed, iters_boot, iters_perm, block_length, "target")
    n2 = evaluate_shuffled_pairs(pairs, side, seed + 1, iters_boot, iters_perm, block_length, "signal")
    rand_features = feature_series(bars, "random_null", {"seed": seed})
    rand_pairs = _pairs_from_features(bars, rand_features, window, target, horizon, "research")
    high_cut = percentile([p[0] for p in rand_pairs], 0.67)
    low_cut = percentile([p[0] for p in rand_pairs], 0.33)
    cond, base = split_condition(rand_pairs, "high", high_cut, low_cut)
    n3 = _stats(cond, base, seed + 2, iters_boot, iters_perm, block_length)
    return {
        "null_permute_target": n1,
        "null_shuffle_signal": n2,
        "null_random_factor": n3,
    }


def null_discovery_rate(p_values, q=0.05):
    out = benjamini_hochberg(p_values, q=q)
    return {
        "m": out["m"],
        "discoveries": len(out["discoveries"]),
        "q": q,
    }
