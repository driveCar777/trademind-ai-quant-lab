"""Pick exactly one new family. Rules are code, not taste."""
from __future__ import print_function

from research_engine.opportunity.score_v2 import rank_v2, top_n


FORBIDDEN_TOKENS = ("rsi", "macd", "ma cross", "ma_cross", "breakout scan", "weekday")


def _clean(row):
    text = ("%s %s %s" % (row.get("mechanism_text") or "", row.get("mechanism") or "", row.get("id") or "")).lower()
    for tok in FORBIDDEN_TOKENS:
        if tok in text:
            return False
    if row.get("killed_isomorph"):
        return False
    if row.get("status") != "UNKNOWN":
        return False
    if int(row.get("data_available") or 0) < 4:
        return False
    if int(row.get("economic_reason") or 0) < 4:
        return False
    if int(row.get("novelty") or 0) < 3:
        return False
    if row.get("needs_h1"):
        return False
    return True


def select_one(rows):
    scored, live = rank_v2(rows)
    top = top_n(live, 10)
    eligible = [r for r in top if _clean(r)]
    chosen = eligible[0] if eligible else None
    return {
        "top10": top,
        "eligible": [r["id"] for r in eligible],
        "chosen": None if chosen is None else chosen["id"],
        "chosen_row": chosen,
        "why": None if chosen is None else chosen.get("why_not_tested"),
        "rule": "UNKNOWN + data_available>=4 + economic_reason>=4 + not isomorph + not H1-blocked + not indicator",
    }
