"""GER40 1-day return percentile crosses. Trade next bar. Not same-bar peek."""
from __future__ import print_function

from research_engine.idx_async import DOWN_PCTL, PCT_LOOKBACK, UP_PCTL


def _ret(bars, i):
    if i < 1:
        return None
    a = bars[i - 1].get("close")
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
    ger = aligned["GER40"]
    n = len(ger)
    hist = []
    prev_up = None
    prev_down = None
    book = []
    i = 0
    while i < n:
        r = _ret(ger, i)
        if r is not None:
            hist.append(r)
        window = hist[-PCT_LOOKBACK:] if len(hist) >= PCT_LOOKBACK else []
        hi = _percentile(window, UP_PCTL) if window else None
        lo = _percentile(window, DOWN_PCTL) if window else None
        up = bool(r is not None and hi is not None and r > hi)
        down = bool(r is not None and lo is not None and r < lo)
        up_x = bool(up and prev_up is False)
        down_x = bool(down and prev_down is False)
        book.append(
            {
                "date": ger[i].get("date"),
                "timestamp_utc": ger[i].get("timestamp_utc"),
                "ger_ret": r,
                "is_ger_up_cross": up_x,
                "is_ger_down_cross": down_x,
                "role": None,
            }
        )
        if r is not None and hi is not None:
            prev_up = up
            prev_down = down
        i += 1
    return book
