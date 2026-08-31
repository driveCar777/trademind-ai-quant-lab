"""Download and normalize BaoStock profit rows. Raw is immutable. One session."""
from __future__ import print_function

import csv
import json
import os
from datetime import datetime, timezone

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share.universe_daily import load_equities
from research_engine.cn_a_share_information_v16 import FIN_YEAR0, FIN_YEAR1
from research_engine.cn_a_share_information_v16.financial_schema import NORMALIZED_COLS, normalize_profit_row
from research_engine.cn_a_share_information_v16.paths import (
    BASIC_CSV,
    FIN_MAN,
    FIN_NORM,
    FIN_QUAL,
    FIN_RAW,
    FIN_REF,
    ensure_v16,
)
from research_protocol.hashing import canonical_hash, file_sha256


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _year0(listing_date):
    if listing_date and len(listing_date) >= 4 and listing_date[:4].isdigit():
        return max(FIN_YEAR0, int(listing_date[:4]) - 1)
    return FIN_YEAR0


def symbol_jobs(equities):
    jobs = []
    for e in equities:
        jobs.append(
            {
                "symbol": e["symbol"],
                "listing_date": e.get("listing_date"),
                "delisting_date": e.get("delisting_date"),
                "year0": _year0(e.get("listing_date")),
                "year1": FIN_YEAR1,
            }
        )
    return jobs


def _raw_path(symbol):
    return os.path.join(FIN_RAW, "profit", symbol.replace(".", "_") + ".json")


def _done_set():
    path = os.path.join(FIN_RAW, "profit", "_done.txt")
    if not os.path.isfile(path):
        return set()
    handle = open(path, "r", encoding="utf-8")
    try:
        return set(line.strip() for line in handle if line.strip())
    finally:
        handle.close()


def _mark_done(symbol):
    path = os.path.join(FIN_RAW, "profit", "_done.txt")
    handle = open(path, "a", encoding="utf-8")
    try:
        handle.write(symbol + "\n")
    finally:
        handle.close()


def _consume(rs):
    rows = []
    fields = list(getattr(rs, "fields", []) or [])
    if str(getattr(rs, "error_code", "1")) != "0":
        return rows
    while rs.error_code == "0" and rs.next():
        rows.append(dict(zip(fields, rs.get_row_data())))
    return rows


def download_profit_annual(max_symbols=None, sleep_s=0.0):
    """Annual Q4 only. Quarterly API is audited; not swept for this freeze."""
    ensure_v16()
    import baostock as bs

    equities = load_equities(BASIC_CSV)
    jobs = symbol_jobs(equities)
    if max_symbols:
        jobs = jobs[: int(max_symbols)]
    done = _done_set()
    todo = [j for j in jobs if j["symbol"] not in done]
    print("V16_FIN_DL", "done", len(done), "todo", len(todo), flush=True)
    if not todo:
        return {"n_done": len(done), "n_todo": 0}
    login = bs.login()
    if str(login.error_code) != "0":
        raise RuntimeError("BAOSTOCK_LOGIN")
    n_ok = 0
    n_empty = 0
    try:
        for i, job in enumerate(todo):
            symbol = job["symbol"]
            recs = []
            for year in range(job["year0"], job["year1"] + 1):
                raw_rows = _consume(bs.query_profit_data(code=symbol, year=year, quarter=4))
                raw = raw_rows[0] if raw_rows else None
                recs.append({"year": year, "quarter": 4, "empty": raw is None, "raw": raw})
                if raw is None:
                    n_empty += 1
                else:
                    n_ok += 1
            payload = {
                "symbol": symbol,
                "listing_date": job["listing_date"],
                "retrieved_at": _utc_now(),
                "source": "BAOSTOCK_query_profit_data",
                "immutable": True,
                "records": recs,
            }
            dump_json(_raw_path(symbol), payload, sort_keys=True)
            _mark_done(symbol)
            if i % 25 == 0 or i + 1 == len(todo):
                print("V16_FIN_DL", i + 1, "/", len(todo), symbol, "ok_rows", n_ok, flush=True)
    finally:
        bs.logout()
    return {"n_done": len(_done_set()), "n_ok_rows": n_ok, "n_empty": n_empty}


