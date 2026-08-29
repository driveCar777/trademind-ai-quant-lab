"""Join UST10 yield change to GC curve steepening. Knowledge = session T 21:00Z, lagged one session."""
from __future__ import print_function

from research_engine.curve_rate import ROOTS
from research_engine.v6_external.curve import reject_broker_symbol


def _num(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def tag_book(curve_rows, ust_rows):
    by = {}
    dates = []
    seen = set()
    for row in curve_rows:
        reject_broker_symbol(row.get("root"))
        if row.get("root") not in ROOTS:
            continue
        session = row.get("session_date")
        if not session:
            continue
        by[(row.get("root"), session)] = row
        if session not in seen:
            dates.append(session)
            seen.add(session)
    dates = sorted(dates)
    prev_of = {}
    i = 1
    while i < len(dates):
        prev_of[dates[i]] = dates[i - 1]
        i += 1
    ust = {}
    for row in ust_rows or []:
        ts = (row.get("timestamp_utc") or row.get("date") or "")[:10]
        if ts:
            ust[ts] = _num(row.get("close"))
    book = []
    aligned = dict((root, []) for root in ROOTS)
    for session in dates:
        roots = {}
        item = {"date": session, "timestamp_utc": session + "T00:00:00Z", "roots": roots, "role": None}
        prev = prev_of.get(session)
        lagged = prev_of.get(prev) if prev else None
        for root in ROOTS:
            cur = by.get((root, session)) or {}
            src = by.get((root, prev)) if prev else None
            feat = dict(cur)
            feat["lagged_session_date"] = prev
            feat["rates_knowledge_utc"] = (prev + "T21:00:00Z") if prev else None
            y_now = ust.get(prev) if prev else None
            y_prev = ust.get(lagged) if lagged else None
            y_chg = None if y_now is None or y_prev is None else y_now - y_prev
            steep = None if src is None else _num(src.get("steepening"))
            feat["yield_change"] = y_chg
            feat["lagged_steepening"] = steep
            feat["is_yield_up_steepen"] = bool(y_chg is not None and y_chg > 0 and steep is not None and steep > 0)
            feat["is_yield_up_flatten"] = bool(y_chg is not None and y_chg > 0 and steep is not None and steep < 0)
            feat["is_yield_down_flatten"] = bool(y_chg is not None and y_chg < 0 and steep is not None and steep < 0)
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
