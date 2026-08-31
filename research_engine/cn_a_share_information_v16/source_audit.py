"""Live free-source audit. No key. No purchase. One BaoStock login. No retry storm."""
from __future__ import print_function

import inspect
import os
import time
import traceback

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share.pit import knowledge_ok, visible_financials
from research_engine.cn_a_share_information_v16 import (
    CANONICAL_SOURCE,
    NEW_PURCHASE,
    PIT_ASOF,
    PIT_HIDDEN_ANN,
    PIT_HIDDEN_PERIOD,
    PIT_VISIBLE_PERIOD,
    SECONDARY_SOURCE,
)
from research_engine.cn_a_share_information_v16.paths import OUT, TMP, ensure_v16


SAMPLES = ("sh.600519", "sz.000001", "sh.600000")


def _sig(fn):
    try:
        return str(inspect.signature(fn))
    except Exception:
        return "unknown"


def _consume(rs, limit=None):
    rows = []
    fields = list(getattr(rs, "fields", []) or [])
    err = getattr(rs, "error_code", None)
    msg = getattr(rs, "error_msg", None)
    if str(err) != "0":
        return fields, rows, str(err), msg
    n = 0
    while rs.error_code == "0" and rs.next():
        row = rs.get_row_data()
        rows.append(dict(zip(fields, row)) if fields else row)
        n += 1
        if limit is not None and n >= limit:
            break
    return fields, rows, "0", msg


def audit_financial(bs):
    out = {"apis": {}, "timing_s": {}, "fields": {}, "pit_sample": {}, "restatement": {}}
    probes = [
        ("profit_2023q4", lambda: bs.query_profit_data(code="sh.600519", year=2023, quarter=4)),
        ("profit_2022q4", lambda: bs.query_profit_data(code="sh.600519", year=2022, quarter=4)),
        ("profit_2023q1", lambda: bs.query_profit_data(code="sh.600519", year=2023, quarter=1)),
        ("profit_2007q4", lambda: bs.query_profit_data(code="sh.600519", year=2007, quarter=4)),
        ("growth_2023q4", lambda: bs.query_growth_data(code="sh.600519", year=2023, quarter=4)),
        ("balance_2023q4", lambda: bs.query_balance_data(code="sh.600519", year=2023, quarter=4)),
        ("cash_2023q4", lambda: bs.query_cash_flow_data(code="sh.600519", year=2023, quarter=4)),
        ("dupont_2023q4", lambda: bs.query_dupont_data(code="sh.600519", year=2023, quarter=4)),
        ("operation_2023q4", lambda: bs.query_operation_data(code="sh.600519", year=2023, quarter=4)),
    ]
    for name, fn in probes:
        t0 = time.time()
        try:
            _f, rows, err, msg = _consume(fn())
            out["apis"][name] = {"n": len(rows), "sample": rows[:1], "seconds": time.time() - t0, "error": err, "msg": msg}
            if rows:
                out["fields"][name] = sorted(rows[0].keys())
            print("V16_AUDIT", name, len(rows), err, flush=True)
        except Exception as exc:
            out["apis"][name] = {"error": str(exc), "seconds": time.time() - t0}
            print("V16_AUDIT", name, "EXC", exc, flush=True)
    first = ((out["apis"].get("profit_2023q4") or {}).get("sample") or [])
    try:
        _f, again, err, msg = _consume(bs.query_profit_data(code="sh.600519", year=2023, quarter=4))
        out["restatement"] = {
            "version_history": False,
            "label": "RESTATEMENT_RISK",
            "repeat_equal": first == again[:1] if first else None,
            "note": "BaoStock returns one current row per code/year/quarter. No revision table.",
        }
    except Exception as exc:
        out["restatement"] = {"error": str(exc), "label": "RESTATEMENT_RISK"}
    rows = []
    for key in ("profit_2022q4", "profit_2023q4"):
        sample = ((out["apis"].get(key) or {}).get("sample") or [{}])[0]
        if sample:
            rows.append(
                {
                    "symbol": sample.get("code"),
                    "report_period": sample.get("statDate"),
                    "announcement_date": sample.get("pubDate"),
                    "net_profit": sample.get("netProfit"),
                }
            )
    vis = visible_financials(rows, PIT_ASOF)
    out["pit_sample"] = {
        "asof": PIT_ASOF,
        "rows": rows,
        "visible_periods": [r.get("report_period") for r in vis],
        "2023_annual_hidden": not knowledge_ok(PIT_ASOF, PIT_HIDDEN_ANN),
        "2022_annual_expected_visible": PIT_VISIBLE_PERIOD in [r.get("report_period") for r in vis],
        "hidden_period": PIT_HIDDEN_PERIOD,
        "ok": (not knowledge_ok(PIT_ASOF, PIT_HIDDEN_ANN))
        and any(r.get("report_period") == PIT_VISIBLE_PERIOD for r in vis),
    }
    t0 = time.time()
    n = 0
    for year, q in ((2020, 4), (2021, 4), (2022, 4), (2023, 4), (2024, 4)):
        for code in SAMPLES:
            _consume(bs.query_profit_data(code=code, year=year, quarter=q))
            n += 1
    out["timing_s"]["profit_15_calls"] = time.time() - t0
    out["timing_s"]["n"] = n
    out["timing_s"]["per_call"] = out["timing_s"]["profit_15_calls"] / float(n) if n else None
    out["signatures"] = {
        "query_profit_data": _sig(bs.query_profit_data),
        "query_balance_data": _sig(bs.query_balance_data),
        "query_stock_industry": _sig(bs.query_stock_industry),
    }
    return out


