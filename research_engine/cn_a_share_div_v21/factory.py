"""BaoStock dividend events. Knowledge time = plan announce (not operate/ex-date)."""
from __future__ import print_function

import json
import os
from datetime import datetime, timezone

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share.universe_daily import load_equities
from research_engine.cn_a_share_div_v21 import DIV_YEAR0, DIV_YEAR1
from research_engine.cn_a_share_div_v21.paths import BASIC_CSV, DIV_CSV, DIV_MAN, DIV_QUAL, DIV_RAW, DIV_REF, OUT, NORMALIZED_COLS, ensure_v21
from research_protocol.hashing import file_sha256


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _consume(rs):
    rows = []
    fields = list(getattr(rs, "fields", []) or [])
    if str(getattr(rs, "error_code", "1")) != "0":
        return rows
    while rs.error_code == "0" and rs.next():
        rows.append(dict(zip(fields, rs.get_row_data())))
    return rows


def parse_float(raw):
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if "或" in text:
        text = text.split("或")[0].strip()
    try:
        return float(text)
    except ValueError:
        return None


def announce_date(raw):
    plan = (raw.get("dividPlanAnnounceDate") or "").strip()
    pre = (raw.get("dividPreNoticeDate") or "").strip()
    if len(plan) == 10:
        return plan
    if len(pre) == 10:
        return pre
    return None


def event_kind(cash, stock, reserve):
    cash_ok = cash is not None and cash > 0
    stock_ok = (stock is not None and stock > 0) or (reserve is not None and reserve > 0)
    if cash_ok and stock_ok:
        return "BOTH"
    if cash_ok:
        return "CASH"
    if stock_ok:
        return "STOCK"
    return None


def _raw_path(symbol):
    return os.path.join(DIV_RAW, symbol.replace(".", "_") + ".json")


def _done_set():
    path = os.path.join(DIV_RAW, "_done.txt")
    if not os.path.isfile(path):
        return set()
    handle = open(path, "r", encoding="utf-8")
    try:
        return set(line.strip() for line in handle if line.strip())
    finally:
        handle.close()


def _mark_done(symbol):
    handle = open(os.path.join(DIV_RAW, "_done.txt"), "a", encoding="utf-8")
    try:
        handle.write(symbol + "\n")
    finally:
        handle.close()


def _year0(listing_date):
    if listing_date and len(listing_date) >= 4 and listing_date[:4].isdigit():
        return max(DIV_YEAR0, int(listing_date[:4]) - 1)
    return DIV_YEAR0


def _year1(delisting_date):
    if delisting_date and len(delisting_date) >= 4 and delisting_date[:4].isdigit():
        return min(DIV_YEAR1, int(delisting_date[:4]) + 1)
    return DIV_YEAR1


def _fetch_symbol(bs, symbol, year0, year1):
    recs = []
    for year in range(year0, year1 + 1):
        raw_rows = _consume(bs.query_dividend_data(code=symbol, year=str(year), yearType="report"))
        recs.append({"year": year, "empty": not raw_rows, "raw": raw_rows})
    return recs


def download_dividends():
    ensure_v21()
    import baostock as bs

    equities = load_equities(BASIC_CSV)
    done = _done_set()
    todo = [e for e in equities if e.get("symbol") and e["symbol"] not in done]
    print("V21_DIV_DL", "done", len(done), "todo", len(todo), flush=True)
    if not todo:
        return {"n_done": len(done), "n_todo": 0}
    login = bs.login()
    if str(login.error_code) != "0":
        raise RuntimeError("BAOSTOCK_LOGIN")
    n_ok = 0
    try:
        for i, eq in enumerate(todo):
            symbol = eq["symbol"]
            y0 = _year0(eq.get("listing_date"))
            y1 = _year1(eq.get("delisting_date"))
            try:
                recs = _fetch_symbol(bs, symbol, y0, y1)
            except Exception as exc:
                print("V21_DIV_FAIL", symbol, str(exc)[:120], flush=True)
                try:
                    bs.logout()
                except Exception:
                    pass
                login = bs.login()
                if str(login.error_code) != "0":
                    print("V21_DIV_RELOGIN_FAIL", flush=True)
                    break
                continue
            dump_json(
                _raw_path(symbol),
                {"symbol": symbol, "retrieved_at": _utc_now(), "immutable": True, "source": "BAOSTOCK_query_dividend_data", "records": recs},
            )
            _mark_done(symbol)
            n_ok += 1
            if (i + 1) % 25 == 0:
                print("V21_DIV_DL", i + 1, "/", len(todo), "ok", n_ok, flush=True)
    finally:
        try:
            bs.logout()
        except Exception:
            pass
    return {"n_done": len(_done_set()), "n_ok": n_ok}


def normalize_dividends():
    ensure_v21()
    rows = []
    n_files = 0
    n_with_announce = 0
    if os.path.isdir(DIV_RAW):
        for name in os.listdir(DIV_RAW):
            if not name.endswith(".json"):
                continue
            n_files += 1
            handle = open(os.path.join(DIV_RAW, name), "r", encoding="utf-8")
            try:
                payload = json.load(handle)
            finally:
                handle.close()
            symbol = payload.get("symbol")
            for rec in payload.get("records") or []:
                for raw in rec.get("raw") or []:
                    ann = announce_date(raw)
                    cash = parse_float(raw.get("dividCashPsBeforeTax"))
                    stock = parse_float(raw.get("dividStocksPs"))
                    reserve = parse_float(raw.get("dividReserveToStockPs"))
                    kind = event_kind(cash, stock, reserve)
                    if not ann or kind is None:
                        continue
                    n_with_announce += 1
                    rows.append(
                        {
                            "symbol": symbol or raw.get("code"),
                            "announce_date": ann,
                            "operate_date": (raw.get("dividOperateDate") or "").strip() or None,
                            "cash_ps": cash,
                            "stock_ps": stock,
                            "reserve_ps": reserve,
                            "kind": kind,
                            "source": "BAOSTOCK_query_dividend_data",
                        }
                    )
    write_csv(DIV_CSV, NORMALIZED_COLS, rows)
    catalog = {
        "n_rows": len(rows),
        "n_files": n_files,
        "n_with_announce": n_with_announce,
        "n_cash": sum(1 for r in rows if r["kind"] in ("CASH", "BOTH")),
        "n_stock": sum(1 for r in rows if r["kind"] in ("STOCK", "BOTH")),
        "n_symbols": len(set(r["symbol"] for r in rows if r.get("symbol"))),
        "download_complete": n_files > 5000,
        "knowledge_time": "dividPlanAnnounceDate else dividPreNoticeDate",
        "operate_date_not_knowledge": True,
        "csv_sha256": file_sha256(DIV_CSV) if os.path.isfile(DIV_CSV) else None,
        "csv": DIV_CSV,
    }
    dump_json(os.path.join(DIV_REF, "DIVIDEND_CATALOG.json"), catalog)
    dump_json(os.path.join(DIV_MAN, "DIVIDEND_NORMALIZE.json"), catalog)
    dump_json(os.path.join(DIV_QUAL, "DIVIDEND_CATALOG.json"), catalog)
    dump_json(os.path.join(OUT, "DIVIDEND_CATALOG.json"), catalog)
    print("V21_DIV_NORM", catalog["n_rows"], catalog["n_files"], flush=True)
    return rows, catalog
