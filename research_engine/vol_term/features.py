"""H1 realized vol vs D1 realized vol. Fixed percentile crosses. Not ATR."""
from __future__ import print_function

from research_engine.vol_term import D1_RV_LOOKBACK, FLAT_PCTL, H1_RV_DAYS, PCT_LOOKBACK, STEEP_PCTL


def _ret(bars, i):
    if i < 1:
        return None
    a = bars[i - 1].get("close")
    b = bars[i].get("close")
    if a is None or b is None or a <= 0:
        return None
    return (float(b) / float(a)) - 1.0


def _std(xs):
    if xs is None or len(xs) < 2:
        return None
    m = sum(xs) / float(len(xs))
    acc = 0.0
    i = 0
    while i < len(xs):
        acc += (xs[i] - m) ** 2
        i += 1
    return (acc / float(len(xs) - 1)) ** 0.5


def _mean(xs):
    if not xs:
        return None
    return sum(xs) / float(len(xs))


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


def daily_h1_rv(h1_bars):
    by_date = {}
    i = 1
    while i < len(h1_bars):
        r = _ret(h1_bars, i)
        d = h1_bars[i].get("date")
        if r is not None and d:
            by_date.setdefault(d, []).append(r)
        i += 1
    out = {}
    for d, xs in by_date.items():
        if len(xs) >= 6:
            out[d] = _std(xs)
    return out


def tag_book(aligned, h1_rv):
    gold = aligned["GOLD"]
    n = len(gold)
    hist = []
    prev_steep = None
    prev_flat = None
    book = []
    i = 0
    while i < n:
        d1_rets = []
        t = i - D1_RV_LOOKBACK + 1
        while t <= i:
            if t >= 1:
                r = _ret(gold, t)
                if r is not None:
                    d1_rets.append(r)
            t += 1
        long_rv = _std(d1_rets) if len(d1_rets) >= 10 else None
        shorts = []
        k = 0
        while k < H1_RV_DAYS and (i - k) >= 0:
            d = gold[i - k].get("date")
            rv = h1_rv.get(d) if d else None
            if rv is not None:
                shorts.append(rv)
            k += 1
        short_rv = _mean(shorts)
        ratio = None
        if short_rv is not None and long_rv is not None and long_rv > 0:
            ratio = short_rv / long_rv
            hist.append(ratio)
        window = hist[-PCT_LOOKBACK:] if len(hist) >= PCT_LOOKBACK else []
        hi = _percentile(window, STEEP_PCTL) if window else None
        lo = _percentile(window, FLAT_PCTL) if window else None
        steep = bool(ratio is not None and hi is not None and ratio > hi)
        flat = bool(ratio is not None and lo is not None and ratio < lo)
        steep_x = bool(steep and prev_steep is False)
        flat_x = bool(flat and prev_flat is False)
        book.append(
            {
                "date": gold[i].get("date"),
                "timestamp_utc": gold[i].get("timestamp_utc"),
                "vol_ratio": ratio,
                "is_vol_steep_cross": steep_x,
                "is_vol_flat_cross": flat_x,
                "role": None,
            }
        )
        if ratio is not None and hi is not None:
            prev_steep = steep
            prev_flat = flat
        i += 1
    return book
