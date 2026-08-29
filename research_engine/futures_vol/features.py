"""Lag volume events by one session so knowledge T+1 21:00Z is respected."""
from __future__ import print_function

from research_engine.futures_vol import ROOTS
from research_engine.v6_external.curve import reject_broker_symbol


def _px(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _flag(row, key):
    if not row:
        return False
    return str(row.get(key) or "") in ("1", "True", "true")


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
            feat["is_vol_confirm_up"] = _flag(lagged, "vol_confirm_up")
            feat["is_vol_fade_thin"] = _flag(lagged, "vol_fade_thin")
            feat["is_vol_pressure_down"] = _flag(lagged, "vol_pressure_down")
            roots[root] = feat
            aligned[root].append(
                {
                    "date": session,
                    "timestamp_utc": session + "T00:00:00Z",
                    "open": _px(cur.get("front_open")),
                    "high": None,
                    "low": None,
                    "close": _px(cur.get("front_settle")),
                    "root": root,
                    "role": None,
                }
            )
        book.append(item)
    return book, aligned
