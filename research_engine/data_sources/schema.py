"""Typed observation records. Different sources stay semantically typed."""
from __future__ import print_function

from research_engine.data_sources import FUTURES_FIELDS, OPTION_FIELDS, REQUIRED_FIELDS


class SchemaError(ValueError):
    pass


def _require(row, fields):
    missing = [name for name in fields if name not in row]
    if missing:
        raise SchemaError("missing %s" % ",".join(missing))


def validate_observation(row):
    _require(row, REQUIRED_FIELDS)
    if row.get("knowledge_timestamp_utc") in (None, ""):
        raise SchemaError("knowledge_timestamp_utc required")
    if row.get("timestamp_utc") in (None, ""):
        raise SchemaError("timestamp_utc required")
    return True


def validate_option_row(row):
    validate_observation(row)
    _require(row, OPTION_FIELDS)
    if row.get("record_type") != "option_surface":
        raise SchemaError("option row must be record_type=option_surface")
    return True


def validate_futures_row(row):
    validate_observation(row)
    _require(row, FUTURES_FIELDS)
    if row.get("record_type") != "futures_contract":
        raise SchemaError("futures row must be record_type=futures_contract")
    return True


def validate_macro_row(row):
    validate_observation(row)
    for name in ("event_time", "publication_time", "knowledge_time"):
        if name not in row:
            raise SchemaError("macro missing %s" % name)
    if row.get("field") == "surprise" and row.get("consensus") in (None, ""):
        raise SchemaError("surprise requires consensus; do not fabricate")
    return True
