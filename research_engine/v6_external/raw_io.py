"""Stream Databento Pack E year-split CSV. Never load the raw dump into RAM."""
from __future__ import print_function

import csv
import io
import os
import re

from research_engine.data_expansion.paths import repo_root
from research_engine.v6_external.knowledge_time import session_date_utc


ROOTS = ("GC", "CL")
OUTRIGHT_RE = re.compile(r"^(GC|CL)[FGHJKMNQUVXZ][0-9]{1,2}$")
SKIP_NAMES = ("manifest.json", "condition.json", "metadata.json")
STAT_SETTLEMENT = 3
STAT_CLEARED_VOLUME = 6
STAT_OPEN_INTEREST = 9


def pack_e_root():
    return os.path.join(repo_root(), "data", "market", "raw", "databento", "pack_e")


def list_data_files(job_dir):
    if not os.path.isdir(job_dir):
        return []
    out = []
    for name in sorted(os.listdir(job_dir)):
        if name in SKIP_NAMES or name.endswith(".part"):
            continue
        path = os.path.join(job_dir, name)
        if os.path.isfile(path) and (
            name.endswith(".csv.zst") or name.endswith(".csv")
        ):
            out.append(path)
    return out


def _open_text(path):
    handle = open(path, "rb")
    if path.endswith(".zst"):
        import zstandard as zstd

        reader = zstd.ZstdDecompressor().stream_reader(handle)
        return io.TextIOWrapper(reader, encoding="utf-8", newline=""), handle
    return io.TextIOWrapper(handle, encoding="utf-8", newline=""), handle


def iter_csv(path):
    text, raw = _open_text(path)
    try:
        reader = csv.DictReader(text)
        for row in reader:
            yield row
    finally:
        try:
            text.close()
        except Exception:
            pass
        raw.close()


def is_outright_symbol(symbol):
    name = str(symbol or "").strip().upper()
    if ":" in name or "-" in name:
        return False
    return bool(OUTRIGHT_RE.match(name))


def root_of(symbol):
    name = str(symbol or "").strip().upper()
    if name.endswith(".FUT"):
        return name.split(".", 1)[0]
    if len(name) >= 2 and name[:2] in ROOTS:
        return name[:2]
    return ""


def instrument_class_ok(value):
    text = str(value or "").strip().upper()
    return text in ("F", "FUTURE", "")


def parse_stat_type(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value):
    number = _as_float(value)
    if number is None:
        return None
    return int(number)


def load_outright_definitions(paths):
    """instrument_id / raw_symbol -> latest outright definition."""
    by_id = {}
    by_symbol = {}
    n_all = 0
    n_outright = 0
    classes = {}
    for path in paths:
        for row in iter_csv(path):
            n_all += 1
            klass = str(row.get("instrument_class") or "").strip()
            classes[klass] = classes.get(klass, 0) + 1
            symbol = (row.get("raw_symbol") or row.get("symbol") or "").strip()
            if not instrument_class_ok(klass) or not is_outright_symbol(symbol):
                continue
            n_outright += 1
            item = {
                "raw_symbol": symbol,
                "root": root_of(symbol),
                "expiry": session_date_utc(row.get("expiration") or row.get("expiration_date")),
                "instrument_class": "F",
                "instrument_id": str(row.get("instrument_id") or ""),
                "min_price_increment": row.get("min_price_increment"),
            }
            if item["instrument_id"]:
                by_id[item["instrument_id"]] = item
            by_symbol[symbol] = item
    return {
        "by_id": by_id,
        "by_symbol": by_symbol,
        "n_definition_rows": n_all,
        "n_outright": n_outright,
        "instrument_class_counts": classes,
    }


def load_ohlcv(paths, allowed_symbols=None):
    bars = {}
    n_all = 0
    n_keep = 0
    for path in paths:
        for row in iter_csv(path):
            n_all += 1
            symbol = (row.get("symbol") or row.get("raw_symbol") or "").strip()
            if allowed_symbols is not None:
                if symbol not in allowed_symbols:
                    continue
            elif not is_outright_symbol(symbol):
                continue
            session = session_date_utc(row.get("ts_event") or row.get("ts_recv"))
            if not session:
                continue
            n_keep += 1
            bars.setdefault(symbol, {})[session] = {
                "open": _as_float(row.get("open")),
                "high": _as_float(row.get("high")),
                "low": _as_float(row.get("low")),
                "close": _as_float(row.get("close")),
                "volume": _as_int(row.get("volume")),
                "instrument_id": str(row.get("instrument_id") or ""),
            }
    return {"bars": bars, "n_ohlcv_rows": n_all, "n_ohlcv_outright": n_keep}


def load_statistics(paths, allowed_symbols=None, allowed_ids=None):
    stats = {}
    n_all = 0
    n_keep = 0
    by_type = {STAT_SETTLEMENT: 0, STAT_CLEARED_VOLUME: 0, STAT_OPEN_INTEREST: 0}
    for path in paths:
        for row in iter_csv(path):
            n_all += 1
            stype = parse_stat_type(row.get("stat_type") or row.get("stype"))
            if stype not in by_type:
                continue
            symbol = (row.get("symbol") or row.get("raw_symbol") or "").strip()
            iid = str(row.get("instrument_id") or "")
            allowed = False
            if allowed_symbols is not None and symbol in allowed_symbols:
                allowed = True
            if allowed_ids is not None and iid in allowed_ids:
                allowed = True
            if allowed_symbols is None and allowed_ids is None:
                allowed = is_outright_symbol(symbol)
            if not allowed:
                continue
            session = session_date_utc(row.get("ts_ref") or row.get("ts_event"))
            if not session:
                continue
            n_keep += 1
            by_type[stype] += 1
            slot = stats.setdefault(symbol, {}).setdefault(
                session, {"settlement": None, "cleared_volume": None, "open_interest": None}
            )
            if stype == STAT_SETTLEMENT:
                slot["settlement"] = _as_float(row.get("price"))
            elif stype == STAT_CLEARED_VOLUME:
                slot["cleared_volume"] = _as_int(row.get("quantity"))
            else:
                slot["open_interest"] = _as_int(row.get("quantity"))
    return {
        "stats": stats,
        "n_statistics_rows": n_all,
        "n_statistics_keep": n_keep,
        "n_settlement": by_type[STAT_SETTLEMENT],
        "n_cleared_volume": by_type[STAT_CLEARED_VOLUME],
        "n_open_interest": by_type[STAT_OPEN_INTEREST],
    }
