"""Data Layer V0.1 constants. Schema fields live here; see SPEC §25."""

SCHEMA_VERSION = "0.1"

BAR_COLUMNS = [
    "timestamp_utc",
    "timestamp_unix",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "real_volume",
    "spread",
]

TIMEFRAME_MINUTES = {
    "M15": 15,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

ALLOWED_TIMEFRAMES = tuple(TIMEFRAME_MINUTES.keys())

LOGICAL_SYMBOLS = ("GOLD", "EURUSD", "USDJPY", "OIL")

DEFAULT_ALIASES = {
    "GOLD": ("GOLD", "XAUUSD", "XAUUSDm", "XAUUSD.a", "XAUUSD."),
    "EURUSD": ("EURUSD", "EURUSDm", "EURUSD.a"),
    "USDJPY": ("USDJPY", "USDJPYm", "USDJPY.a"),
    "OIL": ("CrudeOIL", "WTICrude", "XTIUSD", "USOIL", "CRUDE", "WTICOUSD"),
}

MT5_ALLOWED = (
    "initialize",
    "shutdown",
    "terminal_info",
    "version",
    "symbols_get",
    "symbol_info",
    "symbol_select",
    "copy_rates_from_pos",
    "copy_rates_from",
    "copy_rates_range",
    "last_error",
)

MT5_FORBIDDEN = (
    "order_send",
    "order_check",
    "positions_get",
    "orders_get",
    "history_orders_get",
    "history_deals_get",
    "order_calc_margin",
    "order_calc_profit",
    "login",
    "account_info",
)

BARS_FILENAME = "bars.csv"
MANIFEST_FILENAME = "manifest.json"
QUALITY_FILENAME = "DATA_QUALITY.json"
LOCK_FILENAME = "LOCK.json"

LOG_EVENTS = (
    "DATA_FETCH_START",
    "MT5_INITIALIZED",
    "SYMBOL_RESOLVED",
    "RATES_FETCHED",
    "DATA_VALIDATED",
    "DATA_WRITTEN",
    "MANIFEST_WRITTEN",
    "HASH_CREATED",
    "DATASET_FROZEN",
    "ERROR",
)
