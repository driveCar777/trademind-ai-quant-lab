"""Classify live MT5 symbols from specification/path. Name is last resort."""
from __future__ import print_function


CATEGORIES = ("FX", "Metals", "Energy", "Indices", "Crypto", "Rates", "Other")

SPEC_FIELDS = (
    "name",
    "description",
    "path",
    "currency_base",
    "currency_profit",
    "currency_margin",
    "digits",
    "point",
    "trade_tick_size",
    "trade_tick_value",
    "trade_contract_size",
    "volume_min",
    "volume_max",
    "volume_step",
    "swap_long",
    "swap_short",
    "swap_mode",
    "trade_mode",
    "trade_calc_mode",
    "spread",
    "spread_float",
    "visible",
    "select",
    "custom",
    "category",
    "industry",
    "sector",
    "starting",
    "expiration",
    "basis",
    "page",
)


def spec_dict(info):
    row = {}
    if info is None:
        return row
    if hasattr(info, "_asdict"):
        raw = info._asdict()
        for key, value in raw.items():
            row[key] = _jsonable(value)
        return row
    for name in SPEC_FIELDS:
        if hasattr(info, name):
            row[name] = _jsonable(getattr(info, name))
    return row


def _jsonable(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return str(value)


def classify(spec):
    path = str(spec.get("path") or "").lower().replace("/", "\\")
    desc = str(spec.get("description") or "").lower()
    blob = path + " | " + desc
    reason = "path+description"
    if _has(blob, ("forex", "fx\\", "\\fx\\", "currenc", "majors", "minors", "exotics")):
        return "FX", reason
    if _has(blob, ("metal", "gold", "silver", "xau", "xag", "platinum", "palladium")):
        return "Metals", reason
    if _has(blob, ("energy", "oil", "crude", "brent", "wti", "gas", "xti", "xbr", "xng")):
        return "Energy", reason
    if _has(blob, ("indic", "index", "indices", "dow", "nasdaq", "s&p", "dax", "nikkei", "ftse")):
        return "Indices", reason
    if _has(blob, ("crypto", "bitcoin", "btc", "eth", "ether")):
        return "Crypto", reason
    if _has(blob, ("bond", "yield", "rate", "treasury", "bund")):
        return "Rates", reason
    name = str(spec.get("name") or "").upper()
    if _looks_fx_name(name):
        return "FX", "name_fallback_6letter"
    return "Other", "unmatched_spec"


def _has(blob, needles):
    for item in needles:
        if item in blob:
            return True
    return False


def _looks_fx_name(name):
    compact = "".join(ch for ch in name if ch.isalpha())
    return len(compact) == 6 and compact.isalpha()


def is_equity_cfd(spec):
    name = str(spec.get("name") or "")
    return name.startswith("#")


def is_priority(spec, category):
    if is_equity_cfd(spec):
        return False
    name = str(spec.get("name") or "").upper()
    path = str(spec.get("path") or "").upper()
    tokens = (
        "GOLD",
        "XAU",
        "XAG",
        "SILVER",
        "OIL",
        "XTI",
        "XBR",
        "XNG",
        "BRENT",
        "CRUDE",
        "EURUSD",
        "USDJPY",
        "GBPUSD",
        "USDCHF",
        "AUDUSD",
        "USDCAD",
        "NZDUSD",
        "BTC",
        "NAS",
        "SPX",
        "DJ30",
        "DAX",
        "UK100",
        "JPN225",
        "NDX",
    )
    blob = name + " " + path
    if any(tok in blob for tok in tokens):
        return True
    return category in ("Metals", "Energy", "FX") and not is_equity_cfd(spec)
