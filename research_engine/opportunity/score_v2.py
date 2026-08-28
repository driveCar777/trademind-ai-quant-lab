"""Opportunity Score V2.

score = mechanism * economic_reason * data_available * time_scale
        * transaction_cost_survival * novelty
previous_failure is a multiplier in {0, 1, 2} inverted: 0 kills, 1 isomorph risk, 2 clean.
"""
from __future__ import print_function


AXES = (
    "mechanism",
    "economic_reason",
    "data_available",
    "time_scale",
    "transaction_cost_survival",
    "novelty",
)


def _clip(value, lo=0, hi=5):
    try:
        n = int(value)
    except Exception:
        n = 0
    if n < lo:
        return lo
    if n > hi:
        return hi
    return n


def item_score(row):
    if row.get("killed_isomorph") or row.get("status") in ("FAILED", "BLOCKED", "FORBIDDEN"):
        return 0
    if int(row.get("data_available") or 0) <= 0:
        return 0
    prev = _clip(row.get("previous_failure"), 0, 2)
    if prev <= 0:
        return 0
    acc = 1
    for key in AXES:
        acc *= _clip(row.get(key) or 0)
    return acc * prev


def annotate(rows):
    out = []
    for row in rows:
        item = dict(row)
        item["score"] = item_score(item)
        item["implementable"] = item["score"] > 0 and item.get("status") == "UNKNOWN"
        out.append(item)
    return out


def rank_v2(rows):
    scored = annotate(rows)
    live = [r for r in scored if r.get("implementable")]
    live.sort(key=lambda r: (-int(r["score"]), r["id"]))
    scored.sort(key=lambda r: (-int(r["score"]), r["id"]))
    return scored, live


def top_n(live, n=10):
    return live[:n]
