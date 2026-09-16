"""DATA_SNAPSHOT: universe composition + quality distribution on a reference day.

Answers "is the return just from buying junk small-caps?" WITHOUT changing any selection. Fields that
need data we don't have (market cap) are reported UNKNOWN, never fabricated. Read-only.
"""
from __future__ import print_function

import numpy as np


def _pct(a, q):
    a = np.asarray(a, dtype=float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return None
    return float(np.percentile(a, q))


def _board_of(sym):
    if sym.startswith("sh.688"):
        return "STAR"
    if sym.startswith("bj."):
        return "BSE"
    if sym.startswith("sz.30"):
        return "CHINEXT"
    if sym.startswith("sh.60") or sym.startswith("sz.00"):
        return "MAIN"
    return "OTHER"


def data_snapshot(pack=None, elig=None, asof_index=None, data_status="READY"):
    """Build a DATA_SNAPSHOT for a reference day. If pack is None/degenerate -> UNKNOWN with reason."""
    if pack is None:
        return {"data_status": data_status, "available": False, "reason": "NO_PACK",
                "market_cap": "UNKNOWN"}
    symbols = pack["symbols"]
    close = np.asarray(pack["close"], dtype=float)
    T, N = close.shape
    t = asof_index if asof_index is not None else (T - 1)
    t = max(0, min(t, T - 1))
    listed = np.asarray(pack["listed"])[t]
    status = np.asarray(pack["tradestatus"])[t]
    st = np.asarray(pack["isST"])[t]
    o = np.asarray(pack["open"], dtype=float)[t]
    pre = np.asarray(pack["preclose"], dtype=float)[t]
    c = close[t]
    amt = np.asarray(pack["amount"], dtype=float)[t] if "amount" in pack else np.full(N, np.nan)
    turn = np.asarray(pack["turn"], dtype=float)[t] if "turn" in pack else np.full(N, np.nan)

    listed_mask = listed == 1
    total = int(listed_mask.sum())
    # board composition among listed
    boards = {"MAIN": 0, "CHINEXT": 0, "STAR": 0, "BSE": 0, "OTHER": 0}
    for j in np.where(listed_mask)[0]:
        boards[_board_of(symbols[int(j)])] += 1
    st_count = int(((st == 1) & listed_mask).sum())
    suspended = int(((status != 1) & listed_mask).sum())

    # limit-hit count on the day (uses canonical limit rule, read-only)
    try:
        from research_engine.cn_a_share_alpha.pack import limit_pct_for
        day = pack["dates"][t]
        lim = 0
        with np.errstate(all="ignore"):
            ratio = np.where((pre > 0) & np.isfinite(pre) & np.isfinite(c), c / pre - 1.0, np.nan)
        for j in np.where(listed_mask)[0]:
            j = int(j)
            r = ratio[j]
            if not np.isfinite(r):
                continue
            L = limit_pct_for(symbols[j], bool(st[j] == 1), day)
            if abs(r) >= L - 0.002:
                lim += 1
        limit_hits = int(lim)
    except Exception:
        limit_hits = "UNKNOWN"

    px = c[listed_mask]
    amt_l = amt[listed_mask]
    turn_l = turn[listed_mask]
    n_elig = int(np.asarray(elig[t]).sum()) if elig is not None else "UNKNOWN"

    def dist(a, have):
        if not have:
            return "UNKNOWN"
        return {"min": _pct(a, 0), "p10": _pct(a, 10), "median": _pct(a, 50),
                "p90": _pct(a, 90), "max": _pct(a, 100)}

    return {
        "data_status": data_status, "available": True, "asof": pack["dates"][t],
        "total_listed_symbols": total, "eligible_symbols": n_elig,
        "board_composition": boards, "st_count": st_count, "suspended_count": suspended,
        "limit_hit_count": limit_hits,
        "price_distribution": dist(px, True),
        "amount_distribution": dist(amt_l, bool(np.isfinite(amt_l).any())),
        "turnover_distribution": dist(turn_l, bool(np.isfinite(turn_l).any())),
        "volatility_distribution": "UNKNOWN",   # not computed here (needs return window); avoid fabrication
        "market_cap": "UNKNOWN",                # no shares-outstanding data in A-Short pack
        "note": "market_cap/volatility require data not in the frozen D1 pack -> UNKNOWN (not fabricated).",
    }


__all__ = ["data_snapshot"]
