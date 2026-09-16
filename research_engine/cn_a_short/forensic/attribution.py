"""Return attribution (APPROX only). Separates benchmark/β from tilt; refuses to fabricate.

With a single momentum signal and NO market-cap / industry / factor-model data in A-Short, size and
selection effects cannot be isolated -> reported UNKNOWN. market_beta uses the EW benchmark exposure;
momentum tilt is approximated by excess-vs-EW and explicitly labeled APPROX. Read-only.
"""
from __future__ import print_function

import numpy as np


def _num(x):
    return x if isinstance(x, (int, float)) and np.isfinite(x) else None


def attribution(evaluate_k):
    """evaluate_k = one Top-K summary dict from baseline.evaluate. Returns approx attribution."""
    ew = _num(evaluate_k.get("mean_gross_ew"))
    topk = _num(evaluate_k.get("mean_gross_topk"))
    excess = _num(evaluate_k.get("mean_excess_vs_ew"))
    t_excess = _num(evaluate_k.get("t_excess"))
    return {
        "method": "APPROX",
        "total_gross_topk": topk,
        "market_beta": ew if ew is not None else "UNKNOWN",           # EW benchmark exposure
        "size_effect": "UNKNOWN",                                     # no market-cap data
        "momentum_effect": {"value": excess, "label": "APPROX",
                            "note": "signal is 20D momentum; excess vs EW attributed to momentum tilt, "
                                    "NOT separated from selection (no factor model)"},
        "selection_effect": "UNKNOWN",                               # cannot separate from momentum
        "excess_vs_ew": excess, "t_excess": t_excess,
        "note": "size/sector/selection require market-cap/industry/factor data absent in A-Short -> UNKNOWN. "
                "If excess vs EW is ~0 (t not significant), return is mostly small-cap/market beta, not alpha.",
    }


def best_worst_trades(trades, n=10):
    """trades = list of dicts with numeric 'net'. Returns best/worst n by net (filled only)."""
    filled = [t for t in (trades or []) if isinstance(t.get("net"), (int, float)) and t.get("entered")]
    filled.sort(key=lambda t: t["net"])
    worst = filled[:n]
    best = list(reversed(filled[-n:])) if filled else []
    return {"best": best, "worst": worst, "n_filled": len(filled)}


__all__ = ["attribution", "best_worst_trades"]
