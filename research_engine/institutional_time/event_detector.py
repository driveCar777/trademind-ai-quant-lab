"""Tag month-end / month-start from timestamps already on the bar. No invented kinds."""
from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.institutional_time import CONTRACT_EVENTS


def _ymd(ts):
    if not ts:
        return None
    try:
        return int(ts[0:4]), int(ts[5:7]), int(ts[8:10])
    except Exception:
        return None


def tag_bars(bars):
    """Add is_month_end / is_month_start using only this series' dates."""
    ymds = []
    i = 0
    while i < len(bars):
        ymds.append(_ymd(bars[i].get("timestamp_utc") or bars[i].get("date")))
        i += 1
    n = len(ymds)
    i = 0
    while i < n:
        cur = ymds[i]
        bars[i]["is_month_end"] = False
        bars[i]["is_month_start"] = False
        if cur is None:
            i += 1
            continue
        prev = ymds[i - 1] if i else None
        nxt = ymds[i + 1] if i + 1 < n else None
        y, m, _d = cur
        if prev is None or prev[0] != y or prev[1] != m:
            bars[i]["is_month_start"] = True
        if nxt is None or nxt[0] != y or nxt[1] != m:
            bars[i]["is_month_end"] = True
        i += 1
    return bars


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "LAST_D1_BAR_OF_CALENDAR_MONTH":
        return bool(bar.get("is_month_end"))
    if event == "FIRST_D1_BAR_OF_CALENDAR_MONTH":
        return bool(bar.get("is_month_start"))
    raise ContractMismatch("INVENTED_EVENT")


def event_dates(bars, event):
    out = []
    for bar in bars:
        if fired_at(bar, event):
            out.append(bar.get("date") or (bar.get("timestamp_utc") or "")[:10])
    return out
