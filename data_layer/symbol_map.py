"""Discover the live MT5 symbol for a logical instrument. Do not assume XAUUSD."""

from data_layer.constants import DEFAULT_ALIASES, LOGICAL_SYMBOLS


def normalize_logical(name):
    text = (name or "").strip().upper()
    aliases = {
        "GOLD": "GOLD",
        "XAU": "GOLD",
        "XAUUSD": "GOLD",
        "EURUSD": "EURUSD",
        "USDJPY": "USDJPY",
        "OIL": "OIL",
        "CRUDE": "OIL",
        "WTI": "OIL",
        "XTIUSD": "OIL",
        "USOIL": "OIL",
        "CRUDEOIL": "OIL",
    }
    if text not in aliases:
        raise ValueError("unsupported logical symbol: %s" % name)
    return aliases[text]


def _norm(name):
    return (name or "").upper().replace(" ", "").replace("_", "")


def _reject(name):
    n = _norm(name)
    if not n or n.startswith("#"):
        return True
    for bad in ("FUTURE", "TEST", "HEATING", "SHARE", "BARRICK"):
        if bad in n:
            return True
    return False


def _scan_match(logical, name):
    if _reject(name):
        return False
    n = _norm(name)
    if logical == "GOLD":
        return n == "GOLD" or n.startswith("XAUUSD")
    if logical == "EURUSD":
        return n == "EURUSD" or n.startswith("EURUSD")
    if logical == "USDJPY":
        return n == "USDJPY" or n.startswith("USDJPY")
    if logical == "OIL":
        return n in (
            "CRUDEOIL",
            "WTICRUDE",
            "XTIUSD",
            "USOIL",
            "CRUDE",
            "WTICOUSD",
            "BRENTOIL",
        ) or n.startswith("XTIUSD") or n.startswith("USOIL")
    return False


def _alias_list(logical, config_aliases):
    if config_aliases and logical in config_aliases:
        return list(config_aliases[logical])
    return list(DEFAULT_ALIASES.get(logical, ()))


def resolve_symbol(mt5, logical, config_aliases=None):
    """Return (logical_symbol, mt5_symbol) from the live terminal."""
    logical = normalize_logical(logical)
    names = []
    symbols = mt5.symbols_get()
    if symbols:
        names = [getattr(item, "name", "") for item in symbols]

    for alias in _alias_list(logical, config_aliases):
        if alias in names:
            info = mt5.symbol_info(alias)
            if info is not None:
                mt5.symbol_select(alias, True)
                return logical, alias

    for name in names:
        if _scan_match(logical, name):
            info = mt5.symbol_info(name)
            if info is not None:
                mt5.symbol_select(name, True)
                return logical, name

    raise ValueError("no live MT5 symbol for logical %s" % logical)


def supported_logicals():
    return LOGICAL_SYMBOLS
