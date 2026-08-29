"""Join official settlement to broker CFD. Gap is DERIVED. GOLD is not spot."""
from __future__ import print_function

from research_engine.fut_cfd import ABSORB_CFD, ABSORB_FUT, CFD_OF, GAP, ROOTS
from research_engine.v6_external.curve import reject_broker_symbol


def _px(value):
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return number


def _ret(now, prev):
    a = _px(now)
    b = _px(prev)
    if a is None or b is None:
        return None
    return a / b - 1.0


def tag_book(curve_rows, cfd_by_root):
    curve = {}
    dates = set()
    for row in curve_rows:
        root = row.get("root")
        reject_broker_symbol(root)
        session = (row.get("session_date") or "")[:10]
        if root not in ROOTS or not session:
            continue
        curve[(root, session)] = row
        dates.add(session)
    cfd_dates = {}
    for root, bars in (cfd_by_root or {}).items():
        for bar in bars:
            day = (bar.get("date") or "")[:10]
            if day:
                cfd_dates.setdefault(root, {})[day] = bar
                dates.add(day)
    dates = sorted(d for d in dates if all(d in (cfd_dates.get(r) or {}) for r in ROOTS) and all((r, d) in curve for r in ROOTS))
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
            cur = curve.get((root, session)) or {}
            prev_cur = curve.get((root, prev)) if prev else None
            cfd = (cfd_dates.get(root) or {}).get(session) or {}
            prev_cfd = (cfd_dates.get(root) or {}).get(prev) if prev else None
            fut_ret = _ret(cur.get("front_settle"), (prev_cur or {}).get("front_settle"))
            cfd_ret = _ret(cfd.get("close"), (prev_cfd or {}).get("close"))
            gap = None
            if fut_ret is not None and cfd_ret is not None:
                gap = fut_ret - cfd_ret
            feat = {
                "cfd": CFD_OF[root],
                "front": cur.get("front"),
                "front_settle": _px(cur.get("front_settle")),
                "fut_ret": fut_ret,
                "cfd_ret": cfd_ret,
                "gap": gap,
                "is_fut_lead": bool(gap is not None and gap > GAP),
                "is_cfd_overshoot": bool(gap is not None and gap < -GAP),
                "is_absorb": bool(
                    fut_ret is not None
                    and cfd_ret is not None
                    and fut_ret > ABSORB_FUT
                    and abs(cfd_ret) < ABSORB_CFD
                ),
                "spread": cfd.get("spread"),
            }
            roots[root] = feat
            aligned[root].append(
                {
                    "date": session,
                    "timestamp_utc": session + "T00:00:00Z",
                    "open": _px(cfd.get("open")),
                    "high": _px(cfd.get("high")),
                    "low": _px(cfd.get("low")),
                    "close": _px(cfd.get("close")),
                    "spread": cfd.get("spread"),
                    "root": root,
                    "cfd": CFD_OF[root],
                    "role": None,
                }
            )
        book.append(item)
    return book, aligned
