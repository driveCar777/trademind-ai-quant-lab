"""Industry snapshot. Do not backfill today's industry into history."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share.session import BaoSession
from research_engine.cn_a_share_information_v16.industry_schema import NORMALIZED_COLS, normalize_industry_row
from research_engine.cn_a_share_information_v16.paths import IND_MAN, IND_QUAL, IND_RAW, IND_REF, OUT, ensure_v16


def download_industry_snapshot():
    ensure_v16()
    sess = BaoSession(sleep_s=0.03, max_retries=4)
    try:
        sess.login()
        rows = sess._retry(lambda: sess.bs.query_stock_industry())
    finally:
        sess.logout()
    dump_json(os.path.join(IND_RAW, "industry_snapshot.json"), {"n": len(rows), "rows": rows, "immutable": True})
    norms = [normalize_industry_row(r) for r in rows]
    norms = [n for n in norms if n]
    write_csv(os.path.join(IND_REF, "INDUSTRY_SNAPSHOT.csv"), NORMALIZED_COLS, norms)
    catalog = {
        "n": len(norms),
        "n_update_dates": len(set(n.get("source_update_date") for n in norms if n.get("source_update_date"))),
        "update_dates": sorted(set(n.get("source_update_date") for n in norms if n.get("source_update_date"))),
        "effective_date_present": any(n.get("effective_date") for n in norms),
        "pit_available": False,
        "label": "CURRENT_ONLY",
        "backfill_forbidden": True,
    }
    dump_json(os.path.join(IND_REF, "INDUSTRY_CATALOG.json"), catalog)
    dump_json(os.path.join(IND_MAN, "INDUSTRY_SNAPSHOT.json"), catalog)
    dump_json(os.path.join(IND_QUAL, "INDUSTRY_CATALOG.json"), catalog)
    dump_json(os.path.join(OUT, "INDUSTRY_CATALOG.json"), catalog)
    print("V16_IND_SNAP", catalog, flush=True)
    return norms, catalog


def load_industry_snapshot():
    from research_engine.cn_a_share.io_util import load_json

    raw = load_json(os.path.join(IND_RAW, "industry_snapshot.json"))
    return [normalize_industry_row(r) for r in raw.get("rows") or []]
