"""Monte Carlo / bootstrap scaffold.

Only for a TRUE Candidate (C0–C13). None exist. Do not fake one.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


def block_bootstrap(rets: List[float], n_paths: int = 500, block: int = 5, seed: int = 25) -> Dict[str, Any]:
    raise RuntimeError("NO_CANDIDATE: Monte Carlo is scaffolding only until C0–C13 pass")


def describe() -> Dict[str, Any]:
    return {
        "available": True,
        "used": False,
        "reason": "NO_CANDIDATE",
        "when": "only after Candidate Gate V2 all pass",
        "methods": ["block_bootstrap", "defensive: do not use to promote a family"],
        "n_paths_default": 500,
        "seed_default": 25,
    }
