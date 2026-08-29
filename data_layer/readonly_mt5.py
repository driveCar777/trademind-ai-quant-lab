"""Read-only MT5 facade. Trade execution APIs raise DATA_LAYER_READ_ONLY."""

import os

from data_layer.constants import MT5_ALLOWED, MT5_FORBIDDEN
from data_layer.errors import DataLayerReadOnlyError, Mt5UnavailableError


def _is_forbidden(name):
    if name in MT5_FORBIDDEN:
        return True
    if name.startswith("order_") and name not in MT5_ALLOWED:
        return True
    if name in ("buy", "sell"):
        return True
    return False


class ReadOnlyMT5(object):
    """Proxy that only exposes market-data calls and TIMEFRAME_* constants."""

    def __init__(self, mt5_module):
        object.__setattr__(self, "_mt5", mt5_module)

    def __getattr__(self, name):
        if _is_forbidden(name):
            raise DataLayerReadOnlyError(name)
        if name.startswith("TIMEFRAME_") or name.startswith("COPY_TICKS_"):
            return getattr(self._mt5, name)
        if name not in MT5_ALLOWED:
            raise DataLayerReadOnlyError(name)
        return getattr(self._mt5, name)

    def __setattr__(self, name, value):
        raise DataLayerReadOnlyError("setattr")


def import_readonly_mt5():
    try:
        import MetaTrader5 as mt5
    except Exception as exc:
        raise Mt5UnavailableError("MetaTrader5 package is not installed: %s" % exc)
    return ReadOnlyMT5(mt5), getattr(mt5, "__version__", None)


def initialize_readonly(mt5, terminal_path=None):
    from research_engine.local_fs import force_project_temp

    force_project_temp()
    if os.environ.get("TEMP", "").upper().startswith("C:\\"):
        raise RuntimeError("TEMP_MUST_BE_ON_D")
    if terminal_path:
        ok = mt5.initialize(path=terminal_path)
    else:
        ok = mt5.initialize()
    if not ok:
        err = None
        try:
            err = mt5.last_error()
        except Exception:
            err = "last_error unavailable"
        raise Mt5UnavailableError("MT5 initialize failed: %s" % (err,))
    return True
