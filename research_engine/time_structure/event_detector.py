"""Tag London / NY session-open H1 bars from the contracted DST tables only."""
from __future__ import print_function

from research_engine.errors import ContractMismatch
from research_engine.time_structure import CONTRACT_EVENTS
from research_engine.time_structure.dst import london_open_utc_hour, ny_fx_open_utc_hour


def _ymd_h(ts):
    if not ts or len(ts) < 13:
        return None
    try:
        return int(ts[0:4]), int(ts[5:7]), int(ts[8:10]), int(ts[11:13])
    except Exception:
        return None


def tag_bars(bars):
    i = 0
    while i < len(bars):
        bars[i]["is_london_open"] = False
        bars[i]["is_ny_fx_open"] = False
        parts = _ymd_h(bars[i].get("timestamp_utc") or "")
        if parts is None:
            i += 1
            continue
        y, m, d, hour = parts
        if hour == london_open_utc_hour(y, m, d):
            bars[i]["is_london_open"] = True
        if hour == ny_fx_open_utc_hour(y, m, d):
            bars[i]["is_ny_fx_open"] = True
        i += 1
    return bars


def fired_at(bar, event):
    if event not in CONTRACT_EVENTS:
        raise ContractMismatch("INVENTED_EVENT")
    if event == "LONDON_OPEN_H1":
        return bool(bar.get("is_london_open"))
    if event == "NY_FX_OPEN_H1":
        return bool(bar.get("is_ny_fx_open"))
    raise ContractMismatch("INVENTED_EVENT")


def event_dates(bars, event):
    out = []
    for bar in bars:
        if fired_at(bar, event):
            out.append(bar.get("timestamp_utc") or bar.get("date"))
    return out
