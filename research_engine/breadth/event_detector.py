from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.breadth import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "BREADTH_THRUST":
        return bool(bar.get("is_breadth_thrust"))
    if event == "BREADTH_CONTRACT":
        return bool(bar.get("is_breadth_contract"))
    raise ContractMismatch("INVENTED_EVENT")
