"""Locked V0.6 labels. Formula is written here, not invented after seeing results."""
from __future__ import print_function


def _pos(value):
    return value is not None and value > 0


def classify_row(research, validation):
    r = research or {}
    v = validation or {}
    r_tr = r.get("total_return")
    v_tr = v.get("total_return")
    r_n = r.get("trade_count") or 0
    v_n = v.get("trade_count") or 0
    r_dd = r.get("max_drawdown")
    v_dd = v.get("max_drawdown")
    share = r.get("max_trade_share")
    reasons = []
    if r_n < 8:
        reasons.append("RESEARCH_TRADES<%s" % 8)
    if v_n < 4:
        reasons.append("VALIDATION_TRADES<%s" % 4)
    if not _pos(r_tr):
        reasons.append("RESEARCH_NOT_PROFITABLE")
    if not _pos(v_tr):
        reasons.append("VALIDATION_NOT_PROFITABLE")
    if r_dd is None or r_dd < -0.25:
        reasons.append("RESEARCH_DD")
    if v_dd is None or v_dd < -0.30:
        reasons.append("VALIDATION_DD")
    if share is not None and share > 0.50:
        reasons.append("SINGLE_TRADE_DOMINANCE")
    if not reasons:
        return "CANDIDATE", "PASS_LOCKED_GATES"
    if _pos(r_tr) or _pos(v_tr):
        return "WEAK_EDGE", ",".join(reasons)
    return "NO_EDGE", ",".join(reasons)


def rank_program(dataset_rows):
    """dataset_rows: list of {dataset_id, timeframe, strategy_id, research, validation}"""
    by_sid = {}
    for row in dataset_rows:
        sid = row.get("strategy_id")
        bucket = by_sid.get(sid)
        if bucket is None:
            bucket = {"strategy_id": sid, "family": row.get("family"), "datasets": []}
            by_sid[sid] = bucket
        status, why = classify_row(row.get("research"), row.get("validation"))
        item = dict(row)
        item["dataset_status"] = status
        item["dataset_why"] = why
        bucket["datasets"].append(item)
    ranked = []
    for sid in sorted(by_sid.keys()):
        bucket = by_sid[sid]
        pos = 0
        cand = 0
        weak = 0
        none = 0
        rets = []
        for item in bucket["datasets"]:
            st = item["dataset_status"]
            if st == "CANDIDATE":
                cand += 1
            elif st == "WEAK_EDGE":
                weak += 1
            else:
                none += 1
            tr = (item.get("research") or {}).get("total_return")
            if tr is not None:
                rets.append(tr)
                if tr > 0:
                    pos += 1
        if cand >= 2:
            status = "CANDIDATE"
            why = "CANDIDATE_ON_GE_2_DATASETS"
        elif cand == 1 or (weak >= 2 and pos >= 2):
            status = "WEAK_EDGE"
            why = "PARTIAL_SUPPORT"
        else:
            status = "NO_EDGE"
            why = "SEARCH_SPACE_INSUFFICIENT_OR_NULL"
        ranked.append(
            {
                "strategy_id": sid,
                "family": bucket["family"],
                "status": status,
                "why": why,
                "candidate_datasets": cand,
                "weak_datasets": weak,
                "no_edge_datasets": none,
                "positive_research_datasets": pos,
                "tested_datasets": len(bucket["datasets"]),
                "mean_research_return": None if not rets else sum(rets) / float(len(rets)),
                "rows": bucket["datasets"],
                "note": "CANDIDATE != 10% annualized. Not MT5.",
            }
        )
    counts = {"CANDIDATE": 0, "WEAK_EDGE": 0, "NO_EDGE": 0}
    for row in ranked:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    outcome = "NO_STRATEGY_CANDIDATE"
    if counts["CANDIDATE"]:
        outcome = "STRATEGY_CANDIDATE_FOUND"
    elif counts["WEAK_EDGE"]:
        outcome = "WEAK_EDGE_ONLY"
    return {
        "outcome": outcome,
        "counts": counts,
        "strategies": ranked,
        "gate": (
            "CANDIDATE dataset: research and validation total_return>0 after cost, "
            "research trades>=8, validation trades>=4, DD>=-25%/-30%, "
            "max trade share<=50%. Program CANDIDATE needs that on >=2 datasets."
        ),
    }
