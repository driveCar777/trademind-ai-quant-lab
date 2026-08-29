"""DTE and front-roll events. Definition is known at settlement 21:00Z. No OI lag."""
from __future__ import print_function

from research_engine.futures_dte import ROOTS
from research_engine.v6_external.curve import reject_broker_symbol


def _px(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _dte(value):
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


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
            dte = _dte(cur.get("days_to_expiry"))
            front = (cur.get("front") or "").strip()
            prev_front = ((lagged or {}).get("front") or "").strip()
            rolled = bool(front and prev_front and front != prev_front)
            feat = dict(cur)
            feat["session_for_knowledge"] = session
            feat["is_near_expiry"] = bool(dte is not None and dte <= 5)
            feat["is_front_roll"] = rolled
            older = by.get((root, prev_of.get(prev))) if prev and prev_of.get(prev) else None
            older_front = ((older or {}).get("front") or "").strip()
            feat["is_post_roll"] = bool(prev_front and older_front and prev_front != older_front)
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
