"""Industry schema. PIT requires an effective date. Snapshot-only is not enough."""
from __future__ import print_function

INDUSTRY_VENDOR = ("updateDate", "code", "code_name", "industry", "industryClassification")

NORMALIZED_COLS = (
    "symbol",
    "name",
    "industry",
    "industry_classification",
    "source_update_date",
    "effective_date",
    "pit_available",
    "source",
)


def normalize_industry_row(raw):
    if not raw:
        return None
    upd = (raw.get("updateDate") or "").strip()
    return {
        "symbol": raw.get("code"),
        "name": raw.get("code_name"),
        "industry": raw.get("industry"),
        "industry_classification": raw.get("industryClassification"),
        "source_update_date": upd or None,
        "effective_date": None,
        "pit_available": False,
        "source": "BAOSTOCK_query_stock_industry",
    }
