"""Deeper live audit: basics census, as-of membership, index date, early delist bars."""
from __future__ import print_function

import json
import os

from research_engine.cn_a_share.paths import TMP, ensure_tree


def _consume(rs):
    rows = []
    fields = list(getattr(rs, "fields", []) or [])
    if getattr(rs, "error_code", "0") != "0":
        return fields, rows, rs.error_code, rs.error_msg
    while rs.error_code == "0" and rs.next():
        rows.append(dict(zip(fields, rs.get_row_data())) if fields else rs.get_row_data())
    return fields, rows, "0", "success"


def run_audit():
    import baostock as bs

    ensure_tree()
    login = bs.login()
    out = {"login": login.error_code, "checks": {}}
    try:
        _f, rows, err, msg = _consume(bs.query_stock_basic())
        out["checks"]["stock_basic_all"] = {
            "n": len(rows),
            "error": err,
            "fields": _f,
        }
        by_type = {}
        by_status = {}
        delisted = []
        for row in rows:
            by_type[row.get("type")] = by_type.get(row.get("type"), 0) + 1
            by_status[row.get("status")] = by_status.get(row.get("status"), 0) + 1
            if row.get("status") == "0" and row.get("type") == "1":
                delisted.append(row)
        out["checks"]["stock_basic_all"]["by_type"] = by_type
        out["checks"]["stock_basic_all"]["by_status"] = by_status
        out["checks"]["stock_basic_all"]["n_stock_delisted"] = len(delisted)
        out["checks"]["stock_basic_all"]["delist_sample"] = delisted[:8]
        # persist full basic for factory (small)
        basic_path = os.path.join(TMP, "stock_basic_all.json")
        handle = open(basic_path, "w", encoding="utf-8")
        json.dump(rows, handle, ensure_ascii=False)
        handle.close()
        out["checks"]["stock_basic_all"]["path"] = basic_path

        for day, expect_in, expect_out in (
            ("2016-12-30", "sh.600005", None),
            ("2017-03-01", None, "sh.600005"),
            ("2026-08-28", "sz.000001", "sh.600005"),
        ):
            _f, uni, err, msg = _consume(bs.query_all_stock(day=day))
            codes = set(r.get("code") for r in uni)
            stocks = [r for r in uni if (r.get("code") or "").split(".")[-1][:1] in "036" and not (r.get("code") or "").startswith("sh.000")]
            # crude: sh.6 / sz.0 / sz.3 / bj.8 / bj.4
            a_eq = [r for r in uni if _is_equity(r.get("code"))]
            out["checks"]["asof_" + day] = {
                "n_all": len(uni),
                "n_equity_guess": len(a_eq),
                "has_600005": "sh.600005" in codes,
                "has_000001": "sz.000001" in codes,
                "has_000003": "sz.000003" in codes,
                "error": err,
            }

        # index date param
        fn = bs.query_hs300_stocks
        _f, now, err, msg = _consume(fn())
        try:
            _f2, old, err2, msg2 = _consume(fn(date="2018-06-29"))
        except TypeError:
            old, err2 = [], "no-date"
        now_c = set(r.get("code") for r in now)
        old_c = set(r.get("code") for r in old)
        out["checks"]["hs300_pit"] = {
            "n_now": len(now),
            "n_2018": len(old),
            "now_update": (now[0] or {}).get("updateDate") if now else None,
            "old_update": (old[0] or {}).get("updateDate") if old else None,
            "symmetric_diff": len(now_c.symmetric_difference(old_c)) if old else None,
            "error_old": err2,
        }

        _f, early, err, msg = _consume(
            bs.query_history_k_data_plus(
                "sz.000003",
                "date,code,close,volume,tradestatus",
                start_date="1991-01-01",
                end_date="2002-12-31",
                frequency="d",
                adjustflag="3",
            )
        )
        out["checks"]["k_000003_early"] = {"n": len(early), "error": err, "first": early[0] if early else None, "last": early[-1] if early else None}

        # sample 12 delisted equities for bar coverage 2000-2019
        sample = delisted[:12]
        cov = []
        for row in sample:
            _f, bars, err, msg = _consume(
                bs.query_history_k_data_plus(
                    row["code"],
                    "date,code,close,volume,tradestatus",
                    start_date="2000-01-01",
                    end_date="2019-12-31",
                    frequency="d",
                    adjustflag="3",
                )
            )
            cov.append({"code": row["code"], "outDate": row.get("outDate"), "n_bars": len(bars), "first": (bars[0] or {}).get("date") if bars else None, "last": (bars[-1] or {}).get("date") if bars else None})
        out["checks"]["delist_bar_sample"] = cov
    finally:
        bs.logout()
    path = os.path.join(TMP, "SOURCE_AUDIT_DEEP.json")
    handle = open(path, "w", encoding="utf-8")
    json.dump(out, handle, indent=2, ensure_ascii=False)
    handle.close()
    return path, out


def _is_equity(code):
    if not code or "." not in code:
        return False
    mkt, num = code.split(".", 1)
    if mkt not in ("sh", "sz", "bj"):
        return False
    if mkt == "sh" and num.startswith("6"):
        return True
    if mkt == "sz" and (num.startswith("00") or num.startswith("30")):
        return True
    if mkt == "bj" and (num.startswith("8") or num.startswith("4") or num.startswith("9")):
        return True
    return False
