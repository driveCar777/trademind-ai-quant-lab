"""Machine catalog for Opportunity V2. Mechanisms, not indicators."""
from __future__ import print_function


def _r(
    rid,
    mechanism_text,
    mechanism,
    economic,
    data,
    scale,
    cost,
    prev,
    novelty,
    status,
    why_not,
    flags=None,
):
    flags = flags or {}
    return {
        "id": rid,
        "mechanism_text": mechanism_text,
        "mechanism": mechanism,
        "economic_reason": economic,
        "data_available": data,
        "time_scale": scale,
        "transaction_cost_survival": cost,
        "previous_failure": prev,
        "novelty": novelty,
        "status": status,
        "why_not_tested": why_not,
        "killed_isomorph": bool(flags.get("killed")),
        "needs_h1": bool(flags.get("h1")),
        "target_hint": flags.get("target") or "GOLD/OIL D1",
    }


def all_opportunities():
    return [
        _r(
            "OPP-IT-ME",
            "Month-end institutional rebalance window on D1",
            5, 5, 5, 4, 4, 2, 5, "UNKNOWN",
            "Queued behind V0.9/V0.91. Backlog mentioned calendar; no contract was written. Not a weekday dummy.",
            {"target": "GOLD and OIL D1"},
        ),
        _r(
            "OPP-IT-QE",
            "Quarter-end window dressing / book flattening",
            4, 4, 5, 2, 4, 2, 4, "UNKNOWN",
            "Same reason as month-end. Fewer events on the frozen D1 packs (~26 quarters).",
            {"target": "OIL D1"},
        ),
        _r(
            "OPP-IT-LON",
            "London cash open inventory adjustment",
            4, 4, 2, 2, 3, 2, 5, "UNKNOWN",
            "Never contracted. Frozen H1 is months. Broker probe meets ~5.03y H1 only as a new dataset_id. Not on-disk yet.",
            {"h1": True, "target": "GOLD H1"},
        ),
        _r(
            "OPP-IT-NY",
            "New York open overlap flow",
            4, 4, 1, 2, 3, 2, 5, "UNKNOWN",
            "Same as London: 5y H1 is acquirable, not frozen. Do not contract yet.",
            {"h1": True, "target": "GOLD H1"},
        ),
        _r(
            "OPP-RV-TERM",
            "Short vs long realized-vol term structure from OHLC",
            4, 4, 5, 4, 3, 1, 4, "UNKNOWN",
            "IV is blocked so this was never opened. ATR *level* was used in V0.5/V0.9; slope of RV was not.",
            {"target": "OIL D1"},
        ),
        _r(
            "OPP-VOVOL",
            "Vol-of-vol of ATR/TR, not enter-HIGH",
            3, 3, 5, 4, 3, 1, 3, "UNKNOWN",
            "Adjacent to V0.9 VOL_SHOCK. Left untested to avoid a fourth RT ID.",
            {"target": "OIL D1"},
        ),
        _r(
            "OPP-VSURP",
            "Tick-volume surprise versus its own baseline",
            3, 3, 5, 3, 3, 1, 4, "UNKNOWN",
            "FD tested tickvol_z as next-return *level* and rejected it. Surprise was not the hypothesis.",
            {"target": "GOLD D1"},
        ),
        _r(
            "OPP-VDIV",
            "Volume-return divergence (activity without a matching return)",
            4, 4, 5, 3, 3, 1, 4, "UNKNOWN",
            "Not in the FD search space as a joint event. tick_volume is still on disk. Do not delete it.",
            {"target": "GOLD D1"},
        ),
        _r(
            "OPP-RISK-LABEL",
            "Same-day GOLD/OIL/FX joint sign as a label for a *new* target",
            3, 3, 5, 3, 2, 1, 2, "UNKNOWN",
            "V0.8 used FX to forecast next GOLD/OIL. A label without a new target is not a family.",
            {"target": "undefined"},
        ),
        _r(
            "OPP-USD",
            "USD proxy to trade GOLD tomorrow",
            2, 2, 5, 4, 2, 0, 1, "FAILED",
            "This is V0.8.",
            {"killed": True, "target": "GOLD D1"},
        ),
        _r(
            "OPP-BASKET",
            "GOLD+OIL basket residual versus one leg",
            3, 3, 5, 4, 3, 0, 2, "FAILED",
            "Too close to V0.91. Treat as isomorph until a third asset exists.",
            {"killed": True, "target": "GOLD/OIL D1"},
        ),
        _r(
            "OPP-IV",
            "IV minus RV",
            5, 5, 0, 1, 4, 2, 5, "BLOCKED",
            "No options tape.",
            {"target": "none"},
        ),
        _r(
            "OPP-CARRY",
            "Rate carry",
            5, 5, 0, 1, 4, 2, 5, "BLOCKED",
            "No rates tape.",
            {"target": "none"},
        ),
        _r(
            "OPP-WEEKDAY",
            "Weekday dummy / weekend gap as the hypothesis",
            2, 2, 5, 3, 3, 1, 1, "FORBIDDEN",
            "User forbids weekday fishing. Low novelty versus month-end.",
            {"target": "GOLD D1"},
        ),
    ]
