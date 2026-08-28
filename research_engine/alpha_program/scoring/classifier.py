"""Score an economic mechanism. Not an indicator farm."""
from __future__ import print_function


AXES = (
    "economic_plausibility",
    "data_availability",
    "historical_coverage",
    "existing_evidence",
    "implementation_feasibility",
)


def _clip(value):
    try:
        n = int(value)
    except Exception:
        n = 1
    if n < 1:
        return 1
    if n > 5:
        return 5
    return n


def opportunity_score(row):
    if row.get("status") == "BLOCKED" or row.get("data_blocked"):
        return 0
    if row.get("status") == "FAILED" and row.get("killed_isomorph"):
        return 0
    acc = 1
    for key in AXES:
        acc *= _clip(row.get(key) or 1)
    return acc


def classify(row):
    item = dict(row)
    item["score"] = opportunity_score(item)
    status = item.get("status")
    if item.get("data_blocked"):
        item["status"] = "BLOCKED"
    elif item.get("killed_isomorph") or status == "FAILED":
        item["status"] = "FAILED"
    elif status not in ("DONE", "FAILED", "UNKNOWN", "BLOCKED"):
        item["status"] = "UNKNOWN"
    item["implementable"] = item["score"] > 0 and item.get("status") not in ("BLOCKED", "FAILED")
    return item


def rank_mechanisms(rows):
    scored = [classify(r) for r in rows]
    live = [r for r in scored if r.get("implementable")]
    live.sort(key=lambda r: (-int(r["score"]), r["id"]))
    scored.sort(key=lambda r: (-int(r["score"]), r["id"]))
    return scored, live
