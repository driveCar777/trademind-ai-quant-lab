"""60-day GOLD/US500 return correlation. Fixed percentile crosses. No search."""
from __future__ import print_function

from research_engine.corr_shock import BREAK_PCTL, CORR_LOOKBACK, PCT_LOOKBACK, SPIKE_PCTL


def _ret(bars, i):
    if i < 1:
        return None
    a = bars[i - 1].get("close")
    b = bars[i].get("close")
    if a is None or b is None or a <= 0:
        return None
    return (float(b) / float(a)) - 1.0


def _pearson(xs, ys):
    n = len(xs)
    if n < 3 or n != len(ys):
        return None
    mx = sum(xs) / float(n)
    my = sum(ys) / float(n)
    num = 0.0
    dx = 0.0
    dy = 0.0
    i = 0
    while i < n:
        a = xs[i] - mx
        b = ys[i] - my
        num += a * b
        dx += a * a
        dy += b * b
        i += 1
    if dx <= 0 or dy <= 0:
        return None
    return num / ((dx * dy) ** 0.5)


def _corr_at(gold, us, i, lookback):
    if i < lookback:
        return None
    xs = []
    ys = []
    t = i - lookback + 1
    while t <= i:
        a = _ret(gold, t)
        b = _ret(us, t)
        if a is None or b is None:
            return None
        xs.append(a)
        ys.append(b)
        t += 1
    return _pearson(xs, ys)


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
    gold = aligned["GOLD"]
    us = aligned["US500"]
    n = len(gold)
    hist = []
    prev_below = None
    prev_above = None
    book = []
    i = 0
    while i < n:
        corr = _corr_at(gold, us, i, CORR_LOOKBACK)
        if corr is not None:
            hist.append(corr)
        window = hist[-PCT_LOOKBACK:] if len(hist) >= PCT_LOOKBACK else []
        lo = _percentile(window, BREAK_PCTL) if window else None
        hi = _percentile(window, SPIKE_PCTL) if window else None
        below = bool(corr is not None and lo is not None and corr < lo)
        above = bool(corr is not None and hi is not None and corr > hi)
        brk = bool(below and prev_below is False)
        spk = bool(above and prev_above is False)
        book.append(
            {
                "date": gold[i].get("date"),
                "timestamp_utc": gold[i].get("timestamp_utc"),
                "corr60": corr,
                "is_corr_break_cross": brk,
                "is_corr_spike_cross": spk,
                "role": None,
            }
        )
        if corr is not None and lo is not None:
            prev_below = below
            prev_above = above
        i += 1
    return book
