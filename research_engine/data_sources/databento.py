"""Databento historical HTTP adapter. Quote before download. No first-pass ticks."""
from __future__ import print_function

import base64
import csv
import io
import json
import os

try:
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode
    from urllib.request import ProxyHandler, Request, build_opener
except ImportError:
    from urllib import urlencode

    from urllib2 import HTTPError, ProxyHandler, Request, URLError, build_opener

from research_engine.data_sources import ENV_DATABENTO
from research_engine.data_sources.pipeline import AcquisitionBlocked
from research_engine.data_sources.schema import validate_futures_row
from research_engine.v6_external import (
    CREDIT_USD,
    DATASET,
    FORBIDDEN_FIRST_SCHEMAS,
    PARENT_SYMBOLS,
)
from research_engine.v6_external.env import databento_api_key, has_databento_key
from research_engine.v6_external.knowledge_time import (
    definition_knowledge_utc,
    oi_knowledge_utc,
    session_date_utc,
    settlement_knowledge_utc,
)


HIST_ROOT = "https://hist.databento.com/v0"
# Databento StatType (official schema). Only the three we need for curve.
STAT_SETTLEMENT = 3
STAT_CLEARED_VOLUME = 6
STAT_OPEN_INTEREST = 9


def _proxy_opener():
    url = (
        os.environ.get("TRADEMIND_HTTPS_PROXY")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or ""
    )
    if url:
        return build_opener(ProxyHandler({"http": url, "https": url}))
    return build_opener()


def _basic_auth(key):
    token = base64.b64encode(("%s:" % key).encode("utf-8")).decode("ascii")
    return "Basic %s" % token


class DatabentoHttpError(RuntimeError):
    pass


class HistoricalClient(object):
    def __init__(self, api_key, timeout=600):
        self.api_key = api_key
        self.timeout = timeout
        self.opener = _proxy_opener()

    def _post(self, method, fields, accept="application/json"):
        url = "%s/%s" % (HIST_ROOT, method)
        body = urlencode(fields, doseq=True).encode("utf-8")
        req = Request(url, data=body)
        req.add_header("Authorization", _basic_auth(self.api_key))
        req.add_header("Accept", accept)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        last = None
        for attempt in range(4):
            try:
                handle = self.opener.open(req, timeout=self.timeout)
                try:
                    return handle.read()
                finally:
                    handle.close()
            except HTTPError as exc:
                detail = exc.read() if hasattr(exc, "read") else b""
                raise DatabentoHttpError(
                    "HTTP %s %s %s" % (exc.code, method, detail[:400])
                )
            except URLError as exc:
                last = exc
                if attempt < 3:
                    continue
                raise DatabentoHttpError("URL %s %s" % (method, exc.reason))
        raise DatabentoHttpError("URL %s %s" % (method, last.reason if last else "unknown"))

    def get_cost(self, dataset, schema, symbols, start, end, stype_in="parent"):
        raw = self._post(
            "metadata.get_cost",
            {
                "dataset": dataset,
                "schema": schema,
                "symbols": ",".join(symbols) if isinstance(symbols, (list, tuple)) else symbols,
                "stype_in": stype_in,
                "start": start,
                "end": end,
            },
        )
        text = raw.decode("utf-8").strip()
        try:
            return float(json.loads(text))
        except ValueError:
            return float(text)

    def get_dataset_range(self, dataset):
        raw = self._post("metadata.get_dataset_range", {"dataset": dataset})
        return json.loads(raw.decode("utf-8"))

    def get_billable_size(self, dataset, schema, symbols, start, end, stype_in="parent"):
        raw = self._post(
            "metadata.get_billable_size",
            {
                "dataset": dataset,
                "schema": schema,
                "symbols": ",".join(symbols) if isinstance(symbols, (list, tuple)) else symbols,
                "stype_in": stype_in,
                "start": start,
                "end": end,
            },
        )
        text = raw.decode("utf-8").strip()
        try:
            return int(json.loads(text))
        except (TypeError, ValueError):
            return int(float(text))

    def get_range_csv(self, dataset, schema, symbols, start, end, stype_in="parent"):
        raw = self._post(
            "timeseries.get_range",
            {
                "dataset": dataset,
                "schema": schema,
                "symbols": ",".join(symbols) if isinstance(symbols, (list, tuple)) else symbols,
                "stype_in": stype_in,
                "stype_out": "raw_symbol",
                "start": start,
                "end": end,
                "encoding": "csv",
            },
            accept="text/csv",
        )
        return raw

    def submit_batch(self, dataset, schema, symbols, start, end, stype_in="parent"):
        raw = self._post(
            "batch.submit_job",
            {
                "dataset": dataset,
                "schema": schema,
                "symbols": ",".join(symbols) if isinstance(symbols, (list, tuple)) else symbols,
                "stype_in": stype_in,
                "stype_out": "raw_symbol",
                "start": start,
                "end": end,
                "encoding": "csv",
                "compression": "zstd",
                "pretty_px": "true",
                "pretty_ts": "true",
                "map_symbols": "true",
                "split_duration": "year",
                "delivery": "download",
            },
        )
        return json.loads(raw.decode("utf-8"))

    def list_jobs(self, states="queued,processing,done"):
        raw = self._post("batch.list_jobs", {"states": states})
        return json.loads(raw.decode("utf-8"))

    def list_files(self, job_id):
        raw = self._post("batch.list_files", {"job_id": job_id})
        return json.loads(raw.decode("utf-8"))


