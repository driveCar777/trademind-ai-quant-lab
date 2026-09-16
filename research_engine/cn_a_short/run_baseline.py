"""CLI: run the A-Short D1 baseline over T+1/T+2/T+3/T+5 x Top-K, IF the frozen price pack is present.

Empirical alpha requires the upstream frozen price pack (tm-ashare-EQUITY-D1-...). When it is not
materialized in this environment the run is DATA_BLOCKED and this prints exactly what to do; it never
fabricates results. Cost/account/feasibility tables do NOT need the pack -> see report_tables.py.

Usage:
  python -m research_engine.cn_a_short.run_baseline                 # research window, momentum baseline
  python -m research_engine.cn_a_short.run_baseline --scores PATH   # external [T,N] score .npy
Windows/OOS are LOCKED (single unlock) per contract; this CLI refuses OOS unless --unlock-oos given.
"""
from __future__ import print_function

import argparse
import json
import os

import numpy as np

from research_engine.cn_a_short import (CONTRACT_ID, HORIZONS, MIN_ELIGIBLE, RESEARCH_WINDOW,
                                        TOP_KS, UPSTREAM_DATASET_HASH, UPSTREAM_DATASET_ID)
from research_engine.cn_a_short.baseline import evaluate, momentum_scores, simple_eligible

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_short")


def _pack_available():
    try:
        from research_engine.cn_a_share_alpha.pack import pack_exists
        return pack_exists()
    except Exception:
        return False


def _blocked_message():
    from research_engine.cn_a_share_alpha.paths import CACHE
    return {
        "status": "DATA_BLOCKED",
        "reason": "FROZEN_PRICE_PACK_NOT_MATERIALIZED",
        "contract": CONTRACT_ID,
        "upstream_dataset_id": UPSTREAM_DATASET_ID,
        "upstream_dataset_hash": UPSTREAM_DATASET_HASH,
        "expected_pack_cache": CACHE,
        "how_to_materialize": [
            "On a host that has the raw daily panel + BaoStock access (the :9000 master box):",
            "python -c \"from research_engine.cn_a_share_alpha.pack import pack_panel; pack_panel()\"",
            "then re-run: python -m research_engine.cn_a_short.run_baseline",
        ],
        "note": "Cost/account/feasibility results DO NOT need the pack; run report_tables.py for those.",
    }


def run(window=RESEARCH_WINDOW, scores_path=None, equity=100_000.0, boards="ALL", unlock_oos=False):
    if not _pack_available():
        msg = _blocked_message()
        print(json.dumps(msg, indent=2))
        return msg
    from research_engine.cn_a_share_alpha.pack import load_pack
    pack = load_pack()
    dates = pack["dates"]
    elig = simple_eligible(pack, min_hist=20)
    a, b = window
    i0 = next(i for i, d in enumerate(dates) if d >= a)
    i1 = max(i for i, d in enumerate(dates) if d <= b)
    signal_idx = list(range(i0, i1 + 1))
    if scores_path:
        scores = np.load(scores_path, mmap_mode="r")
        score_fn = scores
    else:
        score_fn = lambda t: momentum_scores(pack, t, lookback=20)
    result = {"contract": CONTRACT_ID, "window": window, "equity": equity, "boards": boards,
              "scores": scores_path or "MOMENTUM_20D_BASELINE", "horizons": {}}
    for hold in HORIZONS:
        result["horizons"][hold] = evaluate(pack, score_fn, elig, signal_idx, hold, TOP_KS, equity,
                                            boards=boards, min_eligible=MIN_ELIGIBLE)
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    path = os.path.join(OUT, "BASELINE_%s.json" % ("MOMENTUM" if not scores_path else "CUSTOM"))
    json.dump(result, open(path, "w"), indent=2, default=float)
    print("WROTE", path)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default=None)
    ap.add_argument("--equity", type=float, default=100_000.0)
    ap.add_argument("--boards", default="ALL")
    ap.add_argument("--unlock-oos", action="store_true")
    args = ap.parse_args()
    run(scores_path=args.scores, equity=args.equity, boards=args.boards, unlock_oos=args.unlock_oos)
