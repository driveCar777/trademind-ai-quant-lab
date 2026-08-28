"""Deterministic ranking. crowding 5 = retail-saturated = lower uniqueness."""
from __future__ import print_function


def uniqueness(crowding):
    c = int(crowding)
    if c < 1:
        c = 1
    if c > 5:
        c = 5
    return 6 - c


def item_score(row):
    if row.get("data_blocked") or int(row.get("data_availability") or 0) <= 1:
        return 0
    if row.get("killed_isomorph"):
        return 0
    e = int(row["economic_plausibility"])
    d = int(row["data_availability"])
    u = uniqueness(row["crowding"])
    c = int(row["cost_survivability"])
    t = int(row["testability"])
    return e * d * u * c * t


def annotate(rows):
    out = []
    for row in rows:
        item = dict(row)
        item["uniqueness"] = uniqueness(row["crowding"])
        item["score"] = item_score(row)
        item["implementable"] = item["score"] > 0 and not item.get("killed_isomorph")
        out.append(item)
    return out


def rank_implementable(rows):
    scored = annotate(rows)
    live = [r for r in scored if r["implementable"]]
    live.sort(key=lambda r: (-int(r["score"]), r["id"]))
    return scored, live


def cluster_best(live):
    best = {}
    for row in live:
        if not row.get("contract_eligible", True):
            continue
        key = row["cluster"]
        prev = best.get(key)
        if prev is None or int(row["score"]) > int(prev["score"]):
            best[key] = row
    clusters = list(best.values())
    clusters.sort(key=lambda r: (-int(r["score"]), r["cluster"]))
    return clusters
