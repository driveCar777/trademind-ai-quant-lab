"""Reload V13 contract. Authority for both statistic and strategy."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share_alpha.contract import build_contract
from research_engine.cn_a_share_alpha.paths import ALPHA_ROOT
from research_engine.cn_a_share_strategy_v14_1 import (
    DATASET_HASH,
    DATASET_ID,
    DENIED,
    HOLD_DAYS,
    PARENT_CONTRACT_HASH,
    QUANTILE,
    RESEARCH,
    SEED,
    VALIDATION,
)


def reload_contract():
    live = build_contract()
    stored = load_json(os.path.join(ALPHA_ROOT, "CONTRACT.json"))
    ok = live["contract_hash"] == PARENT_CONTRACT_HASH == stored.get("contract_hash")
    return {
        "hash_match": ok,
        "contract_hash": live["contract_hash"],
        "dataset_id": stored.get("dataset_id") == DATASET_ID,
        "dataset_hash": stored.get("dataset_hash") == DATASET_HASH,
        "hold_days": stored.get("hold_days") == HOLD_DAYS,
        "quantile": float(stored.get("quantile")) == QUANTILE,
        "seed": stored.get("seed") == SEED,
        "research": tuple(stored.get("research") or ()) == RESEARCH,
        "validation": tuple(stored.get("validation") or ()) == VALIDATION,
        "denied": tuple(stored.get("denied_window") or ()) == DENIED,
        "rebalance": stored.get("rebalance"),
        "stats_formation": stored.get("stats_formation"),
        "signal_price": stored.get("signal_price"),
        "execution_price": stored.get("execution_price"),
        "return_representation": stored.get("return_representation"),
        "candidate_statistic_is": (
            "DAILY_OVERLAPPING_H_DAY: each date t, equal-weight mean of filled "
            "open(t+1)->open(t+1+20) minus one round-trip cost. "
            "Reported CAGR is (1+mean_net_h)^(242/20)-1. That is not a compounded capital path."
        ),
        "canonical_strategy_is": (
            "NON_OVERLAPPING_EVERY_HOLD capital account. One book, rebalance every 20 "
            "trading days, compound (1+period_return). This is the official strategy object."
        ),
        "all_ok": ok
        and stored.get("dataset_id") == DATASET_ID
        and stored.get("hold_days") == HOLD_DAYS
        and stored.get("final_oos") == "DENIED",
        "contract": stored,
    }
