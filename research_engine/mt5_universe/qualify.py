"""Coverage label. Does not invent history."""
from __future__ import print_function

from research_engine.mt5_universe import HISTORY_TARGETS


def coverage(timeframe, years):
    need = HISTORY_TARGETS.get(timeframe)
    if years is None:
        return "NOT_AVAILABLE"
    years = float(years)
    if years <= 0:
        return "NOT_AVAILABLE"
    if need is None:
        return "AVAILABLE"
    if years + 0.02 >= need:
        return "AVAILABLE"
    return "SHORTFALL"
