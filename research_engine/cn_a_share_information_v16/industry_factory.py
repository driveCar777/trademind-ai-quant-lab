"""Monthly BaoStock industry snapshots. date= is knowledge time. Do not use current-only backfill."""
from __future__ import print_function

import json
import os
import subprocess
import sys
import time
from datetime import date, datetime, timezone

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_information_v16.industry_schema import NORMALIZED_COLS
from research_engine.cn_a_share_information_v16.paths import IND_MAN, IND_NORM, IND_QUAL, IND_RAW, IND_REF, OUT, ensure_v16
from research_protocol.hashing import file_sha256


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _consume(rs):
    rows = []
    fields = list(getattr(rs, "fields", []) or [])
    if str(getattr(rs, "error_code", "1")) != "0":
        return rows, str(rs.error_code), getattr(rs, "error_msg", None)
    while rs.error_code == "0" and rs.next():
        rows.append(dict(zip(fields, rs.get_row_data())))
    return rows, "0", None


def month_grid(start="2009-12-15", end="2024-02-15"):
    y, m, d = [int(x) for x in start.split("-")]
    ey, em, ed = [int(x) for x in end.split("-")]
    out = []
    cur = date(y, m, d)
    last = date(ey, em, ed)
    while cur <= last:
        out.append(cur.isoformat())
        if cur.month == 12:
            cur = date(cur.year + 1, 1, min(d, 28))
        else:
            cur = date(cur.year, cur.month + 1, min(d, 28))
    return out


def download_industry_monthly(start="2009-12-15", end="2024-02-15"):
    """One snapshot per month. Query date is the as-of / effective date."""
    ensure_v16()
    import baostock as bs

    days = month_grid(start, end)
    raw_dir = os.path.join(IND_RAW, "monthly")
    if not os.path.isdir(raw_dir):
        os.makedirs(raw_dir)
    done = set(name[9:19] for name in os.listdir(raw_dir) if name.startswith("asof_") and name.endswith(".json"))
    todo = [d for d in days if d not in done]
    print("V16_IND_DL", "done", len(done), "todo", len(todo), flush=True)
    if not todo:
        return {"n_done": len(done), "n_todo": 0}
    hung = 0
    exe = sys.executable
    for i, day in enumerate(todo):
        path = os.path.join(raw_dir, "asof_%s.json" % day)
        t0 = time.time()
        try:
            proc = subprocess.run(
                [exe, "-u", "-m", "research_engine.cn_a_share_information_v16.industry_one", day, path],
                timeout=75,
                cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
            )
            elapsed = time.time() - t0
            if proc.returncode != 0:
                print("V16_IND_FAIL", day, proc.returncode, "s", round(elapsed, 1), flush=True)
                hung += 1
            else:
                print("V16_IND_DL", i + 1, "/", len(todo), day, "s", round(elapsed, 1), flush=True)
        except subprocess.TimeoutExpired:
            hung += 1
            print("V16_IND_TIMEOUT", day, flush=True)
            if hung >= 8:
                print("V16_IND_ABORT_HANG", flush=True)
                break
    return {"n_done": len([n for n in os.listdir(raw_dir) if n.startswith("asof_")]), "hung": hung}


def download_industry_snapshot():
    """Current snapshot for catalog only. Not a PIT freeze."""
    ensure_v16()
    import baostock as bs

    login = bs.login()
    if str(login.error_code) != "0":
        raise RuntimeError("BAOSTOCK_LOGIN")
    try:
        rows, err, msg = _consume(bs.query_stock_industry())
    finally:
        bs.logout()
    dump_json(os.path.join(IND_RAW, "industry_snapshot.json"), {"n": len(rows), "rows": rows, "immutable": True, "current_only": True})
    return rows


def normalize_industry():
    ensure_v16()
    raw_dir = os.path.join(IND_RAW, "monthly")
    rows = []
    asofs = []
    for name in sorted(os.listdir(raw_dir)):
        if not name.startswith("asof_") or not name.endswith(".json"):
            continue
        handle = open(os.path.join(raw_dir, name), "r", encoding="utf-8")
        try:
            payload = json.load(handle)
        finally:
            handle.close()
        asof = payload.get("asof")
        asofs.append(asof)
        for raw in payload.get("rows") or []:
            rows.append(
                {
                    "symbol": raw.get("code"),
                    "name": raw.get("code_name"),
                    "industry": raw.get("industry"),
                    "industry_classification": raw.get("industryClassification"),
                    "source_update_date": raw.get("updateDate"),
                    "effective_date": asof,
                    "pit_available": True,
                    "source": "BAOSTOCK_query_stock_industry_date",
                }
            )
    csv_path = os.path.join(IND_NORM, "INDUSTRY_MONTHLY.csv")
    write_csv(csv_path, NORMALIZED_COLS, rows)
    catalog = {
        "n_rows": len(rows),
        "n_asof": len(asofs),
        "asof_min": asofs[0] if asofs else None,
        "asof_max": asofs[-1] if asofs else None,
        "n_symbols": len(set(r["symbol"] for r in rows)),
        "effective_date_present": True,
        "pit_available": True,
        "label": "MONTHLY_ASOF",
        "csv_sha256": file_sha256(csv_path),
        "grid": "15th_of_month",
        "knowledge_time": "effective_date = query date",
    }
    dump_json(os.path.join(IND_REF, "INDUSTRY_CATALOG.json"), catalog)
    dump_json(os.path.join(IND_MAN, "INDUSTRY_NORMALIZE.json"), catalog)
    dump_json(os.path.join(IND_QUAL, "INDUSTRY_CATALOG.json"), catalog)
    dump_json(os.path.join(OUT, "INDUSTRY_CATALOG.json"), catalog)
    print("V16_IND_NORM", catalog["n_rows"], catalog["n_asof"], flush=True)
    return rows, catalog
