"""Join EIA stocks wow sign to CL curve steepening. Knowledge = Wednesday 16:00Z."""
from __future__ import print_function

from research_engine.curve_eia import ROOTS
from research_engine.v6_external.curve import reject_broker_symbol


def _num(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _last_steep(curve_rows, root, kt):
    last = None
    for row in curve_rows:
        if row.get("root") != root:
            continue
        know = row.get("settlement_knowledge_utc") or ""
        if not know or (kt and know > kt):
            continue
        steep = _num(row.get("steepening"))
        if steep is None:
            continue
        last = steep
    return last


def tag_book(curve_rows, eia_rows):
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
    series = [r for r in (eia_rows or []) if r.get("knowledge_time_utc")]
    series.sort(key=lambda r: r.get("knowledge_time_utc") or "")
    week_feat = {}
    i = 1
    while i < len(series):
        prev = series[i - 1]
        cur = series[i]
        kt = cur.get("knowledge_time_utc")
        now = _num(cur.get("value"))
        before = _num(prev.get("value"))
        if now is None or before is None:
            i += 1
            continue
        wow = now - before
        steep = _last_steep(curve_rows, "CL", kt)
        fire_date = None
        for session in dates:
            if session + "T00:00:00Z" > kt:
                fire_date = session
                break
        if fire_date:
            week_feat[("CL", fire_date)] = {
                "eia_knowledge_utc": kt,
                "inv_wow": wow,
                "cl_steepening": steep,
                "is_inv_build_steepen": bool(wow > 0 and steep is not None and steep > 0),
                "is_inv_draw_flatten": bool(wow < 0 and steep is not None and steep < 0),
                "is_inv_draw_steepen": bool(wow < 0 and steep is not None and steep > 0),
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
            feat.setdefault("is_inv_build_steepen", False)
            feat.setdefault("is_inv_draw_flatten", False)
            feat.setdefault("is_inv_draw_steepen", False)
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