def audit_industry(bs):
    out = {"snapshot": {}, "date_attempts": {}, "historical_membership": False}
    t0 = time.time()
    try:
        _f, rows, err, msg = _consume(bs.query_stock_industry())
        updates = sorted(set((r.get("updateDate") or "") for r in rows))
        out["snapshot"] = {
            "n": len(rows),
            "seconds": time.time() - t0,
            "fields": sorted(rows[0].keys()) if rows else [],
            "update_dates": updates[:8],
            "n_update_dates": len(updates),
            "sample": rows[:3],
            "error": err,
        }
        out["current_only_without_date"] = len(updates) <= 2
        print("V16_AUDIT industry_n", len(rows), "update_dates", updates, flush=True)
    except Exception as exc:
        out["snapshot"] = {"error": str(exc)}
        out["current_only"] = True
    sig = _sig(bs.query_stock_industry)
    out["signature"] = sig
    params = []
    try:
        params = list(inspect.signature(bs.query_stock_industry).parameters)
    except Exception:
        params = []
    out["date_param_in_signature"] = any(p.lower() in ("date", "day", "asof") for p in params)
    for day in ("2015-06-15", "2020-01-02"):
        if not out["date_param_in_signature"]:
            out["date_attempts"][day] = {"skipped": "no date parameter in signature"}
            continue
        try:
            _f, rows, err, msg = _consume(bs.query_stock_industry(date=day))
            out["date_attempts"][day] = {
                "n": len(rows),
                "update_dates": sorted(set(r.get("updateDate") or "" for r in rows))[:4],
                "error": err,
            }
        except TypeError as exc:
            out["date_attempts"][day] = {"type_error": str(exc)}
        except Exception as exc:
            out["date_attempts"][day] = {"error": str(exc)[:200]}
    try:
        _f, a, err_a, _m = _consume(bs.query_hs300_stocks(date="2018-06-01"))
        _f, b, err_b, _m = _consume(bs.query_hs300_stocks(date="2024-06-03"))
        out["hs300_date_works"] = {
            "n_2018": len(a),
            "n_2024": len(b),
            "sets_differ": set(r.get("code") for r in a) != set(r.get("code") for r in b),
        }
        out["hs300_is_not_industry"] = True
    except Exception as exc:
        out["hs300_date_works"] = {"error": str(exc)}
    ns = [v.get("n") for v in out.get("date_attempts", {}).values() if isinstance(v, dict) and v.get("n")]
    out["current_only"] = len(set(ns)) <= 1 if ns else True
    out["historical_membership"] = len(set(ns)) >= 2 if ns else False
    out["pit_available"] = bool(out["historical_membership"] and out.get("date_param_in_signature"))
    out["status"] = "MONTHLY_ASOF_AVAILABLE" if out["pit_available"] else "CURRENT_ONLY"
    return out


def audit_secondary():
    import urllib.request

    out = {"akshare_installed": False, "canonical": False, "role": "CROSS_CHECK_ONLY"}
    try:
        import akshare

        out["akshare_installed"] = True
        out["akshare_version"] = getattr(akshare, "__version__", None)
    except Exception:
        out["akshare_note"] = "Not installed. Not installing."
    url = "https://push2.eastmoney.com/api/qt/stock/get?secid=1.600519&fields=f58,f57"
    req = urllib.request.Request(url, headers={"User-Agent": "TradeMindV16Audit/1.0"})
    try:
        handle = urllib.request.urlopen(req, timeout=15)
        try:
            body = handle.read(4000)
        finally:
            handle.close()
        out["em_http_ok"] = True
        out["em_bytes"] = len(body)
    except Exception as exc:
        out["em_http_ok"] = False
        out["em_error"] = str(exc)
    out["not_used_as_store"] = True
    return out


def run_source_audit():
    ensure_v16()
    import baostock as bs

    report = {
        "NEW_PURCHASE": NEW_PURCHASE,
        "canonical": CANONICAL_SOURCE,
        "secondary": SECONDARY_SOURCE,
        "forbidden": ["TUSHARE", "WIND", "CHOICE", "CSMAR", "DATABENTO", "OPTIONS", "MT5"],
        "financial": None,
        "industry": None,
        "secondary_probe": None,
    }
    print("V16_AUDIT_LOGIN", flush=True)
    login = bs.login()
    report["login"] = {"error_code": getattr(login, "error_code", None), "error_msg": getattr(login, "error_msg", None)}
    try:
        if str(report["login"]["error_code"]) != "0":
            raise RuntimeError("BAOSTOCK_LOGIN")
        report["financial"] = audit_financial(bs)
        report["industry"] = audit_industry(bs)
    except Exception:
        report["session_error"] = traceback.format_exc()
    finally:
        try:
            bs.logout()
        except Exception:
            pass
    report["secondary_probe"] = audit_secondary()
    fin = report.get("financial") or {}
    ind = report.get("industry") or {}
    report["verdict"] = {
        "financial_api_live": bool((fin.get("apis") or {}).get("profit_2023q4", {}).get("n")),
        "financial_has_pubDate": "pubDate" in ((fin.get("fields") or {}).get("profit_2023q4") or []),
        "financial_pit_sample_ok": bool((fin.get("pit_sample") or {}).get("ok")),
        "financial_restatement_risk": True,
        "industry_current_only": bool(ind.get("current_only", True)),
        "industry_pit": bool(ind.get("pit_available")),
        "purchase_required": False,
    }
    dump_json(os.path.join(OUT, "SOURCE_AUDIT.json"), report)
    dump_json(os.path.join(TMP, "SOURCE_AUDIT.json"), report)
    print("V16_AUDIT", report["verdict"], flush=True)
    return report


if __name__ == "__main__":
    run_source_audit()
