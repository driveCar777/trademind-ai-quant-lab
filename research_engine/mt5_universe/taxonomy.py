"""Path-first taxonomy. CFD is not futures. Name is last resort."""
from __future__ import print_function

import re

CLASS_FROM_ROOT = {
    "FOREX": "FX",
    "FX": "FX",
    "METALS": "METAL",
    "METAL": "METAL",
    "ENERGY": "ENERGY",
    "ENERGIES": "ENERGY",
    "INDICES": "INDEX",
    "INDEX": "INDEX",
    "CRYPTO": "CRYPTO",
    "CRYPTOCURRENCIES": "CRYPTO",
    "RATES": "RATE",
    "BONDS": "BOND",
    "BOND": "BOND",
    "CFD-STOCKS": "STOCK",
    "CFD-SHARES": "STOCK",
    "CFD-ENERGIES": "ENERGY",
    "CFD-AGRICULTURAL": "OTHER",
    "CFD-METALS": "METAL",
    "CFD-INDICES": "INDEX",
    "CFD-BONDS": "BOND",
    "INTERNAL": "FX",
    "CFD-ETFS": "ETF",
    "CFD-ETF": "ETF",
    "STOCKS": "STOCK",
    "SHARES": "STOCK",
    "ETFS": "ETF",
    "ETF": "ETF",
    "FUTURES": "FUTURE",
    "FUTURE": "FUTURE",
    "OPTIONS": "OPTION",
    "OPTION": "OPTION",
    "COMMODITIES": "OTHER",
}

UNDERLYING_ALIASES = {
    "XAUUSD": "GOLD",
    "GOLD": "GOLD",
    "GOLDFUTURE": "GOLD",
    "XAGUSD": "SILVER",
    "SILVER": "SILVER",
    "SIFUTURE": "SILVER",
    "XPTUSD": "PLATINUM",
    "PLATINUM": "PLATINUM",
    "XPDUSD": "PALLADIUM",
    "PALLADIUM": "PALLADIUM",
    "XTIUSD": "WTI",
    "CRUDEOIL": "WTI",
    "WTI": "WTI",
    "WTICRUDE": "WTI",
    "XBRUSD": "BRENT",
    "BRENT": "BRENT",
    "BRENTOIL": "BRENT",
    "UKOIL": "BRENT",
    "XNGUSD": "NATGAS",
    "NATGAS": "NATGAS",
    "NATURALGAS": "NATGAS",
    "US500": "US500",
    "US_500": "US500",
    "SPX500": "US500",
    "US100": "US100",
    "US_100": "US100",
    "US_TECH100": "US100",
    "USTEC": "US100",
    "NAS100": "US100",
    "US30": "US30",
    "US_30": "US30",
    "DJ30": "US30",
    "GER40": "GER40",
    "GERMANY40": "GER40",
    "GERMANY_40": "GER40",
    "UK100": "UK100",
    "UK_100": "UK100",
    "JP225": "JP225",
    "JAPAN225": "JP225",
    "JAPAN_225": "JP225",
    "BTCUSD": "BTC",
    "BITCOIN": "BTC",
    "ETHUSD": "ETH",
    "ETHEREUM": "ETH",
}


def path_parts(path):
    text = str(path or "").replace("/", "\\")
    return [p for p in text.split("\\") if p]


def path_root(path):
    parts = path_parts(path)
    return parts[0].upper() if parts else ""


def asset_class_from_path(path, name=""):
    root = path_root(path)
    mapped = CLASS_FROM_ROOT.get(root)
    if mapped:
        return mapped
    blob = (str(path or "") + " " + str(name or "")).upper()
    if "FOREX" in blob or blob.startswith("FX"):
        return "FX"
    if "METAL" in blob:
        return "METAL"
    if "ENERGY" in blob or "OIL" in blob or "BRENT" in blob:
        return "ENERGY"
    if "INDIC" in blob or "INDEX" in blob:
        return "INDEX"
    if "CRYPTO" in blob:
        return "CRYPTO"
    if "BOND" in blob or "TREASUR" in blob:
        return "BOND"
    if "ETF" in blob:
        return "ETF"
    if "STOCK" in blob or "SHARE" in blob:
        return "STOCK"
    return "OTHER"


