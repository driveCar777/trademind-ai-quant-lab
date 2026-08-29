"""Ag 20-day participation. Thrust/contract crosses. Not rank L3/S3."""
from __future__ import print_function

from research_engine.breadth import CONTRACT, FEATURE_BASKET, LOOKBACK, THRUST


def _ret(bars, i, lookback):
    if i < lookback:
        return None
    a = bars[i - lookback].get("close")
    b = bars[i].get("close")
    if a is None or b is None or a <= 0:
        return None
    return (float(b) / float(a)) - 1.0


def tag_book(aligned, names=None):
    names = list(names or FEATURE_BASKET)
    n = len(aligned["GOLD"])
    prev_thrust = None
    prev_contract = None
    book = []
    i = 0
    while i < n:
        up = 0
        have = 0
        j = 0
        while j < len(names):
            r = _ret(aligned[names[j]], i, LOOKBACK)
            if r is not None:
                have += 1
                if r > 0:
                    up += 1
            j += 1
        breadth = (float(up) / float(have)) if have == len(names) else None
        thrust = bool(breadth is not None and breadth > THRUST)
        contract = bool(breadth is not None and breadth < CONTRACT)
        thrust_x = bool(thrust and prev_thrust is False)
        contract_x = bool(contract and prev_contract is False)
        book.append(
            {
                "date": aligned["GOLD"][i].get("date"),
                "timestamp_utc": aligned["GOLD"][i].get("timestamp_utc"),
                "breadth": breadth,
                "n_up": up,
                "n_have": have,
                "is_breadth_thrust": thrust_x,
                "is_breadth_contract": contract_x,
                "role": None,
            }
        )
        if breadth is not None:
            prev_thrust = thrust
            prev_contract = contract
        i += 1
    return book
