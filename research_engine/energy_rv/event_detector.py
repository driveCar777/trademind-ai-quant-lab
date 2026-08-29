from __future__ import print_function

from research_engine.energy_rv import CONTRACT_EVENTS
from research_engine.errors import ContractMismatch


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "CRACK_CHEAP_CROSS":
        return bool(bar.get("is_crack_cheap_cross"))
    if event == "CRACK_RICH_CROSS":
        return bool(bar.get("is_crack_rich_cross"))
    raise ContractMismatch("INVENTED_EVENT")
