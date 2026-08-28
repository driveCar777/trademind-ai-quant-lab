"""Strategy contract fields. V0.5 holding is fixed. No sizing."""
from __future__ import print_function


REQUIRED = (
    "strategy_id",
    "name",
    "state_filter",
    "signal_rule",
    "entry",
    "exit",
    "holding",
    "cost_rule",
    "risk_rule",
    "target",
    "horizon",
    "side",
    "status",
)


def validate_strategy(row):
    for key in REQUIRED:
        if key not in row:
            raise ValueError("missing strategy field %s" % key)
    if row.get("entry") != "NEXT_CLOSED_BAR":
        raise ValueError("V0.5 entry must be NEXT_CLOSED_BAR")
    if row.get("cost_rule") != "RAW_SPREAD_OVER_CLOSE_SCREEN_ONLY":
        raise ValueError("V0.5 cost_rule locked")
    if not row.get("causal"):
        raise ValueError("strategy must be causal")
    return True
