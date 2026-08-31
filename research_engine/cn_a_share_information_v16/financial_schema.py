"""Financial schema. Raw API names stay in raw/. Normalized names are locked here."""
from __future__ import print_function

# Vendor profit fields we expect from BaoStock query_profit_data.
PROFIT_VENDOR = (
    "code",
    "pubDate",
    "statDate",
    "roeAvg",
    "npMargin",
    "gpMargin",
    "netProfit",
    "epsTTM",
    "MBRevenue",
    "totalShare",
    "liqaShare",
)

BALANCE_VENDOR = (
    "code",
    "pubDate",
    "statDate",
    "currentRatio",
    "quickRatio",
    "cashRatio",
    "YOYLiability",
    "liabilityToAsset",
    "assetToEquity",
)

NORMALIZED_COLS = (
    "symbol",
    "report_period",
    "announcement_date",
    "year",
    "quarter",
    "period_kind",
    "revenue",
    "net_profit",
    "eps",
    "eps_kind",
    "roe",
    "roa",
    "debt_ratio",
    "gross_margin",
    "np_margin",
    "source",
    "restatement_risk",
)

FIELD_STATUS = {
    "symbol": "FROM_CODE",
    "report_period": "FROM_STATDATE",
    "announcement_date": "FROM_PUBDATE",
    "revenue": "FROM_MBRevenue",
    "net_profit": "FROM_netProfit",
    "eps": "VENDOR_epsTTM_NOT_PERIOD_EPS",
    "roe": "FROM_roeAvg",
    "roa": "UNAVAILABLE_UNLESS_DERIVED_FROM_THEN_KNOWN",
    "debt_ratio": "FROM_liabilityToAsset_IF_BALANCE_DOWNLOADED",
    "gross_margin": "FROM_gpMargin",
}

PERIOD_KIND = {
    1: "QUARTERLY_Q1",
    2: "SEMIANNUAL_OR_Q2",
    3: "QUARTERLY_Q3",
    4: "ANNUAL",
}


def to_float(x):
    if x in (None, "", "None"):
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def normalize_profit_row(raw, year, quarter):
    if not raw:
        return None
    pub = (raw.get("pubDate") or "").strip()
    stat = (raw.get("statDate") or "").strip()
    if not pub or not stat:
        return None
    eps = to_float(raw.get("epsTTM"))
    return {
        "symbol": raw.get("code"),
        "report_period": stat,
        "announcement_date": pub,
        "year": int(year),
        "quarter": int(quarter),
        "period_kind": PERIOD_KIND[int(quarter)],
        "revenue": to_float(raw.get("MBRevenue")),
        "net_profit": to_float(raw.get("netProfit")),
        "eps": eps,
        "eps_kind": "VENDOR_TTM" if eps is not None else "UNAVAILABLE",
        "roe": to_float(raw.get("roeAvg")),
        "roa": None,
        "debt_ratio": None,
        "gross_margin": to_float(raw.get("gpMargin")),
        "np_margin": to_float(raw.get("npMargin")),
        "source": "BAOSTOCK_query_profit_data",
        "restatement_risk": True,
    }


def attach_balance(norm, raw_balance):
    if not norm or not raw_balance:
        return norm
    if (raw_balance.get("pubDate") or "").strip() != norm["announcement_date"]:
        # same period preferred; still attach if statDate matches
        if (raw_balance.get("statDate") or "").strip() != norm["report_period"]:
            return norm
    norm["debt_ratio"] = to_float(raw_balance.get("liabilityToAsset"))
    return norm
