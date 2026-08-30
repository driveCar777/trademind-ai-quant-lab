"""A-share schemas. No alpha fields."""
from __future__ import print_function

SCHEMA_VERSION = "12.1"

TYPE_MAP = {
    "1": "EQUITY",
    "2": "INDEX",
    "4": "CONVERTIBLE",
    "5": "ETF",
}

DAILY_RAW_COLS = (
    "trade_date",
    "symbol",
    "raw_open",
    "raw_high",
    "raw_low",
    "raw_close",
    "volume",
    "amount",
    "turnover",
    "preclose",
    "tradestatus",
    "is_st",
    "adjustflag",
)

DAILY_ADJ_COLS = (
    "trade_date",
    "symbol",
    "adjusted_open",
    "adjusted_high",
    "adjusted_low",
    "adjusted_close",
    "adjust_convention",
    "adjustflag",
)

BASIC_COLS = (
    "symbol",
    "name",
    "listing_date",
    "delisting_date",
    "instrument_type",
    "status",
    "listing_date_known",
    "delisting_date_known",
)

CALENDAR_COLS = ("calendar_date", "is_trading_day", "weekday", "session_tz")

INDUSTRY_COLS = ("symbol", "industry", "industry_classification", "effective_date", "pit_available")

FINANCIAL_MIN_COLS = (
    "symbol",
    "report_period",
    "announcement_date",
    "revenue",
    "net_profit",
    "eps",
    "roe",
    "roa",
    "gross_margin",
    "debt_ratio",
)

SESSION = {
    "timezone": "Asia/Shanghai",
    "morning": {"open": "09:30", "close": "11:30"},
    "afternoon": {"open": "13:00", "close": "15:00"},
    "note": "Defined only. Intraday research is later.",
}

ADJUST_CONVENTIONS = {
    "3": "RAW_UNADJUSTED",
    "2": "FORWARD_QFQ",
    "1": "BACKWARD_HFQ",
}


def dataset_id(kind, ymd, seq=1):
    return "tm-cn-a-%s-%s-%06d" % (kind, ymd, int(seq))


def ashare_dataset_id(ymd, seq=1, kind="EQUITY-D1"):
    """TradeMind convention: tm-ashare-{kind}-{YYYYMMDD}-{seq}."""
    return "tm-ashare-%s-%s-%06d" % (kind, ymd, int(seq))


def quality_label(ok, limitations):
    if not ok:
        return "BLOCKED"
    if limitations:
        return "CONDITIONAL"
    return "PASS"
