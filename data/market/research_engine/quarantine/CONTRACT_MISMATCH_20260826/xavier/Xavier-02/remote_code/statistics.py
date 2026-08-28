"""Deterministic stdlib statistics. No numpy/scipy."""
from __future__ import print_function

import math

from research_engine import BLOCK_LENGTH, BOOTSTRAP_ITERS, FDR_Q, PERMUTATION_ITERS, SEED


class LCG(object):
    def __init__(self, seed):
        self.state = int(seed) & 0xFFFFFFFF

    def next_u32(self):
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return self.state

    def randrange(self, n):
        if n <= 0:
            raise ValueError("n must be positive")
        return self.next_u32() % n


def _finite(xs):
    out = []
    for x in xs:
        if isinstance(x, (int, float)) and not isinstance(x, bool) and not math.isnan(x) and not math.isinf(x):
            out.append(float(x))
    return out


def sample_count(xs):
    return len(_finite(xs))


def mean(xs):
    vals = _finite(xs)
    if not vals:
        return None
    return sum(vals) / float(len(vals))


def median(xs):
    vals = sorted(_finite(xs))
    if not vals:
        return None
    n = len(vals)
    mid = n // 2
    if n % 2:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / 2.0


def variance(xs, ddof=1):
    vals = _finite(xs)
    n = len(vals)
    if n <= ddof:
        return None
    m = mean(vals)
    acc = 0.0
    for x in vals:
        acc += (x - m) ** 2
    return acc / float(n - ddof)


def stdev(xs, ddof=1):
    v = variance(xs, ddof=ddof)
    if v is None:
        return None
    return math.sqrt(v)


def standard_error(xs):
    vals = _finite(xs)
    s = stdev(vals)
    if s is None or not vals:
        return None
    return s / math.sqrt(len(vals))


def difference_of_means(a, b):
    ma = mean(a)
    mb = mean(b)
    if ma is None or mb is None:
        return None
    return ma - mb


def proportion(xs, pred):
    vals = _finite(xs)
    if not vals:
        return None
    hits = 0
    for x in vals:
        if pred(x):
            hits += 1
    return hits / float(len(vals))


def difference_in_proportions(a, b, pred=None):
    if pred is None:
        pred = lambda x: x > 0
    pa = proportion(a, pred)
    pb = proportion(b, pred)
    if pa is None or pb is None:
        return None
    return pa - pb


def effect_size_cohens_d(cond, base):
    a = _finite(cond)
    b = _finite(base)
    if len(a) < 2 or len(b) < 2:
        return None
    va = variance(a)
    vb = variance(b)
    if va is None or vb is None:
        return None
    pooled = math.sqrt(((len(a) - 1) * va + (len(b) - 1) * vb) / float(len(a) + len(b) - 2))
    if pooled == 0:
        return 0.0
    return (mean(a) - mean(b)) / pooled


def bootstrap_mean_ci(xs, iterations=BOOTSTRAP_ITERS, seed=SEED, alpha=0.05):
    vals = _finite(xs)
    n = len(vals)
    if n == 0:
        return None
    rng = LCG(seed)
    means = []
    i = 0
    while i < iterations:
        acc = 0.0
        j = 0
        while j < n:
            acc += vals[rng.randrange(n)]
            j += 1
        means.append(acc / float(n))
        i += 1
    means.sort()
    lo_i = int(alpha / 2.0 * iterations)
    hi_i = int((1.0 - alpha / 2.0) * iterations) - 1
    if hi_i < 0:
        hi_i = 0
    if hi_i >= iterations:
        hi_i = iterations - 1
    return {"low": means[lo_i], "high": means[hi_i], "iterations": iterations, "seed": seed, "method": "iid_bootstrap"}


def bootstrap_delta_ci(cond, base, iterations=BOOTSTRAP_ITERS, seed=SEED, alpha=0.05):
    a = _finite(cond)
    b = _finite(base)
    if not a or not b:
        return None
    rng = LCG(seed)
    na = len(a)
    nb = len(b)
    deltas = []
    i = 0
    while i < iterations:
        sa = 0.0
        sb = 0.0
        j = 0
        while j < na:
            sa += a[rng.randrange(na)]
            j += 1
        j = 0
        while j < nb:
            sb += b[rng.randrange(nb)]
            j += 1
        deltas.append(sa / float(na) - sb / float(nb))
        i += 1
    deltas.sort()
    lo_i = int(alpha / 2.0 * iterations)
    hi_i = int((1.0 - alpha / 2.0) * iterations) - 1
    if hi_i < 0:
        hi_i = 0
    if hi_i >= iterations:
        hi_i = iterations - 1
    return {"low": deltas[lo_i], "high": deltas[hi_i], "iterations": iterations, "seed": seed, "method": "iid_bootstrap_delta"}


