"""One symbol annual profit pull. Isolated so the parent can kill a hung BaoStock call."""
from __future__ import print_function

import sys

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_information_v16.financial_factory import _fetch_symbol, _utc_now


def main(symbol, year0, year1, listing_date, path):
    import baostock as bs

    login = bs.login()
    if str(login.error_code) != "0":
        raise RuntimeError("BAOSTOCK_LOGIN")
    try:
        job = {"symbol": symbol, "year0": int(year0), "year1": int(year1), "listing_date": listing_date or None}
        recs = _fetch_symbol(bs, job, 0.0)
    finally:
        bs.logout()
    n_ok = sum(1 for r in recs if r.get("raw"))
    dump_json(
        path,
        {
            "symbol": symbol,
            "listing_date": listing_date or None,
            "retrieved_at": _utc_now(),
            "source": "BAOSTOCK_query_profit_data",
            "immutable": True,
            "records": recs,
        },
        sort_keys=True,
    )
    print("V16_FIN_ONE", symbol, "ok", n_ok, "years", len(recs), flush=True)
    return n_ok


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
