"""One monthly as-of snapshot for HS300 and ZZ500. Isolated so a hung BaoStock call can die."""
from __future__ import print_function

import sys

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_index_v20.factory import _consume, _utc_now


def main(day, hs_path, zz_path):
    import baostock as bs

    login = bs.login()
    if str(login.error_code) != "0":
        raise RuntimeError("BAOSTOCK_LOGIN")
    try:
        hs_rows, hs_err, hs_msg = _consume(bs.query_hs300_stocks(date=day))
        zz_rows, zz_err, zz_msg = _consume(bs.query_zz500_stocks(date=day))
    finally:
        bs.logout()
    dump_json(
        hs_path,
        {
            "asof": day,
            "index": "HS300",
            "retrieved_at": _utc_now(),
            "n": len(hs_rows),
            "error": hs_err,
            "msg": hs_msg,
            "immutable": True,
            "rows": hs_rows,
        },
    )
    dump_json(
        zz_path,
        {
            "asof": day,
            "index": "ZZ500",
            "retrieved_at": _utc_now(),
            "n": len(zz_rows),
            "error": zz_err,
            "msg": zz_msg,
            "immutable": True,
            "rows": zz_rows,
        },
    )
    print("V20_IDX_ONE", day, "HS300", len(hs_rows), "ZZ500", len(zz_rows), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
