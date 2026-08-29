"""Label information as OBSERVED / DERIVED / INFERRED. Do not mix."""
from __future__ import print_function


def provenance_catalog():
    return {
        "catalog_id": "PROVENANCE_V8",
        "rule": "OBSERVED is a vendor or broker field. DERIVED is a deterministic transform. INFERRED is an LLM or narrative claim.",
        "items": [
            {"name": "GC/CL official settlement", "kind": "OBSERVED", "source": "Databento statistics"},
            {"name": "GC/CL official open interest", "kind": "OBSERVED", "source": "Databento statistics", "knowledge": "T+1 21:00Z"},
            {"name": "GC/CL cleared volume", "kind": "OBSERVED", "source": "Databento statistics", "knowledge": "T+1 21:00Z"},
            {"name": "GC/CL expiry / front identity", "kind": "OBSERVED", "source": "Databento definition"},
            {"name": "curve slope / roll / backwardation", "kind": "DERIVED", "from": "two official settlements"},
            {"name": "OI shock / new longs / cover", "kind": "DERIVED", "from": "OI change x settlement change"},
            {"name": "volume shock", "kind": "DERIVED", "from": "cleared volume change x settlement change"},
            {"name": "days to expiry / front roll", "kind": "DERIVED", "from": "definition + calendar"},
            {"name": "MT5 GOLD/OIL OHLC", "kind": "OBSERVED", "source": "broker CFD quote, not exchange spot"},
            {"name": "CFTC mm_net_oi", "kind": "OBSERVED", "source": "CFTC disagg COT"},
            {"name": "EIA crude stocks", "kind": "OBSERVED", "source": "EIA WCESTUS1"},
            {"name": "UST10 / EFFR", "kind": "OBSERVED", "source": "public rates"},
            {"name": "futures minus CFD return gap", "kind": "DERIVED", "from": "official settlement vs broker close"},
            {"name": "daily OI vs weekly positioning change", "kind": "DERIVED", "from": "official OI + CFTC"},
            {"name": "inventory wow + curve steepening", "kind": "DERIVED", "from": "EIA wow + official slope change"},
            {"name": "UST10 change + GC curve", "kind": "DERIVED", "from": "DGS10 change + official slope"},
            {"name": "MARKET_INFORMATION_STATE", "kind": "DERIVED", "from": "controlled state vector"},
            {"name": "economic narrative / LLM gloss", "kind": "INFERRED", "not_a_feature": True},
        ],
    }
