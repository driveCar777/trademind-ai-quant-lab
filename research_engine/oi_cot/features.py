"""Join daily official OI flow to weekly positioning change. Knowledge = Friday 21:00Z."""
from __future__ import print_function

from research_engine.oi_cot import ROOTS
from research_engine.v6_external.curve import reject_broker_symbol


def _num(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sum_oi(curve_rows, root, prev_kt, kt):
    total = 0.0
    seen = False
    for row in curve_rows:
        if row.get("root") != root:
            continue
        know = row.get("oi_knowledge_utc") or ""
        if not know:
            continue
        if prev_kt and know <= prev_kt:
            continue
        if kt and know > kt:
            continue
        chg = _num(row.get("front_oi_change"))
        if chg is None:
            continue
        total += chg
        seen = True
    if not seen:
        return None
    return total


def tag_book(curve_rows, cot_by_root):
    by = {}
    dates = []
    seen = set()
    for row in curve_rows:
        reject_broker_symbol(row.get("root"))
        session = row.get("session_date")
        if not session:
            continue
        by[(row.get("root"), session)] = row
        if session not in seen:
            dates.append(session)
            seen.add(session)
    dates = sorted(dates)
    week_feat = {}
    for root in ROOTS:
        series = list(cot_by_root.get(root) or [])
        series = [r for r in series if r.get("knowledge_time_utc")]
        series.sort(key=lambda r: r.get("knowledge_time_utc") or "")
        i = 1
        while i < len(series):
            prev = series[i - 1]
            cur = series[i]
            kt = cur.get("knowledge_time_utc")
            prev_kt = prev.get("knowledge_time_utc")
            mm_now = _num(cur.get("mm_net"))
            mm_prev = _num(prev.get("mm_net"))
            if mm_now is None or mm_prev is None:
                i += 1
                continue
            mm_chg = mm_now - mm_prev
            week_oi = _sum_oi(curve_rows, root, prev_kt, kt)
            fire_date = None
            for session in dates:
                if session + "T00:00:00Z" > kt:
                    fire_date = session
                    break
            if fire_date:
                week_feat[(root, fire_date)] = {
                    "week_knowledge_utc": kt,
                    "week_oi_change": week_oi,
                    "mm_net_change": mm_chg,
                    "is_build_align": bool(week_oi is not None and week_oi > 0 and mm_chg > 0),
                    "is_speed_gap": bool(week_oi is not None and week_oi > 0 and mm_chg < 0),
                    "is_unwind_align": bool(week_oi is not None and week_oi < 0 and mm_chg < 0),
                }
            i += 1
    book = []
    aligned = dict((root, []) for root in ROOTS)
    for session in dates:
        roots = {}
        item = {"date": session, "timestamp_utc": session + "T00:00:00Z", "roots": roots, "role": None}
        for root in ROOTS:
            cur = by.get((root, session)) or {}
            feat = dict(cur)
            extra = week_feat.get((root, session)) or {}
            feat.update(extra)
            feat.setdefault("is_build_align", False)
            feat.setdefault("is_speed_gap", False)
            feat.setdefault("is_unwind_align", False)
            roots[root] = feat
            aligned[root].append(
                {
                    "date": session,
                    "timestamp_utc": session + "T00:00:00Z",
                    "open": _num(cur.get("front_open")),
                    "high": None,
                    "low": None,
                    "close": _num(cur.get("front_settle")),
                    "root": root,
                    "role": None,
                }
            )
        book.append(item)
    return book, aligned
