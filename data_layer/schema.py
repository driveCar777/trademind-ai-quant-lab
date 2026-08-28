"""Bar and manifest schemas. Missing values stay null — never silently 0."""

from data_layer.constants import BAR_COLUMNS, SCHEMA_VERSION


def empty_optional(value):
    if value is None:
        return None
    return value


def bar_from_mt5_row(row):
    """Convert one MT5 rate row to the V0.1 bar dict."""
    unix = int(row["time"])
    spread = row["spread"] if "spread" in row.dtype.names else None
    tick = row["tick_volume"] if "tick_volume" in row.dtype.names else None
    real = row["real_volume"] if "real_volume" in row.dtype.names else None
    return {
        "timestamp_unix": unix,
        "timestamp_utc": unix_to_utc(unix),
        "open": _num_or_none(row["open"]),
        "high": _num_or_none(row["high"]),
        "low": _num_or_none(row["low"]),
        "close": _num_or_none(row["close"]),
        "tick_volume": _int_or_none(tick),
        "real_volume": _int_or_none(real),
        "spread": _int_or_none(spread),
    }


def unix_to_utc(unix):
    from datetime import datetime, timezone

    return datetime.fromtimestamp(int(unix), tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _num_or_none(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def required_columns():
    return list(BAR_COLUMNS)


def schema_version():
    return SCHEMA_VERSION
