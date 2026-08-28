"""Phase 7 decision tree. No optimization. No strategy without a candidate."""
from __future__ import print_function


def decide_program(outcome, family="REGIME_TRANSITION_V0.9"):
    if outcome == "CANDIDATE":
        return {
            "family": family,
            "outcome": outcome,
            "level": 1,
            "next_action": "STRATEGY_MINING",
            "strategy_layer_allowed": True,
            "optimize_forbidden": True,
            "run_residual": False,
        }
    if outcome == "WEAK_EDGE":
        return {
            "family": family,
            "outcome": outcome,
            "level": 0,
            "next_action": "SECOND_MECHANISM_RESIDUAL_V0.91",
            "strategy_layer_allowed": False,
            "optimize_forbidden": True,
            "run_residual": True,
        }
    return {
        "family": family,
        "outcome": outcome or "NO_CANDIDATE",
        "level": 0,
        "next_action": "WRITE_FAILED_THEN_RESIDUAL_V0.91",
        "strategy_layer_allowed": False,
        "optimize_forbidden": True,
        "run_residual": True,
    }


def distance_to_10(current_cagr, target=0.10):
    if current_cagr is None:
        return {
            "current_cagr": None,
            "target": target,
            "gap": None,
            "note": "No certified strategy CAGR. Path leftovers are not 10%.",
        }
    return {
        "current_cagr": current_cagr,
        "target": target,
        "gap": target - float(current_cagr),
        "note": "Not a marketing number. Research leftover only.",
    }
