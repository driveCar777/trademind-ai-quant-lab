"""One industry as-of snapshot. Isolated so the parent can kill a hung BaoStock call."""
from __future__ import print_function

import sys

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_information_v16.industry_factory import _consume, _utc_now


def main(day, path):
    import baostock as bs

    login = bs.login()
    if str(login.error_code) != "0":
        raise RuntimeError("BAOSTOCK_LOGIN")
    try:
        rows, err, msg = _consume(bs.query_stock_industry(date=day))
    finally:
        bs.logout()
    dump_json(
        path,
        {
            "asof": day,
            "retrieved_at": _utc_now(),
            "n": len(rows),
            "error": err,
            "msg": msg,
            "immutable": True,
            "rows": rows,
        },
    )
    print("V16_IND_ONE", day, len(rows), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
