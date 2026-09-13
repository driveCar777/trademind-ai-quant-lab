"""H1 hold=24 overlapping-label audit. Book stays non-overlapping."""
from __future__ import annotations

from typing import Any, Dict

import numpy as np


def audit_hold(n_bars: int, hold: int, first_pred: int = 0) -> Dict[str, Any]:
    n_labels = max(0, n_bars - hold - 1 - first_pred)
    shared = max(0, hold - 1)
    overlap_frac = float(shared) / float(hold) if hold else None
    n_independent = int(np.floor(n_labels / float(hold))) if hold else 0
    return {
        "hold": hold,
        "n_bars": n_bars,
        "n_overlapping_labels": n_labels,
        "shared_bars_adjacent": shared,
        "overlap_fraction": overlap_frac,
        "approx_independent_labels": n_independent,
        "purge_gap": hold,
        "embargo": hold + 1,
        "official_book": "non_overlapping",
        "warning": (
            "Training on every t with hold=%d shares %d bars between neighbors. "
            "IC on overlapping y is inflated. Use purge/embargo or non-overlap OOS."
            % (hold, shared)
        ),
        "phase1": "H1 V1 train IC 0.52 vs fold OOS 0.038 is the same pathology.",
    }
