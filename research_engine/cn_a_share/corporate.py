"""Corporate-action fetch and adjustment check. Not a factor."""
from __future__ import print_function

from research_engine.cn_a_share.bars import _f


def fetch_dividends(symbol, year):
    import baostock as bs

    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError("BAOSTOCK_LOGIN:%s" % login.error_msg)
    try:
        rs = bs.query_dividend_data(code=symbol, year=str(year), yearType="report")
        rows = []
        while rs.error_code == "0" and rs.next():
            rows.append(dict(zip(rs.fields, rs.get_row_data())))
        return rows
    finally:
        bs.logout()


def fetch_adjust_factors(symbol, start, end):
    import baostock as bs

    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError("BAOSTOCK_LOGIN:%s" % login.error_msg)
    try:
        rs = bs.query_adjust_factor(code=symbol, start_date=start, end_date=end)
        rows = []
        while rs.error_code == "0" and rs.next():
            rows.append(dict(zip(rs.fields, rs.get_row_data())))
        return rows
    finally:
        bs.logout()


def verify_ex_date(raw_rows, qfq_rows, operate_date):
    """On operate date, raw and qfq closes should differ if a cash/stock event exists."""
    raw_map = dict((r.get("date") or r.get("trade_date"), _f(r.get("close") or r.get("raw_close"))) for r in raw_rows)
    qfq_map = dict((r.get("date") or r.get("trade_date"), _f(r.get("close") or r.get("adjusted_close"))) for r in qfq_rows)
    # find nearest trade dates around operate_date
    dates = sorted(set(raw_map.keys()) & set(qfq_map.keys()))
    if not dates:
        return {"ok": False, "reason": "NO_OVERLAP"}
    raw_eq = 0
    qfq_diff = 0
    for d in dates:
        if raw_map[d] is None or qfq_map[d] is None:
            continue
        if abs(raw_map[d] - qfq_map[d]) > 1e-6:
            qfq_diff += 1
        else:
            raw_eq += 1
    return {
        "ok": qfq_diff > 0,
        "operate_date": operate_date,
        "n_overlap": len(dates),
        "n_raw_eq_qfq": raw_eq,
        "n_raw_ne_qfq": qfq_diff,
        "reason": "QFQ_DIFFERS_FROM_RAW" if qfq_diff > 0 else "RAW_EQUALS_QFQ",
    }
