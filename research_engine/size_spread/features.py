"""US2000 minus US500 20-day return. Sign crosses. Not participation count."""
from __future__ import print_function

from research_engine.size_spread import LOOKBACK


def _ret(bars, i, lookback):
    if i < lookback:
        return None
    a = bars[i - lookback].get("close")
    b = bars[i].get("close")
    if a is None or b is None or a <= 0:
        return None
    return (float(b) / float(a)) - 1.0


def tag_book(aligned, names=None):
    n = len(aligned["GOLD"])
    prev_pos = None
    book = []
    i = 0
    while i < n:
        small = _ret(aligned["US2000"], i, LOOKBACK)
        large = _ret(aligned["US500"], i, LOOKBACK)
        spread = None
        if small is not None and large is not None:
            spread = small - large
        pos = None if spread is None else spread > 0
        lag_x = bool(pos is False and prev_pos is True)
        lead_x = bool(pos is True and prev_pos is False)
        book.append(
            {
                "date": aligned["GOLD"][i].get("date"),
                "timestamp_utc": aligned["GOLD"][i].get("timestamp_utc"),
                "size_spread": spread,
                "is_size_lag": lag_x,
                "is_size_lead": lead_x,
                "role": None,
            }
        )
        if pos is not None:
            prev_pos = pos
        i += 1
    return book
