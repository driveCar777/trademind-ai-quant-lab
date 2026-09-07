"""Monthly BaoStock HS300/ZZ500 as-of snapshots. Query date is knowledge time."""
from __future__ import print_function

import json
import os
import subprocess
import sys
import time
from datetime import date, datetime, timezone

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_index_v20.paths import IDX_CSV, IDX_MAN, IDX_NORM, IDX_QUAL, IDX_RAW, IDX_REF, OUT, NORMALIZED_COLS, ensure_v20
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


def download_index_monthly(start="2009-12-15", end="2024-02-15"):
    ensure_v20()
    days = month_grid(start, end)
    raw_dir = os.path.join(IDX_RAW, "monthly")
    if not os.path.isdir(raw_dir):
        os.makedirs(raw_dir)
    done = []
    todo = []
    for day in days:
        hs = os.path.join(raw_dir, "hs300_%s.json" % day)
        zz = os.path.join(raw_dir, "zz500_%s.json" % day)
        if os.path.isfile(hs) and os.path.isfile(zz):
            done.append(day)
        else:
            todo.append(day)
    print("V20_IDX_DL", "done", len(done), "todo", len(todo), flush=True)
    if not todo:
        return {"n_done": len(done), "n_todo": 0}
    hung = 0
    exe = sys.executable
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    for i, day in enumerate(todo):
        hs = os.path.join(raw_dir, "hs300_%s.json" % day)
        zz = os.path.join(raw_dir, "zz500_%s.json" % day)
        ok = False
        for attempt in range(2):
            t0 = time.time()
            try:
                proc = subprocess.run(
                    [exe, "-u", "-m", "research_engine.cn_a_share_index_v20.index_one", day, hs, zz],
                    timeout=90,
                    cwd=cwd,
                )
                elapsed = time.time() - t0
                if proc.returncode == 0 and os.path.isfile(hs) and os.path.isfile(zz):
                    print("V20_IDX_DL", i + 1, "/", len(todo), day, "s", round(elapsed, 1), "try", attempt + 1, flush=True)
                    hung = 0
                    ok = True
                    break
                print("V20_IDX_FAIL", day, proc.returncode, "s", round(elapsed, 1), "try", attempt + 1, flush=True)
            except subprocess.TimeoutExpired:
                hung += 1
                print("V20_IDX_TIMEOUT", day, "try", attempt + 1, "hung", hung, flush=True)
                if hung >= 8:
                    print("V20_IDX_ABORT_HANG", flush=True)
                    return {"n_done": len(done), "hung": hung, "aborted": True}
        if not ok:
            print("V20_IDX_SKIP", day, flush=True)
        time.sleep(0.35)
    n_done = 0
    for day in days:
        if os.path.isfile(os.path.join(raw_dir, "hs300_%s.json" % day)) and os.path.isfile(os.path.join(raw_dir, "zz500_%s.json" % day)):
            n_done += 1
    return {"n_done": n_done, "n_todo": 0, "hung": hung}


def normalize_index():
    ensure_v20()
    raw_dir = os.path.join(IDX_RAW, "monthly")
    rows = []
    asofs = []
    expected = month_grid()
    if not os.path.isdir(raw_dir):
        catalog = {"n_rows": 0, "n_asof": 0, "n_expected": len(expected), "download_complete": False, "pit_available": False, "label": "DOWNLOAD_INCOMPLETE"}
        dump_json(os.path.join(IDX_REF, "INDEX_CATALOG.json"), catalog)
        dump_json(os.path.join(OUT, "INDEX_CATALOG.json"), catalog)
        return [], catalog
    names = sorted(os.listdir(raw_dir))
    seen = set()
    for name in names:
        if not name.endswith(".json"):
            continue
        if not (name.startswith("hs300_") or name.startswith("zz500_")):
            continue
        handle = open(os.path.join(raw_dir, name), "r", encoding="utf-8")
        try:
            payload = json.load(handle)
        finally:
            handle.close()
        asof = payload.get("asof")
        index = payload.get("index")
        if asof:
            seen.add(asof)
        for raw in payload.get("rows") or []:
            rows.append(
                {
                    "symbol": raw.get("code"),
                    "index": index,
                    "name": raw.get("code_name"),
                    "source_update_date": raw.get("updateDate"),
                    "effective_date": asof,
                    "source": "BAOSTOCK_query_%s_stocks_date" % (index or "").lower(),
                }
            )
    asofs = sorted(seen)
    write_csv(IDX_CSV, NORMALIZED_COLS, rows)
    catalog = {
        "n_rows": len(rows),
        "n_asof": len(asofs),
        "n_expected": len(expected),
        "download_complete": len(asofs) >= len(expected) and len(asofs) > 0,
        "asof_min": asofs[0] if asofs else None,
        "asof_max": asofs[-1] if asofs else None,
        "n_symbols": len(set(r["symbol"] for r in rows if r.get("symbol"))),
        "n_hs300_rows": sum(1 for r in rows if r.get("index") == "HS300"),
        "n_zz500_rows": sum(1 for r in rows if r.get("index") == "ZZ500"),
        "effective_date_present": True,
        "pit_available": len(asofs) >= len(expected) and len(asofs) > 0,
        "label": "MONTHLY_ASOF" if len(asofs) >= len(expected) and asofs else "DOWNLOAD_INCOMPLETE",
        "csv_sha256": file_sha256(IDX_CSV) if os.path.isfile(IDX_CSV) else None,
        "grid": "15th_of_month",
        "knowledge_time": "effective_date = query date",
        "csv": IDX_CSV,
    }
    dump_json(os.path.join(IDX_REF, "INDEX_CATALOG.json"), catalog)
    dump_json(os.path.join(IDX_MAN, "INDEX_NORMALIZE.json"), catalog)
    dump_json(os.path.join(IDX_QUAL, "INDEX_CATALOG.json"), catalog)
    dump_json(os.path.join(OUT, "INDEX_CATALOG.json"), catalog)
    print("V20_IDX_NORM", catalog["n_rows"], catalog["n_asof"], flush=True)
    return rows, catalog
