"""At most 20 mechanisms. Top 5 scored. Execute one family at a time."""
from __future__ import print_function

from research_engine.v6_external.novelty import novelty_decision


TOP = [
    {
        "rank": 1,
        "id": "FUT_CFD_LEAD_V1",
        "mechanism": "Official exchange settlement versus broker GOLD/OIL CFD same-session return gap: futures leadership, CFD overshoot, absorption. Exchange basis between venue settlement and a parallel CFD quote. Not price momentum. Broker GOLD is not exchange spot.",
        "economic_rationale": "The listed front is the venue price. The CFD is a broker quote with different close and spread. A gap is quote disagreement, not a pair-to-metal lead.",
        "data": "tm-fut-GLBX-CURVE + tm-market-GOLD/OIL-D1-20260828",
        "history": "2018-12 to 2026-08 overlap",
        "cost": 0,
        "selected": False,
        "executed": "NO_CANDIDATE",
    },
    {
        "rank": 2,
        "id": "CURVE_OI_JOINT_V1",
        "mechanism": "Curve steepening with official contract open interest expansion and a settlement change. Joint curve move plus oi shock, not OI-rising-implies-buy and not slope-as-level.",
        "economic_rationale": "A curve move confirmed by new participation is different from a curve level or an OI sign alone.",
        "data": "frozen curve + OI-flow panel",
        "cost": 0,
        "selected": False,
        "executed": "NO_CANDIDATE",
    },
    {
        "rank": 3,
        "id": "OI_COT_BUILD_V1",
        "mechanism": "Daily official open interest flow versus weekly positioning change (build or unwind). Not a COT extreme.",
        "economic_rationale": "Exchange OI is daily; CFTC is a delayed census. Disagreement is a speed gap, not an extreme z.",
        "data": "OI-flow + CFTC GOLD/OIL 000002",
        "cost": 0,
        "selected": False,
        "executed": "WEAK_EDGE",
    },
    {
        "rank": 4,
        "id": "CURVE_EIA_REPRICE_V1",
        "mechanism": "EIA crude stocks week-over-week sign plus CL curve steepening. Inventory change curve repricing, not inventory z-score.",
        "economic_rationale": "A physical stock change should reprice deferred vs front if storage tightness changed.",
        "data": "curve CL + EIA WCESTUS1",
        "cost": 0,
        "selected": True,
    },
    {
        "rank": 5,
        "id": "CURVE_REALYIELD_V1",
        "mechanism": "UST10 yield change as a real-yield proxy plus GC curve slope change. Not a standardized yield threshold.",
        "economic_rationale": "A higher nominal long rate tightens the gold financing/storage trade-off on the curve, not a metal momentum bet.",
        "data": "curve GC + UST DGS10",
        "cost": 0,
        "selected": False,
    },
]


def opportunity_v8():
    rows = []
    for item in TOP:
        nov = novelty_decision(item["mechanism"], family_id=None)
        row = dict(item)
        row["novelty_guard"] = nov
        rows.append(row)
    chosen = [row for row in rows if row.get("selected")]
    return {
        "catalog_id": "ALPHA_OPPORTUNITY_V8",
        "NO_NEW_PURCHASE": True,
        "max_mechanisms": 20,
        "n": len(rows),
        "top5": rows,
        "selected": chosen[0]["id"] if chosen else None,
        "max_hypotheses": 3,
        "do_not_reopen": [
            "TERM_STRUCTURE_V1",
            "FUTURES_OI_FLOW_V1",
            "VOLUME_PRICE_FLOW_V1",
            "DTE_ROLL_WINDOW_V1",
            "POSITIONING_V1",
            "INVENTORY_V1",
            "RATES_V1",
            "CROSS_ASSET_V0.8",
            "BREADTH_V1",
            "SIZE_SPREAD_V1",
            "FUT_CFD_LEAD_V1",
            "CURVE_OI_JOINT_V1",
            "OI_COT_BUILD_V1",
        ],
    }
