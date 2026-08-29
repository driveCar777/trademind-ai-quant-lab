from __future__ import print_function

from research_engine.corr_shock import CONTRACT_EVENTS
from research_engine.errors import ContractMismatch


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "CORR_BREAK_CROSS":
        return bool(bar.get("is_corr_break_cross"))
    if event == "CORR_SPIKE_CROSS":
        return bool(bar.get("is_corr_spike_cross"))
    raise ContractMismatch("INVENTED_EVENT")
