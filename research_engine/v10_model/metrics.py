"""Prediction metrics. Not trading metrics."""
from __future__ import print_function

import math

from research_engine.v10_model import V10_SEED


def _clip(p):
    if p is None:
        return 0.5
    if p < 1e-12:
        return 1e-12
    if p > 1.0 - 1e-12:
        return 1.0 - 1e-12
    return float(p)


def logloss(y, p):
    if not y:
        return None
    acc = 0.0
    i = 0
    while i < len(y):
        pr = _clip(p[i])
        yi = int(y[i])
        acc += -(yi * math.log(pr) + (1 - yi) * math.log(1.0 - pr))
        i += 1
    return acc / float(len(y))


def brier(y, p):
    if not y:
        return None
    acc = 0.0
    i = 0
    while i < len(y):
        acc += (float(p[i]) - float(y[i])) ** 2
        i += 1
    return acc / float(len(y))


def hit_rate(y, pred):
    if not y:
        return None
    ok = 0
    i = 0
    while i < len(y):
        if int(pred[i]) == int(y[i]):
            ok += 1
        i += 1
    return ok / float(len(y))


def auc(y, p):
    pairs = list(zip([int(v) for v in y], [float(v) for v in p]))
    pos = [s for lab, s in pairs if lab == 1]
    neg = [s for lab, s in pairs if lab == 0]
    if not pos or not neg:
        return 0.5
    pos = sorted(pos)
    neg = sorted(neg)
    better = 0.0
    ties = 0.0
    i = 0
    while i < len(pos):
        j = 0
        while j < len(neg):
            if pos[i] > neg[j]:
                better += 1.0
            elif pos[i] == neg[j]:
                ties += 1.0
            j += 1
        i += 1
    return (better + 0.5 * ties) / float(len(pos) * len(neg))


def binomial_p(hits, n, p0=0.5):
    if n <= 0:
        return 1.0
    from scipy.stats import binomtest

    return float(binomtest(int(hits), int(n), p0, alternative="two-sided").pvalue)


def permutation_auc_p(y, p, iterations=199, seed=V10_SEED):
    observed = auc(y, p)
    if not y:
        return {"statistic": observed, "p_value": 1.0, "iterations": 0}
    labels = [int(v) for v in y]
    scores = [float(v) for v in p]
    rng_state = seed
    extreme = 0
    it = 0
    while it < iterations:
        rng_state = (1103515245 * rng_state + 12345) % (2 ** 31)
        # Fisher-Yates with LCG
        shuf = list(labels)
        i = len(shuf) - 1
        while i > 0:
            rng_state = (1103515245 * rng_state + 12345) % (2 ** 31)
            j = rng_state % (i + 1)
            tmp = shuf[i]
            shuf[i] = shuf[j]
            shuf[j] = tmp
            i -= 1
        stat = auc(shuf, scores)
        if abs(stat - 0.5) >= abs(observed - 0.5):
            extreme += 1
        it += 1
    return {
        "statistic": observed,
        "p_value": (extreme + 1) / float(iterations + 1),
        "iterations": iterations,
        "seed": seed,
        "method": "permutation_two_sided_auc",
    }


def split_metrics(y, proba, pred):
    hits = 0
    i = 0
    while i < len(y):
        if int(pred[i]) == int(y[i]):
            hits += 1
        i += 1
    return {
        "n": len(y),
        "logloss": logloss(y, proba),
        "brier": brier(y, proba),
        "auc": auc(y, proba),
        "hit_rate": hit_rate(y, pred),
        "hits": hits,
        "binomial_p": binomial_p(hits, len(y)) if y else 1.0,
    }


def predictive_advantage(model_m, naive_m):
    if not model_m or not naive_m:
        return False
    ll_m = model_m.get("logloss")
    ll_0 = naive_m.get("logloss")
    br_m = model_m.get("brier")
    br_0 = naive_m.get("brier")
    au = model_m.get("auc")
    if ll_m is None or ll_0 is None or br_m is None or br_0 is None or au is None:
        return False
    return ll_m < ll_0 and br_m < br_0 and au > 0.5
