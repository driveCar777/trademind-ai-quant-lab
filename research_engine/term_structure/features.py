"""Tag the aligned book from the frozen curve panel. No CFD rows."""
from __future__ import print_function

from research_engine.term_structure import ROOTS
from research_engine.v6_external.curve import reject_broker_symbol


def tag_book(features):
    by_date = {}
    for row in features:
        reject_broker_symbol(row.get("root") or row.get("asset"))
        session = row.get("session_date")
        if not session:
            continue
        by_date.setdefault(session, {})[row.get("root")] = row
    dates = sorted(by_date.keys())
    book = []
    aligned = dict((root, []) for root in ROOTS)
    for session in dates:
        roots = {}
        item = {"date": session, "timestamp_utc": session + "T00:00:00Z", "roots": roots, "role": None}
        for root in ROOTS:
            feat = (by_date.get(session) or {}).get(root)
            roots[root] = feat
            bar = {
                "date": session,
                "timestamp_utc": session + "T00:00:00Z",
                "open": None if feat is None else feat.get("front_open"),
                "high": None,
                "low": None,
                "close": None if feat is None else feat.get("front_settle"),
                "root": root,
                "role": None,
            }
            aligned[root].append(bar)
        book.append(item)
    return book, aligned
