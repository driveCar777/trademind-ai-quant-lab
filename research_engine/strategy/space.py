"""Locked V0.5 strategy sketches. Changing this is a new version."""
from __future__ import print_function

from research_engine.strategy import STRATEGY_BOOT, STRATEGY_FDR_Q, STRATEGY_ID, STRATEGY_PERM, STRATEGY_SEED
from research_engine.strategy.schema import validate_strategy
from research_protocol.hashing import canonical_hash


def _s(name, filt, signal, side=1, horizon=1, risk="SKIP_IF_FRICTION_WIDE"):
    row = {
        "strategy_id": "SD-V05-%s-H%s" % (name, horizon),
        "name": name,
        "family_id": "FAM-SD-STATE-0001",
        "state_filter": filt,
        "signal_rule": signal,
        "entry": "NEXT_CLOSED_BAR",
        "exit": "FIXED_HORIZON",
        "holding": horizon,
        "cost_rule": "RAW_SPREAD_OVER_CLOSE_SCREEN_ONLY",
        "risk_rule": risk,
        "target": "future_return",
        "horizon": horizon,
        "side": side,
        "status": "REGISTERED",
        "causal": True,
        "intended_book": "UNSPECIFIED",
        "note": "Sketch. Not a profitable strategy. Not 10% annualized.",
    }
    validate_strategy(row)
    return row


def build_strategies():
    always = {"kind": "always"}
    mom_pos = {"kind": "momentum", "equals": "POS"}
    mom_neg = {"kind": "momentum", "equals": "NEG"}
    fade_ext = {"kind": "location", "equals": "EXTENDED", "fade": True}
    rows = [
        _s("LONG_IN_UP", {"trend": ["UP"]}, always, 1),
        _s("SHORT_IN_DOWN", {"trend": ["DOWN"]}, always, -1),
        _s("MOM_POS_IN_UP_STRONG", {"trend": ["UP"], "strength": ["STRONG"]}, mom_pos, 1),
        _s("MOM_NEG_IN_DOWN_STRONG", {"trend": ["DOWN"], "strength": ["STRONG"]}, mom_neg, -1),
        _s("MOM_POS_IN_UP", {"trend": ["UP"]}, mom_pos, 1),
        _s("MOM_POS_IN_UP_H3", {"trend": ["UP"]}, mom_pos, 1, 3),
        _s("MOM_POS_UP_MIDVOL", {"trend": ["UP"], "vol": ["MID"]}, mom_pos, 1),
        _s("MOM_POS_UP_HIACT", {"trend": ["UP"], "activity": ["HIGH"]}, mom_pos, 1),
        _s("MOM_POS_TIGHT", {"friction": ["TIGHT"]}, mom_pos, 1),
        _s("FADE_EXT_FLAT", {"trend": ["FLAT"], "location": ["EXTENDED"]}, fade_ext, 1),
        _s("FADE_EXT_FLAT_LOWVOL", {"trend": ["FLAT"], "vol": ["LOW"], "location": ["EXTENDED"]}, fade_ext, 1),
        _s("FADE_EXT_FLAT_HIVOL", {"trend": ["FLAT"], "vol": ["HIGH"], "location": ["EXTENDED"]}, fade_ext, 1),
        _s("FADE_EXT_WEAK", {"strength": ["WEAK"], "location": ["EXTENDED"]}, fade_ext, 1),
        _s("LONG_UP_TIGHT", {"trend": ["UP"], "friction": ["TIGHT"]}, always, 1),
        _s("SKIP_WIDE_ONLY", {"friction": ["WIDE"]}, always, 1, 1, "MEASURE_WIDE_AS_TRADE"),
    ]
    seen = {}
    out = []
    for row in rows:
        if row["strategy_id"] in seen:
            raise ValueError("duplicate %s" % row["strategy_id"])
        seen[row["strategy_id"]] = True
        out.append(row)
    return out


def build_search_space():
    strategies = build_strategies()
    body = {
        "discovery_id": STRATEGY_ID,
        "version": "0.5",
        "seed": STRATEGY_SEED,
        "bootstrap_iterations": STRATEGY_BOOT,
        "permutation_iterations": STRATEGY_PERM,
        "fdr_q": STRATEGY_FDR_Q,
        "cost_model": "RAW_SPREAD_OVER_CLOSE_SCREEN_ONLY",
        "execution_model": "NEXT_CLOSED_BAR_FIXED_HOLD_NOT_TRADE",
        "FINAL_OOS_ACCESS": "DENIED",
        "strategy_count": len(strategies),
        "strategies": strategies,
        "note": "Foundation sketches. Not HYP-0001. Not FD V0.1 retune.",
    }
    hashed = dict(body)
    hashed.pop("search_space_hash", None)
    body["search_space_hash"] = canonical_hash(hashed)
    return body
