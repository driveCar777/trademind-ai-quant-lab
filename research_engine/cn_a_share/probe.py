"""Live free-source probe. No key. No purchase. Not a data freeze."""
from __future__ import print_function

import json
import os
import traceback

from research_engine.cn_a_share.paths import TMP, ensure_tree


DELIST_CANDIDATES = (
    "sh.600005",  # 武钢股份, merged/delisted
    "sz.000003",  # PT 金田 historically
    "sh.600849",
    "sz.000022",
)
LIVE_SAMPLES = (
    "sh.600000",  # 浦发银行
    "sz.000001",  # 平安银行
    "sh.600519",  # 贵州茅台, many dividends
)
ASOF_DAYS = ("2015-06-15", "2020-01-02", "2024-01-02")


def _rows(rs, limit=8):
    out = []
    if rs is None:
        return {"error": "None", "rows": out, "fields": []}
    fields = list(getattr(rs, "fields", []) or [])
    err = getattr(rs, "error_code", None)
    msg = getattr(rs, "error_msg", None)
    n = 0
    if getattr(rs, "error_code", "0") in ("0", 0, None):
        while rs.error_code == "0" and rs.next():
            row = rs.get_row_data()
            if n < limit:
                out.append(dict(zip(fields, row)) if fields else row)
            n += 1
    return {
        "error_code": err,
        "error_msg": msg,
        "fields": fields,
        "n_seen": n,
        "sample": out,
    }


def probe_baostock():
    import baostock as bs

    login = bs.login()
    report = {
        "source": "BAOSTOCK",
        "package_version": getattr(bs, "__version__", None),
        "login_error_code": getattr(login, "error_code", None),
        "login_error_msg": getattr(login, "error_msg", None),
        "calls": {},
    }
    try:
        report["calls"]["trade_dates"] = _rows(bs.query_trade_dates(start_date="2024-01-01", end_date="2024-01-31"), 12)
        report["calls"]["all_stock_today"] = _rows(bs.query_all_stock(), 5)
        for day in ASOF_DAYS:
            report["calls"]["all_stock_" + day] = _rows(bs.query_all_stock(day=day), 5)
        for code in LIVE_SAMPLES + DELIST_CANDIDATES:
            report["calls"]["basic_" + code] = _rows(bs.query_stock_basic(code=code), 5)
        report["calls"]["industry"] = _rows(bs.query_stock_industry(), 5)
        report["calls"]["k_raw_600519"] = _rows(
            bs.query_history_k_data_plus(
                "sh.600519",
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
                start_date="2024-06-01",
                end_date="2024-06-20",
                frequency="d",
                adjustflag="3",
            ),
            6,
        )
        report["calls"]["k_qfq_600519"] = _rows(
            bs.query_history_k_data_plus(
                "sh.600519",
                "date,code,open,high,low,close,volume,amount,adjustflag",
                start_date="2024-06-01",
                end_date="2024-06-20",
                frequency="d",
                adjustflag="2",
            ),
            3,
        )
        report["calls"]["adjust_600519"] = _rows(bs.query_adjust_factor(code="sh.600519", start_date="2018-01-01", end_date="2025-12-31"), 8)
        report["calls"]["dividend_600519"] = _rows(bs.query_dividend_data(code="sh.600519", year="2023", yearType="report"), 8)
        report["calls"]["profit_600519"] = _rows(bs.query_profit_data(code="sh.600519", year=2023, quarter=4), 8)
        for attr in ("query_growth_data", "query_balance_data", "query_cash_flow_data", "query_dupont_data"):
            fn = getattr(bs, attr, None)
            if fn is None:
                report["calls"][attr] = {"missing": True}
            else:
                try:
                    report["calls"][attr] = _rows(fn(code="sh.600519", year=2023, quarter=4), 4)
                except TypeError:
                    report["calls"][attr] = {"error": "signature"}
        for code in DELIST_CANDIDATES:
            report["calls"]["k_delist_" + code] = _rows(
                bs.query_history_k_data_plus(
                    code,
                    "date,code,open,high,low,close,volume,amount,tradestatus",
                    start_date="2010-01-01",
                    end_date="2018-12-31",
                    frequency="d",
                    adjustflag="3",
                ),
                3,
            )
        # hs300 constituents if available
        for attr, name in (
            ("query_hs300_stocks", "hs300"),
            ("query_sz50_stocks", "sz50"),
            ("query_zz500_stocks", "zz500"),
        ):
            fn = getattr(bs, attr, None)
            if fn is None:
                report["calls"][name] = {"missing": True}
            else:
                try:
                    report["calls"][name] = _rows(fn(), 4)
                except TypeError:
                    report["calls"][name] = _rows(fn(date="2024-01-02"), 4)
    finally:
        try:
            bs.logout()
        except Exception:
            pass
    return report


def probe_em_http():
    """AkShare-class East Money public kline. Fragile scrape, not canonical."""
    import urllib.request

    url = (
        "https://push2his.eastmoney.com/api/qt/stock/kline/get?"
        "secid=1.600519&klt=101&fqt=0&lmt=5&end=20500101&iscca=1&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "TradeMindV12Audit/1.0"})
    try:
        handle = urllib.request.urlopen(req, timeout=20)
        try:
            body = handle.read(20000)
        finally:
            handle.close()
        payload = json.loads(body.decode("utf-8", "replace"))
        data = (payload.get("data") or {})
        klines = data.get("klines") or []
        return {
            "source": "EASTMONEY_KLINE_HTTP",
            "akshare_class": True,
            "canonical": False,
            "http_ok": True,
            "name": data.get("name"),
            "n_klines": len(klines),
            "sample": klines[:3],
            "fragility": "Unsigned public HTML/JSON endpoint. Breaks without notice. NOT TRUSTED as canonical.",
        }
    except Exception as exc:
        return {
            "source": "EASTMONEY_KLINE_HTTP",
            "akshare_class": True,
            "canonical": False,
            "http_ok": False,
            "error": str(exc),
            "fragility": "Unsigned public HTML/JSON endpoint. Breaks without notice. NOT TRUSTED as canonical.",
        }


def run_probe():
    ensure_tree()
    out = {"NEW_PURCHASE": False, "akshare_installed": False, "baostock": None, "em_http": None}
    try:
        import akshare  # noqa: F401

        out["akshare_installed"] = True
        out["akshare_version"] = getattr(akshare, "__version__", None)
    except Exception:
        out["akshare_installed"] = False
        out["akshare_note"] = "Not installed. Not installing the large scrape stack. East Money HTTP used as AkShare-class cross-check."
    try:
        out["baostock"] = probe_baostock()
    except Exception:
        out["baostock"] = {"error": traceback.format_exc()}
    out["em_http"] = probe_em_http()
    path = os.path.join(TMP, "SOURCE_PROBE_LIVE.json")
    handle = open(path, "w", encoding="utf-8")
    try:
        json.dump(out, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    finally:
        handle.close()
    return path, out
