"""Tag first H1 after a calendar gap >= 36h. Not a Monday dummy."""
from __future__ import print_function

from datetime import datetime

from research_engine.alt_market_structure import GAP_HOURS


def _ts(bar):
    raw = bar.get("timestamp_utc") or ""
    try:
        return datetime.strptime(raw.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


def tag_gaps(bars, gap_hours=GAP_HOURS):
    prev = None
    prev_close = None
    i = 0
    while i < len(bars):
        bars[i]["is_gap_reopen"] = False
        bars[i]["is_gap_down"] = False
        cur = _ts(bars[i])
        if prev is not None and cur is not None:
            delta_h = (cur - prev).total_seconds() / 3600.0
            if delta_h >= float(gap_hours):
                bars[i]["is_gap_reopen"] = True
                op = bars[i].get("open")
                if prev_close and op and float(op) < float(prev_close):
                    bars[i]["is_gap_down"] = True
        prev = cur
        prev_close = bars[i].get("close")
        i += 1
    return bars
