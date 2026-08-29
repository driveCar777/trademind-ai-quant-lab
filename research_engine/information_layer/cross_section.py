"""Catalog existing MT5 D1 cross-section capacity. Do not research BREADTH/SIZE again."""
from __future__ import print_function

import os

from research_engine.data_expansion.paths import repo_root


FX_D1 = (
    "tm-market-AUDUSD-D1-20260828-000001",
    "tm-market-EURUSD-D1-20260828-000001",
    "tm-market-GBPUSD-D1-20260828-000001",
    "tm-market-NZDUSD-D1-20260828-000001",
    "tm-market-USDCAD-D1-20260828-000001",
    "tm-market-USDCHF-D1-20260828-000001",
    "tm-market-USDJPY-D1-20260828-000001",
    "tm-market-EURJPY-D1-20260828-000001",
    "tm-market-EURGBP-D1-20260828-000001",
    "tm-market-GBPJPY-D1-20260828-000001",
)


def cross_section_catalog():
    root = os.path.join(repo_root(), "data", "market", "immutable")
    present = []
    for dataset_id in FX_D1:
        path = os.path.join(root, dataset_id, "bars.csv")
        present.append({"dataset_id": dataset_id, "exists": os.path.isfile(path)})
    return {
        "catalog_id": "DERIVED_CROSS_SECTION_V1",
        "not_research": True,
        "do_not_reopen": ["BREADTH_V1", "SIZE_SPREAD_V1", "XS_REV_V1"],
        "available": {
            "cross_section_rank": True,
            "cross_section_dispersion": True,
            "breadth": "killed as 7-ag participation",
            "leader_laggard": True,
            "relative_return": True,
            "relative_volatility": True,
        },
        "fx_d1_parents": present,
        "stock_cfd_841": "classified only; not a true exchange breadth",
        "auto_research": False,
    }
