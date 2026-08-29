"""Mechanism-driven fusion catalog. Not a feature cross-product farm."""
from __future__ import print_function


def fusion_catalog():
    return {
        "catalog_id": "INFORMATION_FUSION_V7",
        "rule": "economic mechanism only. no feature1 x feature2 x feature3 farm",
        "states": [
            {
                "id": "futures_oi_price_state",
                "mechanism": "Official front OI change confirms or denies the same-session price change. New longs / covering / new shorts.",
                "legs": ["GLBX settlement", "GLBX open interest"],
                "knowledge": "joint known at OI knowledge T+1 21:00Z",
                "novelty": "NEW",
                "selected": True,
            },
            {
                "id": "futures_curve_state",
                "mechanism": "front-second slope",
                "novelty": "KILLED TERM_STRUCTURE_V1",
                "selected": False,
            },
            {
                "id": "positioning_state_cot",
                "mechanism": "weekly CFTC extremes",
                "novelty": "KILLED POSITIONING_V1",
                "selected": False,
            },
            {
                "id": "inventory_state_eia",
                "mechanism": "EIA stocks z-cross",
                "novelty": "KILLED INVENTORY_V1",
                "selected": False,
            },
            {
                "id": "rates_state_ust10",
                "mechanism": "UST10 z-cross",
                "novelty": "KILLED RATES_V1",
                "selected": False,
            },
            {
                "id": "usd_state_dxy",
                "mechanism": "DXY z into metals",
                "novelty": "KILLED USD_METAL_V1",
                "selected": False,
            },
            {
                "id": "curve_plus_cot",
                "mechanism": "exchange curve + CFTC, not COT alone",
                "novelty": "FUSION_UNUSED",
                "selected": False,
                "rank_note": "weekly sparse; after OI flow",
            },
            {
                "id": "curve_plus_eia",
                "mechanism": "CL curve + EIA stocks",
                "novelty": "FUSION_UNUSED",
                "selected": False,
                "rank_note": "after OI flow",
            },
        ],
        "gold_example": {
            "price_state": "front settlement change",
            "futures_curve_state": "killed as level",
            "oi_state": "front OI change after T+1 knowledge",
            "usd_state": "DXY available but USD_METAL killed z-cut",
            "volatility_state": "GVZ killed as z-cross",
        },
    }