def moving_block_bootstrap_mean_ci(xs, block_length=BLOCK_LENGTH, iterations=BOOTSTRAP_ITERS, seed=SEED, alpha=0.05):
    vals = _finite(xs)
    n = len(vals)
    if n == 0:
        return None
    L = block_length if block_length > 0 else 1
    if L > n:
        L = n
    n_blocks = int(math.ceil(n / float(L)))
    max_start = n - L
    if max_start < 0:
        max_start = 0
    rng = LCG(seed)
    means = []
    i = 0
    while i < iterations:
        acc = 0.0
        count = 0
        b = 0
        while b < n_blocks and count < n:
            start = rng.randrange(max_start + 1)
            k = 0
            while k < L and count < n:
                acc += vals[start + k]
                count += 1
                k += 1
            b += 1
        means.append(acc / float(count) if count else 0.0)
        i += 1
    means.sort()
    lo_i = int(alpha / 2.0 * iterations)
    hi_i = int((1.0 - alpha / 2.0) * iterations) - 1
    if hi_i < 0:
        hi_i = 0
    if hi_i >= iterations:
        hi_i = iterations - 1
    return {
        "low": means[lo_i],
        "high": means[hi_i],
        "iterations": iterations,
        "seed": seed,
        "block_length": L,
        "method": "moving_block_bootstrap",
    }


def moving_block_bootstrap_delta_ci(cond, base, block_length=BLOCK_LENGTH, iterations=BOOTSTRAP_ITERS, seed=SEED, alpha=0.05):
    a = _finite(cond)
    b = _finite(base)
    if not a or not b:
        return None
    ca = moving_block_bootstrap_mean_ci(a, block_length, iterations, seed, alpha)
    cb = moving_block_bootstrap_mean_ci(b, block_length, iterations, seed + 1, alpha)
    if ca is None or cb is None:
        return None
    return {
        "low": ca["low"] - cb["high"],
        "high": ca["high"] - cb["low"],
        "iterations": iterations,
        "seed": seed,
        "block_length": block_length,
        "method": "moving_block_bootstrap_delta_conservative",
    }


def permutation_delta_p(cond, base, iterations=PERMUTATION_ITERS, seed=SEED):
    a = _finite(cond)
    b = _finite(base)
    if not a or not b:
        return None
    observed = mean(a) - mean(b)
    pool = a + b
    n_a = len(a)
    n_pool = len(pool)
    rng = LCG(seed)
    extreme = 0
    i = 0
    while i < iterations:
        # Fisher-Yates partial: shuffle then split
        k = n_pool - 1
        while k > 0:
            j = rng.randrange(k + 1)
            tmp = pool[k]
            pool[k] = pool[j]
            pool[j] = tmp
            k -= 1
        sa = 0.0
        j = 0
        while j < n_a:
            sa += pool[j]
            j += 1
        sb = 0.0
        while j < n_pool:
            sb += pool[j]
            j += 1
        delta = sa / float(n_a) - sb / float(n_pool - n_a)
        if abs(delta) >= abs(observed):
            extreme += 1
        i += 1
    p = (extreme + 1) / float(iterations + 1)
    return {
        "statistic": observed,
        "p_value": p,
        "iterations": iterations,
        "seed": seed,
        "method": "permutation_two_sided",
    }


def benjamini_hochberg(p_values, q=FDR_Q):
    items = []
    i = 0
    while i < len(p_values):
        p = p_values[i]
        if p is not None:
            items.append((float(p), i))
        i += 1
    items.sort(key=lambda x: x[0])
    m = len(items)
    adjusted = [None] * len(p_values)
    if m == 0:
        return {"q": q, "discoveries": [], "adjusted_p": adjusted, "m": 0}
    running = 1.0
    k = m - 1
    while k >= 0:
        p, idx = items[k]
        adj = min(1.0, p * m / float(k + 1), running)
        running = adj
        adjusted[idx] = adj
        k -= 1
    cutoff = 0
    k = 0
    while k < m:
        p, idx = items[k]
        if p <= (k + 1) / float(m) * q:
            cutoff = k + 1
        k += 1
    discoveries = [items[j][1] for j in range(cutoff)]
    return {"q": q, "discoveries": discoveries, "adjusted_p": adjusted, "m": m}


def summarize(xs):
    vals = _finite(xs)
    return {
        "n": len(vals),
        "mean": mean(vals),
        "median": median(vals),
        "variance": variance(vals),
        "std": stdev(vals),
        "se": standard_error(vals),
    }
