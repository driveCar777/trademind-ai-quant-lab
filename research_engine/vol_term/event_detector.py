from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.vol_term import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "VOL_STEEP_CROSS":
        return bool(bar.get("is_vol_steep_cross"))
    if event == "VOL_FLAT_CROSS":
        return bool(bar.get("is_vol_flat_cross"))
    raise ContractMismatch("INVENTED_EVENT")
