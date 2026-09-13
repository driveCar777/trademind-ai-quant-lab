"""SignalContractV2 — shared schema for research backtest and paper executor.

SPEC §30.2. Not a Candidate. Does not send orders.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

SIDES = ("LONG", "SHORT", "FLAT")

REQUIRED = (
    "signal_id", "strategy_id", "timestamp", "symbol", "side",
    "expected_return", "expected_net_return", "probability", "threshold",
    "confidence", "valid_until", "time_stop", "stop_loss", "take_profit",
    "risk_budget", "position_size", "model_version", "feature_version",
    "data_version", "experiment_id", "commit", "contract",
    "data_hash", "code_hash", "result_hash",
)


def new_signal_id() -> str:
    return "sig-" + uuid.uuid4().hex[:16]


def make_signal(
    strategy_id: str,
    timestamp: str,
    symbol: str,
    side: str,
    experiment_id: str,
    contract: str,
    model_version: str,
    feature_version: str,
    data_version: str,
    data_hash: str,
    code_hash: str,
    expected_return: Optional[float] = None,
    expected_net_return: Optional[float] = None,
    probability: Optional[float] = None,
    threshold: Optional[float] = None,
    confidence: Optional[float] = None,
    valid_until: Optional[str] = None,
    time_stop: Optional[str] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    risk_budget: Optional[float] = None,
    position_size: Optional[float] = None,
    commit: Optional[str] = None,
    result_hash: Optional[str] = None,
    signal_id: Optional[str] = None,
) -> Dict[str, Any]:
    if side not in SIDES:
        raise ValueError("side must be LONG|SHORT|FLAT, got %r" % side)
    rec = {
        "signal_id": signal_id or new_signal_id(),
        "strategy_id": strategy_id,
        "timestamp": timestamp,
        "symbol": symbol,
        "side": side,
        "expected_return": expected_return,
        "expected_net_return": expected_net_return,
        "probability": probability,
        "threshold": threshold,
        "confidence": confidence,
        "valid_until": valid_until,
        "time_stop": time_stop,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk_budget": risk_budget,
        "position_size": position_size,
        "model_version": model_version,
        "feature_version": feature_version,
        "data_version": data_version,
        "experiment_id": experiment_id,
        "commit": commit,
        "contract": contract,
        "data_hash": data_hash,
        "code_hash": code_hash,
        "result_hash": result_hash,
        "candidate": False,
        "grok_is_strategy": False,
        "order_send": False,
    }
    errors = validate(rec)
    if errors:
        raise ValueError("SignalContractV2 invalid: " + "; ".join(errors))
    return rec


def validate(rec: Dict[str, Any]) -> List[str]:
    errors = []
    if not isinstance(rec, dict):
        return ["not a dict"]
    for key in REQUIRED:
        if key not in rec:
            errors.append("missing " + key)
    if rec.get("side") not in SIDES:
        errors.append("side must be LONG|SHORT|FLAT")
    if rec.get("confidence") is not None and rec.get("side") is None:
        errors.append("confidence cannot replace side")
    return errors
