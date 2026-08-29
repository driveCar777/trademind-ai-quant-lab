"""20-day product-minus-crude return crack. Fixed percentile crosses. Not EIA."""
from __future__ import print_function

from research_engine.energy_rv import CHEAP_PCTL, PCT_LOOKBACK, RET_LOOKBACK, RICH_PCTL


def _ret(bars, i, lookback):
    if i < lookback:
        return None
    a = bars[i - lookback].get("close")
    b = bars[i].get("close")
    if a is None or b is None or a <= 0:
        return None
    return (float(b) / float(a)) - 1.0


def _percentile(xs, p):
    if not xs:
        return None
    ys = sorted(xs)
    if p <= 0:
        return ys[0]
    if p >= 1:
        return ys[-1]
    idx = int(round(p * (len(ys) - 1)))
    return ys[idx]


def tag_book(aligned):
    oil = aligned["OIL"]
    gas = aligned["GASOLINE"]
    heat = aligned["HEATOIL"]
    n = len(oil)
    hist = []
    prev_cheap = None
    prev_rich = None
    book = []
    i = 0
    while i < n:
        r_oil = _ret(oil, i, RET_LOOKBACK)
        r_gas = _ret(gas, i, RET_LOOKBACK)
        r_heat = _ret(heat, i, RET_LOOKBACK)
        crack = None
        if r_oil is not None and r_gas is not None and r_heat is not None:
            crack = 0.5 * (r_gas + r_heat) - r_oil
            hist.append(crack)
        window = hist[-PCT_LOOKBACK:] if len(hist) >= PCT_LOOKBACK else []
        lo = _percentile(window, CHEAP_PCTL) if window else None
        hi = _percentile(window, RICH_PCTL) if window else None
        cheap = bool(crack is not None and lo is not None and crack < lo)
        rich = bool(crack is not None and hi is not None and crack > hi)
        cheap_x = bool(cheap and prev_cheap is False)
        rich_x = bool(rich and prev_rich is False)
        book.append(
            {
                "date": oil[i].get("date"),
                "timestamp_utc": oil[i].get("timestamp_utc"),
                "crack20": crack,
                "is_crack_cheap_cross": cheap_x,
                "is_crack_rich_cross": rich_x,
                "role": None,
            }
        )
        if crack is not None and lo is not None:
            prev_cheap = cheap
            prev_rich = rich
        i += 1
    return book
