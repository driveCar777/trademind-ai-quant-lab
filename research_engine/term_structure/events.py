from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.term_structure import CONTRACT_EVENTS


def fired_at(bar, event, root):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    feat = (bar.get("roots") or {}).get(root) or {}
    if event == "BACKWARDATION":
        return bool(feat.get("backwardation"))
    if event == "STEEPENING":
        steep = feat.get("steepening")
        return steep is not None and steep > 0
    if event == "POSITIVE_ROLL":
        roll = feat.get("roll_yield")
        return roll is not None and roll > 0
    raise ContractMismatch("INVENTED_EVENT")