def instrument_type_from_spec(spec):
    path = str(spec.get("path") or "")
    name = str(spec.get("name") or "")
    desc = str(spec.get("description") or "").lower()
    root = path_root(path)
    option_mode = spec.get("option_mode") or 0
    strike = spec.get("option_strike") or 0
    exp = spec.get("expiration") or spec.get("expiration_time") or 0
    try:
        exp_i = int(exp)
    except Exception:
        exp_i = 0
    try:
        strike_f = float(strike)
    except Exception:
        strike_f = 0.0
    if int(option_mode or 0) or strike_f > 0 or "option" in desc or root in ("OPTIONS", "OPTION"):
        return "OPTION"
    if exp_i > 0 or root in ("FUTURES", "FUTURE"):
        return "FUTURE"
    if root in ("CFD-STOCKS", "STOCKS", "SHARES") or name.startswith("#") or name.startswith("_"):
        if "ETF" in root or "etf" in desc:
            return "CFD"
        return "CFD"
    if root in ("CFD-ETFS", "CFD-ETF", "ETFS", "ETF"):
        return "CFD"
    return "CFD"


def _strip_listing(name):
    text = str(name or "").strip()
    text = text.replace("#", "")
    if text.startswith("_"):
        text = text[1:]
    text = re.sub(r"\.(raw|a|b|pro|ecn|m|mini)$", "", text, flags=re.I)
    text = re.sub(r"[-_](USD|EUR|GBP|JPY|CHF|AUD|CAD|NZD)$", "", text, flags=re.I)
    text = re.sub(r"\.(US|UK|DE|FR|IT|JP|HK|AU|CA)$", "", text, flags=re.I)
    return text.upper()


def _isin_usable(isin, name):
    text = str(isin or "").strip().upper()
    if len(text) != 12 or not text.isalnum():
        return False
    dummy = ("US4642866739", "US4642867729")
    if text in dummy:
        return False
    return True


def economic_underlying(spec):
    name = str(spec.get("name") or "")
    path = str(spec.get("path") or "")
    stripped = _strip_listing(name)
    compact = re.sub(r"[^A-Z0-9]", "", stripped)
    if compact in UNDERLYING_ALIASES:
        return UNDERLYING_ALIASES[compact]
    parts = path_parts(path)
    if len(parts) >= 2:
        leaf = _strip_listing(parts[-1])
        leaf_c = re.sub(r"[^A-Z0-9]", "", leaf)
        if leaf_c in UNDERLYING_ALIASES:
            return UNDERLYING_ALIASES[leaf_c]
    isin = str(spec.get("isin") or "").strip()
    if _isin_usable(isin, name):
        return "ISIN:" + isin.upper()
    if stripped:
        return stripped
    return name or "UNKNOWN"


def listing_kind(name):
    text = str(name or "")
    if text.startswith("#"):
        return "HASH_CFD"
    if text.startswith("_"):
        return "UNDERSCORE_CFD"
    if re.search(r"\.(raw|a|b|pro|ecn)$", text, re.I):
        return "SUFFIX_VARIANT"
    if re.search(r"[-_](USD|EUR|GBP)$", text, re.I):
        return "CURRENCY_VARIANT"
    return "PRIMARY"


def classify_row(spec):
    name = spec.get("name") or spec.get("symbol") or ""
    path = spec.get("path") or (spec.get("meta") or {}).get("path")
    if spec.get("meta") and not spec.get("path"):
        meta = spec.get("meta") or {}
        merged = dict(meta)
        merged["name"] = name or meta.get("name")
        spec = merged
        path = spec.get("path")
        name = spec.get("name") or name
    asset_class = asset_class_from_path(path, name)
    itype = instrument_type_from_spec(spec)
    underlying = economic_underlying(spec)
    return {
        "symbol": name,
        "asset_class": asset_class,
        "instrument_type": itype,
        "economic_underlying": underlying,
        "broker_instrument": itype,
        "listing_kind": listing_kind(name),
        "path": path,
        "path_root": path_root(path),
        "isin": spec.get("isin") or "",
        "description": spec.get("description") or "",
        "currency_base": spec.get("currency_base"),
        "currency_profit": spec.get("currency_profit"),
        "expiration": spec.get("expiration") or spec.get("expiration_time") or 0,
        "option_mode": spec.get("option_mode") or 0,
        "option_strike": spec.get("option_strike") or 0,
        "trade_mode": spec.get("trade_mode"),
        "visible": spec.get("visible"),
    }
