"""Per-day SIGNAL snapshot: rank / score / eligibility / reject_reason. Answers "why buy this stock?".

This REPRODUCES the baseline's selection ordering read-only (same lexsort as `top_k_period`) to record
ranks; it does NOT change any selection or result. Current model = 20D momentum only; `features` is a
dict keyed for future factors but today holds only momentum20. No new feature is introduced.
"""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_ml_v25.top_n_book import board_mask


def _elig_reason(pack, t, j, in_mask):
    if in_mask:
        return "ELIGIBLE"
    if int(pack["listed"][t, j]) != 1:
        return "NOT_LISTED"
    if int(pack["tradestatus"][t, j]) != 1:
        return "SUSPENDED"
    c = float(pack["close"][t, j])
    if not (np.isfinite(c) and c > 0):
        return "NO_CLOSE"
    return "BELOW_MIN_HIST_OR_BOARD"


def signal_snapshot(pack, scores_t, elig_t, t, k, boards="ALL", sample=10):
    """Build one day's SIGNAL snapshot. Mirrors top_k_period ordering (read-only)."""
    symbols = pack["symbols"]
    date = pack["dates"][t]
    if scores_t is None:
        return {"date": date, "n_eligible": int(np.asarray(elig_t).sum()),
                "model": "20D_MOMENTUM_BASELINE", "top_rank": [], "excluded_sample": [],
                "note": "no scores at this day (insufficient lookback)"}
    scores_t = np.asarray(scores_t, dtype=float)
    mask = np.asarray(elig_t) & board_mask(symbols, boards)
    idx = np.where(mask & np.isfinite(scores_t))[0]
    n_eligible = int(mask.sum())
    if idx.size == 0:
        return {"date": date, "n_eligible": n_eligible, "model": "20D_MOMENTUM_BASELINE",
                "top_rank": [], "excluded_sample": [], "note": "no eligible scored names"}
    order = idx[np.lexsort((idx, scores_t[idx]))][::-1]   # same as top_k_period
    picks = [int(j) for j in order[:k]]
    top_rank = []
    for rank, j in enumerate(picks, start=1):
        top_rank.append({
            "symbol": symbols[j], "rank": rank, "score": float(scores_t[j]),
            "features": {"momentum20": float(scores_t[j])},   # baseline score IS 20d momentum
            "eligibility": "ELIGIBLE", "reject_reason": None,
        })
    # a small sample of eligible-but-not-selected (BELOW_TOPK) + a couple ineligible with reasons
    excluded = []
    for j in [int(x) for x in order[k:k + sample]]:
        excluded.append({"symbol": symbols[j], "eligibility": "ELIGIBLE", "reject_reason": "BELOW_TOPK",
                         "score": float(scores_t[j])})
    inelig = np.where(~mask)[0][:sample]
    for j in [int(x) for x in inelig]:
        excluded.append({"symbol": symbols[j], "eligibility": _elig_reason(pack, t, j, False),
                         "reject_reason": "NOT_ELIGIBLE"})
    return {"date": date, "n_eligible": n_eligible, "model": "20D_MOMENTUM_BASELINE",
            "top_rank": top_rank, "excluded_sample": excluded}


__all__ = ["signal_snapshot"]
