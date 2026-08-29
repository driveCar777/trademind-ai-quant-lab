"""Lag curve-steepening x OI joints by one session so OI knowledge T+1 21:00Z is respected."""
from __future__ import print_function

from research_engine.curve_oi import ROOTS
from research_engine.v6_external.curve import reject_broker_symbol


def _num(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _joint(row, steep_sign, oi_sign):
    if not row:
        return False
    steep = _num(row.get("steepening"))
    oi_chg = _num(row.get("front_oi_change"))
    if steep is None or oi_chg is None:
        return False
    if steep_sign > 0 and not (steep > 0):
        return False
    if steep_sign < 0 and not (steep < 0):
        return False
    if oi_sign > 0 and not (oi_chg > 0):
        return False
    if oi_sign < 0 and not (oi_chg < 0):
        return False
    return True


def tag_book(rows):
    by = {}
    dates = []
    seen = set()
    for row in rows:
        reject_broker_symbol(row.get("root"))
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
    book = []
    aligned = dict((root, []) for root in ROOTS)
    for session in dates:
        roots = {}
        item = {"date": session, "timestamp_utc": session + "T00:00:00Z", "roots": roots, "role": None}
        prev = prev_of.get(session)
        for root in ROOTS:
            cur = by.get((root, session)) or {}
            lagged = by.get((root, prev)) if prev else None
            feat = dict(cur)
            feat["lagged_session_date"] = prev
            feat["is_steepen_oi_expand"] = _joint(lagged, 1, 1)
            feat["is_flatten_oi_expand"] = _joint(lagged, -1, 1)
            feat["is_steepen_oi_contract"] = _joint(lagged, 1, -1)
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
