"""20-day return ranks on an aligned FX book. No lookback search."""
from __future__ import print_function

from research_engine.xs_rev import DISP_LOOKBACK, K_LEG, LOOKBACK, REBALANCE_EVERY


def _ret(bars, i, lookback):
    if i < lookback:
        return None
    a = bars[i - lookback].get("close")
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


def _median(xs):
    if not xs:
        return None
    ys = sorted(xs)
    n = len(ys)
    mid = n // 2
    if n % 2:
        return ys[mid]
    return 0.5 * (ys[mid - 1] + ys[mid])


def tag_book(aligned, names):
    n = len(aligned[names[0]])
    hist_std = []
    book = []
    i = 0
    while i < n:
        rets = {}
        j = 0
        while j < len(names):
            name = names[j]
            r = _ret(aligned[name], i, LOOKBACK)
            if r is not None:
                rets[name] = r
            j += 1
        ranked = sorted(rets.items(), key=lambda kv: kv[1])
        laggards = [kv[0] for kv in ranked[:K_LEG]] if len(ranked) >= K_LEG * 2 else []
        leaders = [kv[0] for kv in ranked[-K_LEG:]] if len(ranked) >= K_LEG * 2 else []
        cs_std = _std(list(rets.values())) if len(rets) >= K_LEG * 2 else None
        if cs_std is not None:
            hist_std.append(cs_std)
        med = _median(hist_std[-DISP_LOOKBACK:]) if len(hist_std) >= DISP_LOOKBACK else None
        wide = bool(cs_std is not None and med is not None and cs_std > med)
        ready = bool(laggards and leaders and i >= LOOKBACK)
        rebal = bool(ready and ((i - LOOKBACK) % REBALANCE_EVERY == 0))
        book.append(
            {
                "date": aligned[names[0]][i].get("date"),
                "timestamp_utc": aligned[names[0]][i].get("timestamp_utc"),
                "laggards": laggards,
                "leaders": leaders,
                "cs_std": cs_std,
                "is_xs_rebal": rebal,
                "is_xs_rebal_wide": bool(rebal and wide),
                "n_rets": len(rets),
                "role": None,
            }
        )
        i += 1
    return book
