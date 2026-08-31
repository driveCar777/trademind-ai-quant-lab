"""Reload the frozen V13 contract. Contract is authority, not RESULTS."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share_alpha.contract import build_contract
from research_engine.cn_a_share_alpha.paths import ALPHA_ROOT
from research_engine.cn_a_share_strategy_v14 import (
    DATASET_HASH,
    DATASET_ID,
    DENIED,
    HOLD_DAYS,
    PARENT_CONTRACT_HASH,
    QUANTILE,
    RESEARCH,
    SEED,
    STRATEGIES,
    VALIDATION,
)


def reload_contract():
    live = build_contract()
    stored = load_json(os.path.join(ALPHA_ROOT, "CONTRACT.json"))
    ok = live["contract_hash"] == PARENT_CONTRACT_HASH == stored.get("contract_hash")
    hyps = dict((h["id"], h) for h in stored.get("hypotheses") or [])
    checks = {
        "hash_match": ok,
        "live_hash": live["contract_hash"],
        "stored_hash": stored.get("contract_hash"),
        "expected_hash": PARENT_CONTRACT_HASH,
        "dataset_id": stored.get("dataset_id") == DATASET_ID,
        "dataset_hash": stored.get("dataset_hash") == DATASET_HASH,
        "hold_days": stored.get("hold_days") == HOLD_DAYS,
        "quantile": float(stored.get("quantile")) == QUANTILE,
        "seed": stored.get("seed") == SEED,
        "research": tuple(stored.get("research") or ()) == RESEARCH,
        "validation": tuple(stored.get("validation") or ()) == VALIDATION,
        "denied": tuple(stored.get("denied_window") or ()) == DENIED,
        "final_oos": stored.get("final_oos") == "DENIED",
        "rebalance": stored.get("rebalance") == "NON_OVERLAPPING_EVERY_HOLD",
        "stats_formation": stored.get("stats_formation") == "DAILY_OVERLAPPING_H_DAY",
        "signal_price": stored.get("signal_price") == "RAW_CLOSE_T",
        "execution_price": stored.get("execution_price") == "RAW_OPEN_T1",
        "candidates": {},
    }
    for spec in STRATEGIES:
        h = hyps.get(spec["candidate"]) or {}
        checks["candidates"][spec["candidate"]] = {
            "family": h.get("family") == spec["family"],
            "lookback": h.get("lookback") == spec["lookback"],
            "sign": h.get("sign") == spec["sign"],
        }
    scalar_ok = all(
        checks[k]
        for k in checks
        if k not in ("hash_match", "live_hash", "stored_hash", "expected_hash", "candidates", "all_ok")
    )
    cand_ok = all(all(v.values()) for v in checks["candidates"].values())
    checks["all_ok"] = ok and scalar_ok and cand_ok
    translation = {
        "id": "STATISTIC_TO_STRATEGY_TRANSLATION",
        "candidate_statistic": stored.get("stats_formation"),
        "strategy_accounting": stored.get("rebalance"),
        "note": (
            "Level 1 used overlapping H-day mean_net_h. "
            "Canonical V14 uses the locked non-overlapping 20-day capital book. "
            "Those numbers are not required to match."
        ),
    }
    return {"contract": stored, "checks": checks, "translation": translation}