def normalize_financials():
    ensure_v16()
    profit_dir = os.path.join(FIN_RAW, "profit")
    rows = []
    n_files = 0
    n_empty_files = 0
    for name in sorted(os.listdir(profit_dir)):
        if not name.endswith(".json") or name.startswith("_"):
            continue
        n_files += 1
        handle = open(os.path.join(profit_dir, name), "r", encoding="utf-8")
        try:
            payload = json.load(handle)
        finally:
            handle.close()
        n_rec = 0
        for rec in payload.get("records") or []:
            raw = rec.get("raw")
            if not raw:
                continue
            norm = normalize_profit_row(raw, rec["year"], rec["quarter"])
            if norm is None:
                continue
            rows.append(norm)
            n_rec += 1
        if n_rec == 0:
            n_empty_files += 1
    rows.sort(key=lambda r: (r["symbol"], r["report_period"], r["announcement_date"]))
    csv_path = os.path.join(FIN_NORM, "FINANCIAL_ANNUAL.csv")
    write_csv(csv_path, NORMALIZED_COLS, rows)
    jsonl = os.path.join(FIN_NORM, "FINANCIAL_ANNUAL.jsonl")
    handle = open(jsonl, "w", encoding="utf-8")
    try:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    finally:
        handle.close()
    catalog = {
        "n_files": n_files,
        "n_empty_files": n_empty_files,
        "n_rows": len(rows),
        "n_symbols": len(set(r["symbol"] for r in rows)),
        "n_with_announcement": sum(1 for r in rows if r.get("announcement_date")),
        "n_with_revenue": sum(1 for r in rows if r.get("revenue") is not None),
        "n_with_net_profit": sum(1 for r in rows if r.get("net_profit") is not None),
        "n_with_roe": sum(1 for r in rows if r.get("roe") is not None),
        "n_with_gross_margin": sum(1 for r in rows if r.get("gross_margin") is not None),
        "roa": "UNAVAILABLE",
        "debt_ratio": "UNAVAILABLE",
        "eps_kind": "VENDOR_TTM",
        "period": "ANNUAL_Q4",
        "quarterly_downloaded": False,
        "ttm_constructed": False,
        "restatement_risk": True,
        "csv": csv_path,
        "csv_sha256": file_sha256(csv_path),
        "jsonl_sha256": file_sha256(jsonl),
    }
    catalog["announcement_rate"] = (float(catalog["n_with_announcement"]) / catalog["n_rows"]) if catalog["n_rows"] else 0.0
    dump_json(os.path.join(FIN_REF, "FINANCIAL_CATALOG.json"), catalog)
    dump_json(os.path.join(FIN_MAN, "FINANCIAL_NORMALIZE.json"), {"n_rows": catalog["n_rows"], "csv_sha256": catalog["csv_sha256"]})
    dump_json(os.path.join(FIN_QUAL, "FINANCIAL_CATALOG.json"), catalog)
    print("V16_FIN_NORM", catalog["n_rows"], catalog["n_symbols"], catalog["announcement_rate"], flush=True)
    return rows, catalog


def load_normalized_rows():
    path = os.path.join(FIN_NORM, "FINANCIAL_ANNUAL.csv")
    handle = open(path, "r", encoding="utf-8")
    try:
        out = []
        for row in csv.DictReader(handle):
            for key in ("revenue", "net_profit", "eps", "roe", "roa", "debt_ratio", "gross_margin", "np_margin"):
                v = row.get(key)
                if v in ("", None):
                    row[key] = None
                else:
                    row[key] = float(v)
            row["year"] = int(row["year"])
            row["quarter"] = int(row["quarter"])
            row["restatement_risk"] = str(row.get("restatement_risk")).lower() == "true"
            out.append(row)
        return out
    finally:
        handle.close()
