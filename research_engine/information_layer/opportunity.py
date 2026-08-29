"""Rank unused mechanisms. TERM_STRUCTURE / RSI / z-cut are rejected."""
from __future__ import print_function

from research_engine.v6_external.novelty import novelty_decision


TOP = [
    {
        "rank": 1,
        "id": "FUTURES_OI_FLOW_V1",
        "mechanism": "Official contract open interest flow with same-session price: new longs, short covering, new shorts. Not price momentum. Not curve slope.",
        "novelty": "information novelty high: OI unused in V6.1",
        "history": "2010-2026 GC/CL official statistics",
        "cost": 0,
        "sample": "6728 oi_change rows on frozen curve",
        "potential_edge": "positioning confirmation, not a curve level",
        "complexity": "low",
        "selected": True,
    },
    {
        "rank": 2,
        "id": "VOLUME_PRICE_FLOW_V1",
        "mechanism": "cleared volume change times price change",
        "selected": False,
        "why_not_first": "volume not in slim curve panel; needs raw statistics rescan, still $0",
    },
    {
        "rank": 3,
        "id": "DTE_ROLL_WINDOW_V1",
        "mechanism": "days-to-expiry roll window, not slope",
        "selected": False,
    },
    {
        "rank": 4,
        "id": "CURVE_CURVATURE_V1",
        "mechanism": "front-second-third curvature",
        "selected": False,
        "why_not_first": "needs third outright rescan",
    },
    {
        "rank": 5,
        "id": "OI_PLUS_CURVE_STATE_V1",
        "mechanism": "OI flow filtered by backwardation",
        "selected": False,
        "why_not_first": "risk of TERM_STRUCTURE retune",
    },
    {
        "rank": 6,
        "id": "CL_CURVE_PLUS_EIA_V1",
        "mechanism": "CL structure + EIA stocks, not EIA z alone",
        "selected": False,
    },
    {
        "rank": 7,
        "id": "GC_CURVE_PLUS_COT_V1",
        "mechanism": "GC structure + CFTC, not weekly COT z alone",
        "selected": False,
    },
    {
        "rank": 8,
        "id": "GC_CURVE_PLUS_UST10_V1",
        "mechanism": "GC structure + UST10, not rates z-cut",
        "selected": False,
    },
    {
        "rank": 9,
        "id": "OI_PLUS_GVZ_V1",
        "mechanism": "OI flow + GVZ, not GVZ z-cross",
        "selected": False,
    },
    {
        "rank": 10,
        "id": "OFFICIAL_OI_VS_COT_V1",
        "mechanism": "daily exchange OI vs weekly COT disagreement",
        "selected": False,
    },
]


def opportunity_v7():
    rows = []
    for item in TOP:
        nov = novelty_decision(item["mechanism"], family_id=None)
        row = dict(item)
        row["novelty_guard"] = nov
        rows.append(row)
    chosen = [row for row in rows if row.get("selected")]
    return {
        "catalog_id": "ALPHA_OPPORTUNITY_V7",
        "NO_NEW_PURCHASE": True,
        "top10": rows,
        "selected": chosen[0]["id"] if chosen else None,
        "max_hypotheses": 3,
        "do_not_reopen": [
            "TERM_STRUCTURE_V1",
            "BREADTH_V1",
            "SIZE_SPREAD_V1",
            "POSITIONING_V1",
            "RSI",
        ],
    }
