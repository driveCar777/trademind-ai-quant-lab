"""Live free-source audit. No key. No purchase. One BaoStock session."""
from __future__ import print_function

import inspect
import os
import time
import traceback

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share.pit import knowledge_ok, visible_financials
from research_engine.cn_a_share.session import BaoSession
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
        try:
            return str(inspect.getargspec(fn))
        except Exception:
            return "unknown"


def _call(sess, fn, **kwargs):
    t0 = time.time()
    rows = sess._retry(lambda: fn(**kwargs))
    return rows, time.time() - t0


def audit_financial(sess):
    bs = sess.bs
    out = {"apis": {}, "timing_s": {}, "fields": {}, "pit_sample": {}, "restatement": {}}
    probes = [
        ("profit_2023q4", bs.query_profit_data, {"code": "sh.600519", "year": 2023, "quarter": 4}),
        ("profit_2022q4", bs.query_profit_data, {"code": "sh.600519", "year": 2022, "quarter": 4}),
        ("profit_2023q1", bs.query_profit_data, {"code": "sh.600519", "year": 2023, "quarter": 1}),
        ("profit_2007q4", bs.query_profit_data, {"code": "sh.600519", "year": 2007, "quarter": 4}),
        ("growth_2023q4", bs.query_growth_data, {"code": "sh.600519", "year": 2023, "quarter": 4}),
        ("balance_2023q4", bs.query_balance_data, {"code": "sh.600519", "year": 2023, "quarter": 4}),
        ("cash_2023q4", bs.query_cash_flow_data, {"code": "sh.600519", "year": 2023, "quarter": 4}),
        ("dupont_2023q4", bs.query_dupont_data, {"code": "sh.600519", "year": 2023, "quarter": 4}),
        ("operation_2023q4", bs.query_operation_data, {"code": "sh.600519", "year": 2023, "quarter": 4}),
    ]
    for name, fn, kw in probes:
        try:
            rows, dt = _call(sess, fn, **kw)
            out["apis"][name] = {"n": len(rows), "sample": rows[:1], "seconds": dt}
            if rows:
                out["fields"][name] = sorted(rows[0].keys())
        except Exception as exc:
            out["apis"][name] = {"error": str(exc)}
    # second fetch of 2023Q4: same numbers? no version history either way
    try:
        again, _dt = _call(sess, bs.query_profit_data, code="sh.600519", year=2023, quarter=4)
        first = (out["apis"].get("profit_2023q4") or {}).get("sample") or []
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
            sess._retry(lambda c=code, y=year, qq=q: bs.query_profit_data(code=c, year=y, quarter=qq))
            n += 1
    out["timing_s"]["profit_15_calls"] = time.time() - t0
    out["timing_s"]["n"] = n
    out["timing_s"]["per_call"] = (time.time() - t0) / float(n) if n else None
    out["signatures"] = {
        "query_profit_data": _sig(bs.query_profit_data),
        "query_balance_data": _sig(bs.query_balance_data),
        "query_stock_industry": _sig(bs.query_stock_industry),
    }
    return out


def audit_industry(sess):
    bs = sess.bs
    out = {"snapshot": {}, "date_attempts": {}, "historical_membership": False}
    try:
        rows, dt = _call(sess, bs.query_stock_industry)
        updates = sorted(set((r.get("updateDate") or "") for r in rows))
        out["snapshot"] = {
            "n": len(rows),
            "seconds": dt,
            "fields": sorted(rows[0].keys()) if rows else [],
            "update_dates": updates[:8],
            "n_update_dates": len(updates),
            "sample": rows[:3],
        }
        out["current_only"] = len(updates) <= 2
    except Exception as exc:
        out["snapshot"] = {"error": str(exc)}
        out["current_only"] = True
    for day in ("2015-06-15", "2020-01-02", "2024-01-02"):
        attempt = {"day": day}
        for kwargs in ({"date": day}, {"day": day}, {"updateDate": day}):
            try:
                rows = sess._retry(lambda kw=kwargs: bs.query_stock_industry(**kw))
                attempt[str(kwargs)] = {"n": len(rows), "update_dates": sorted(set(r.get("updateDate") or "" for r in rows))[:4]}
            except TypeError as exc:
                attempt[str(kwargs)] = {"type_error": str(exc)}
            except Exception as exc:
                attempt[str(kwargs)] = {"error": str(exc)[:200]}
        out["date_attempts"][day] = attempt
    # index membership has dates; that is not industry classification
    try:
        a = sess._retry(lambda: bs.query_hs300_stocks(date="2018-06-01"))
        b = sess._retry(lambda: bs.query_hs300_stocks(date="2024-06-03"))
        out["hs300_date_works"] = {"n_2018": len(a), "n_2024": len(b), "sets_differ": set(r.get("code") for r in a) != set(r.get("code") for r in b)}
        out["hs300_is_not_industry"] = True
    except Exception as exc:
        out["hs300_date_works"] = {"error": str(exc)}
    out["pit_available"] = False
    out["status"] = "CURRENT_ONLY" if out.get("current_only") else "UNKNOWN"
    return out


def audit_secondary():
    """AkShare-class HTTP only. Not canonical storage."""
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
    report = {
        "NEW_PURCHASE": NEW_PURCHASE,
        "canonical": CANONICAL_SOURCE,
        "secondary": SECONDARY_SOURCE,
        "forbidden": ["TUSHARE", "WIND", "CHOICE", "CSMAR", "DATABENTO", "OPTIONS", "MT5"],
        "financial": None,
        "industry": None,
        "secondary_probe": None,
    }
    sess = BaoSession(sleep_s=0.03, max_retries=4)
    try:
        sess.login()
        report["financial"] = audit_financial(sess)
        report["industry"] = audit_industry(sess)
    except Exception:
        report["session_error"] = traceback.format_exc()
    finally:
        sess.logout()
    report["secondary_probe"] = audit_secondary()
    fin = report.get("financial") or {}
    ind = report.get("industry") or {}
    report["verdict"] = {
        "financial_api_live": bool((fin.get("apis") or {}).get("profit_2023q4", {}).get("n")),
        "financial_has_pubDate": "pubDate" in ((fin.get("fields") or {}).get("profit_2023q4") or []),
        "financial_pit_sample_ok": bool((fin.get("pit_sample") or {}).get("ok")),
        "financial_restatement_risk": True,
        "industry_current_only": bool(ind.get("current_only", True)),
        "industry_pit": False,
        "purchase_required": False,
    }
    dump_json(os.path.join(OUT, "SOURCE_AUDIT.json"), report)
    dump_json(os.path.join(TMP, "SOURCE_AUDIT.json"), report)
    print("V16_AUDIT", report["verdict"], flush=True)
    return report


if __name__ == "__main__":
    run_source_audit()
