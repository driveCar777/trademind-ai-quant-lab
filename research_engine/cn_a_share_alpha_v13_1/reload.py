"""Reload the frozen V13 contract. Contract is authority, not RESULTS.json."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import load_json
from research_engine.cn_a_share_alpha.contract import build_contract
from research_engine.cn_a_share_alpha.paths import ALPHA_ROOT
from research_engine.cn_a_share_alpha_v13_1 import (
    CANDIDATES,
    DATASET_HASH,
    DATASET_ID,
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
        "final_oos": stored.get("final_oos") == "DENIED",
        "live_api": stored.get("live_api") is False,
        "denied": tuple(stored.get("denied_window") or ()) == ("2024-03-01", "2026-08-28"),
        "signal_price": stored.get("signal_price") == "RAW_CLOSE_T",
        "execution_price": stored.get("execution_price") == "RAW_OPEN_T1",
        "cost_id": (stored.get("cost_model") or {}).get("id") == "A_SHARE_TRANSACTION_COST_MODEL_V1",
        "candidates": {},
    }
    for spec in CANDIDATES:
        h = hyps.get(spec["id"]) or {}
        checks["candidates"][spec["id"]] = {
            "family": h.get("family") == spec["family"],
            "lookback": h.get("lookback") == spec["lookback"],
            "sign": h.get("sign") == spec["sign"],
        }
    checks["all_ok"] = ok and all(
        checks[k] for k in checks if k not in ("hash_match", "live_hash", "stored_hash", "expected_hash", "candidates", "all_ok")
    ) and all(all(v.values()) for v in checks["candidates"].values())
    return {"contract": stored, "checks": checks}
