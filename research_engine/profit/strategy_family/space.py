"""Locked V0.6 strategy list. New members require a new version."""
from __future__ import print_function

from research_engine.profit import COMMISSION_BP, PROFIT_ID, PROFIT_SEED, SLIPPAGE_BP, STOP_ATR_MULT
from research_protocol.hashing import canonical_hash


def _row(name, family, holding, risk_frac):
    risk_tag = "%03d" % int(round(risk_frac * 1000))
    return {
        "strategy_id": "PD-V06-%s-H%s-R%s" % (name, holding, risk_tag),
        "name": name,
        "family": family,
        "entry": "NEXT_BAR_OPEN",
        "exit": "FIXED_HOLD_OR_ATR_STOP",
        "holding": holding,
        "cost": {
            "spread": "BROKER_POINTS_RULE",
            "commission_bp_per_side": COMMISSION_BP,
            "slippage_bp_per_side": SLIPPAGE_BP,
        },
        "risk": {
            "risk_frac": risk_frac,
            "stop_atr_mult": STOP_ATR_MULT,
            "leverage_cap": 1.0,
            "skip_high_vol": True,
            "skip_wide_spread": True,
        },
        "status": "REGISTERED",
        "causal": True,
    }


def build_strategies():
    rows = [
        _row("TF-BRK20", "TF-BRK20", 5, 0.005),
        _row("TF-BRK20", "TF-BRK20", 5, 0.01),
        _row("MR-Z20", "MR-Z20", 5, 0.005),
        _row("MR-Z20", "MR-Z20", 5, 0.01),
        _row("MOM-DIR", "MOM-DIR", 8, 0.005),
        _row("MOM-DIR", "MOM-DIR", 8, 0.01),
        {
            "strategy_id": "PD-V06-DEF-SKIP-HIVOL",
            "name": "DEF-SKIP",
            "family": "DEF",
            "entry": "NONE",
            "exit": "NONE",
            "holding": 0,
            "cost": {"spread": "BROKER_POINTS_RULE", "commission_bp_per_side": COMMISSION_BP, "slippage_bp_per_side": SLIPPAGE_BP},
            "risk": {"risk_frac": 0.0, "skip_high_vol": True, "skip_wide_spread": True},
            "status": "REGISTERED",
            "causal": True,
            "note": "Overlay / cash. Not a profit engine by itself.",
        },
    ]
    ids = [r["strategy_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate strategy_id")
    return rows


def build_search_space():
    strategies = build_strategies()
    body = {
        "discovery_id": PROFIT_ID,
        "version": "0.6",
        "seed": PROFIT_SEED,
        "FINAL_OOS_ACCESS": "DENIED",
        "fill": "NEXT_BAR_OPEN",
        "close_fill": "FORBIDDEN",
        "strategy_count": len(strategies),
        "strategies": strategies,
        "note": "Not HYP-0001. Not FD. Not V0.5 next-bar p-value.",
    }
    hashed = dict(body)
    hashed.pop("search_space_hash", None)
    body["search_space_hash"] = canonical_hash(hashed)
    return body
