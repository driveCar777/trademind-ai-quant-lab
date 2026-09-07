"""Dividend event scores. announce_date < signal date. Window = 20 pack sessions."""
from __future__ import print_function

import bisect
import csv

import numpy as np

from research_engine.cn_a_share_div_v21 import EVENT_WINDOW
from research_engine.cn_a_share_div_v21.paths import DIV_CSV


def load_dividend_rows(path=None):
    path = path or DIV_CSV
    rows = []
    handle = open(path, "r", encoding="utf-8")
    try:
        for row in csv.DictReader(handle):
            if row.get("symbol") and row.get("announce_date") and row.get("kind"):
                rows.append(row)
    finally:
        handle.close()
    return rows


def event_score(pack, rows, kinds, window=EVENT_WINDOW):
    dates = pack["dates"]
    pos = dict((s, i) for i, s in enumerate(pack["symbols"]))
    t = len(dates)
    n = len(pack["symbols"])
    out = np.zeros((t, n), dtype=np.float64)
    kind_set = set(kinds)
    for r in rows:
        if r.get("kind") not in kind_set:
            continue
        j = pos.get(r.get("symbol"))
        if j is None:
            continue
        start = bisect.bisect_right(dates, r["announce_date"])
        if start >= t:
            continue
        end = start + window
        if end > t:
            end = t
        out[start:end, j] = 1.0
    return out


def build_scores(pack, rows):
    return {
        "CASH_ANN_20": event_score(pack, rows, ("CASH", "BOTH")),
        "STOCK_ANN_20": event_score(pack, rows, ("STOCK", "BOTH")),
    }
