from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.carry import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "CARRY_USD_RICH_CROSS":
        return bool(bar.get("is_carry_usd_rich_cross"))
    if event == "CARRY_USD_CHEAP_CROSS":
        return bool(bar.get("is_carry_usd_cheap_cross"))
    raise ContractMismatch("INVENTED_EVENT")