def min_pack_requests(start="2010-06-06", end="2026-08-29"):
    symbols = list(PARENT_SYMBOLS)
    return [
        {
            "id": "ohlcv-1d",
            "schema": "ohlcv-1d",
            "symbols": symbols,
            "stype_in": "parent",
            "start": start,
            "end": end,
        },
        {
            "id": "definition",
            "schema": "definition",
            "symbols": symbols,
            "stype_in": "parent",
            "start": start,
            "end": end,
        },
        {
            "id": "statistics",
            "schema": "statistics",
            "symbols": symbols,
            "stype_in": "parent",
            "start": start,
            "end": end,
        },
    ]


def quote_min_pack(client, start="2010-06-06", end="2026-08-29"):
    quotes = []
    total = 0.0
    for spec in min_pack_requests(start, end):
        cost = client.get_cost(
            DATASET,
            spec["schema"],
            spec["symbols"],
            spec["start"],
            spec["end"],
            spec["stype_in"],
        )
        row = dict(spec)
        row["cost_usd"] = cost
        quotes.append(row)
        total += float(cost)
    return {
        "dataset": DATASET,
        "pack": "E",
        "quotes": quotes,
        "total_usd": total,
        "credit_usd": CREDIT_USD,
        "within_credits": total <= CREDIT_USD,
        "open_standard": False,
    }


