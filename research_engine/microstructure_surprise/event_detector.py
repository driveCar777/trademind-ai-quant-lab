"""Fire only contracted surprise events. Not a raw tick_volume level."""
from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.microstructure_surprise import CONTRACT_EVENTS
from research_engine.microstructure_surprise.surprise import tag_surprise


def tag_bars(bars):
    return tag_surprise(bars)


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "TICKVOL_SAME_HOUR_SURPRISE":
        return bool(bar.get("is_vol_surprise"))
    if event == "TICKVOL_SURPRISE_QUIET_PRICE":
        return bool(bar.get("is_vol_div"))
    raise ContractMismatch("INVENTED_EVENT")


def event_dates(bars, event):
    out = []
    for bar in bars:
        if fired_at(bar, event):
            out.append(bar.get("timestamp_utc") or bar.get("date"))
    return out
