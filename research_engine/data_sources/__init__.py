"""Unified data-source adapters. No READY_FOR_RESEARCH without bytes."""

PIPELINE = ("fetch", "normalize", "timestamp", "validate", "hash", "immutable")
REQUIRED_FIELDS = (
    "timestamp_utc",
    "knowledge_timestamp_utc",
    "source",
    "asset",
    "field",
    "value",
    "revision",
)
OPTION_FIELDS = (
    "expiry",
    "strike",
    "option_type",
    "implied_volatility",
    "delta",
)
FUTURES_FIELDS = (
    "contract",
    "expiry",
    "settlement",
    "open_interest",
    "volume",
)
TIME_FIELDS = (
    "event_time",
    "publication_time",
    "knowledge_time",
)
ENV_DATABENTO = "TRADEMIND_DATABENTO_API_KEY"
ENV_ORATS = "TRADEMIND_ORATS_API_KEY"
ENV_TE = "TRADEMIND_TRADINGECONOMICS_API_KEY"