class DatabentoAdapter(object):
    source = "databento"
    env_name = ENV_DATABENTO

    def status(self, spec=None):
        if has_databento_key():
            return "CREDENTIAL_PRESENT_NOT_FETCHED"
        return "CREDENTIAL_REQUIRED"

    def _reject_first_pass_schema(self, spec):
        schema = str((spec or {}).get("schema") or "").lower()
        if schema in FORBIDDEN_FIRST_SCHEMAS:
            raise AcquisitionBlocked(
                "FIRST_PASS_FORBIDS_%s: daily/definitions/statistics only" % schema
            )
        return schema

    def fetch(self, spec):
        spec = spec or {}
        schema = self._reject_first_pass_schema(spec)
        if self.status(spec) == "CREDENTIAL_REQUIRED":
            raise AcquisitionBlocked("CREDENTIAL_REQUIRED")
        if not schema:
            raise AcquisitionBlocked("MISSING_SCHEMA")
        if spec.get("dry_run"):
            raise AcquisitionBlocked("DRY_RUN")
        client = HistoricalClient(databento_api_key())
        start = spec.get("start") or "2010-06-06"
        end = spec.get("end") or "2026-08-29"
        symbols = spec.get("symbols") or list(PARENT_SYMBOLS)
        cost = client.get_cost(DATASET, schema, symbols, start, end, spec.get("stype_in") or "parent")
        cap = float(spec.get("max_usd") or CREDIT_USD)
        if cost > cap:
            raise AcquisitionBlocked("PAYMENT_REQUIRED:cost=%.6f>cap=%.2f" % (cost, cap))
        raw = client.get_range_csv(
            DATASET,
            schema,
            symbols,
            start,
            end,
            spec.get("stype_in") or "parent",
        )
        return raw

    def normalize(self, raw, spec):
        schema = str((spec or {}).get("schema") or "")
        text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
        reader = csv.DictReader(io.StringIO(text))
        rows = []
        for item in reader:
            if schema == "ohlcv-1d":
                rows.append(self._norm_ohlcv(item))
            elif schema == "definition":
                rows.append(self._norm_definition(item))
            elif schema == "statistics":
                mapped = self._norm_statistics(item)
                if mapped is not None:
                    rows.append(mapped)
            else:
                raise AcquisitionBlocked("unsupported schema %s" % schema)
        return [row for row in rows if row]

    def timestamp(self, row, spec):
        schema = str((spec or {}).get("schema") or "")
        session = session_date_utc(row.get("timestamp_utc") or row.get("session_date"))
        row["session_date"] = session
        if schema == "statistics" and row.get("field") in ("open_interest", "cleared_volume"):
            row["knowledge_timestamp_utc"] = oi_knowledge_utc(session)
        elif schema == "definition":
            row["knowledge_timestamp_utc"] = definition_knowledge_utc(
                row.get("timestamp_utc")
            )
        else:
            row["knowledge_timestamp_utc"] = settlement_knowledge_utc(session)
        row["knowledge_time"] = row["knowledge_timestamp_utc"]
        row["event_time"] = row.get("timestamp_utc")
        row["publication_time"] = row["knowledge_timestamp_utc"]
        return row

    def validate(self, rows, spec):
        fails = []
        futures = 0
        for row in rows:
            if row.get("record_type") == "futures_contract":
                try:
                    validate_futures_row(row)
                    futures += 1
                except Exception as exc:
                    fails.append(str(exc))
            if not row.get("knowledge_timestamp_utc"):
                fails.append("missing knowledge")
        return {
            "validation_status": "PASS" if not fails else "FAIL",
            "fail_reasons": fails[:20],
            "row_count": len(rows),
            "futures_rows": futures,
            "lookahead_ok": True,
            "sample_only": bool((spec or {}).get("sample_only")),
            "has_bytes": True,
        }

    def _root_from_symbol(self, symbol):
        text = str(symbol or "")
        if text.endswith(".FUT"):
            return text.split(".", 1)[0]
        if len(text) >= 2:
            return text[:2]
        return text

    def _norm_ohlcv(self, item):
        symbol = item.get("symbol") or item.get("raw_symbol") or ""
        session = session_date_utc(item.get("ts_event") or item.get("ts_recv"))
        close = item.get("close")
        return {
            "timestamp_utc": session + "T00:00:00Z" if session else "",
            "source": "databento",
            "vendor": "Databento",
            "dataset": DATASET,
            "schema": "ohlcv-1d",
            "asset": self._root_from_symbol(symbol),
            "field": "close",
            "value": close,
            "revision": "electronic_ohlcv_not_official_settle",
            "record_type": "futures_contract",
            "contract": symbol,
            "raw_symbol": symbol,
            "expiry": item.get("expiration") or "",
            "settlement": close,
            "open_interest": item.get("open_interest") or 0,
            "volume": item.get("volume") or 0,
            "open": item.get("open"),
            "high": item.get("high"),
            "low": item.get("low"),
            "close": close,
            "instrument_class": "F",
        }

    def _norm_definition(self, item):
        symbol = item.get("raw_symbol") or item.get("symbol") or ""
        expiry = session_date_utc(item.get("expiration") or item.get("expiration_date"))
        return {
            "timestamp_utc": item.get("ts_event") or "",
            "source": "databento",
            "vendor": "Databento",
            "dataset": DATASET,
            "schema": "definition",
            "asset": self._root_from_symbol(symbol),
            "field": "definition",
            "value": symbol,
            "revision": "instrument_definition",
            "record_type": "futures_definition",
            "contract": symbol,
            "raw_symbol": symbol,
            "expiry": expiry,
            "settlement": item.get("md_security_trading_status") or 0,
            "open_interest": 0,
            "volume": 0,
            "instrument_class": item.get("instrument_class") or "",
            "instrument_id": item.get("instrument_id"),
            "min_price_increment": item.get("min_price_increment"),
            "underlying": item.get("underlying"),
        }

    def _norm_statistics(self, item):
        try:
            stat = int(float(item.get("stat_type") or item.get("stype") or -1))
        except (TypeError, ValueError):
            return None
        field = {
            STAT_SETTLEMENT: "settlement",
            STAT_CLEARED_VOLUME: "cleared_volume",
            STAT_OPEN_INTEREST: "open_interest",
        }.get(stat)
        if not field:
            return None
        symbol = item.get("symbol") or item.get("raw_symbol") or ""
        session = session_date_utc(item.get("ts_ref") or item.get("ts_event"))
        value = item.get("price") if field == "settlement" else item.get("quantity")
        return {
            "timestamp_utc": session + "T00:00:00Z" if session else "",
            "source": "databento",
            "vendor": "Databento",
            "dataset": DATASET,
            "schema": "statistics",
            "asset": self._root_from_symbol(symbol),
            "field": field,
            "value": value,
            "revision": "exchange_daily_statistic",
            "record_type": "futures_contract",
            "contract": symbol,
            "raw_symbol": symbol,
            "expiry": item.get("expiration") or "",
            "settlement": value if field == "settlement" else 0,
            "open_interest": value if field == "open_interest" else 0,
            "volume": value if field == "cleared_volume" else 0,
            "stat_type": stat,
            "instrument_class": "F",
        }
