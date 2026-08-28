from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.regime_interaction import CONTRACT_EVENTS


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "GOLD_RELVOL_CROSSES_CHEAP":
        return bool(bar.get("is_gold_cheap"))
    if event == "OIL_RELVOL_CROSSES_CHEAP":
        return bool(bar.get("is_oil_cheap"))
    if event == "JOINT_VOL_SHOCK":
        return bool(bar.get("is_joint_vol"))
    raise ContractMismatch("INVENTED_EVENT")
