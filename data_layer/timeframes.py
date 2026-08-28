"""Map logical timeframes to official MT5 TIMEFRAME_* constants."""

from data_layer.constants import ALLOWED_TIMEFRAMES, TIMEFRAME_MINUTES


_ATTR = {
    "M15": "TIMEFRAME_M15",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1",
}


def normalize_timeframe(name):
    text = (name or "").strip().upper()
    if text not in ALLOWED_TIMEFRAMES:
        raise ValueError("unsupported timeframe: %s" % name)
    return text


def timeframe_minutes(name):
    return TIMEFRAME_MINUTES[normalize_timeframe(name)]


def mt5_timeframe(mt5, name):
    """Resolve via mt5.TIMEFRAME_* — never a raw integer constant."""
    attr = _ATTR[normalize_timeframe(name)]
    value = getattr(mt5, attr)
    if value is None:
        raise ValueError("MT5 missing %s" % attr)
    return value
