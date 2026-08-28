from __future__ import print_function

from research_engine.alt_market_structure import CONTRACT_EVENTS
from research_engine.alt_market_structure.gap import tag_gaps
from research_engine.errors import ContractMismatch


def tag_bars(bars):
    return tag_gaps(bars)


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "GAP_REOPEN_H1":
        return bool(bar.get("is_gap_reopen"))
    if event == "GAP_REOPEN_DOWN_H1":
        return bool(bar.get("is_gap_down"))
    raise ContractMismatch("INVENTED_EVENT")
