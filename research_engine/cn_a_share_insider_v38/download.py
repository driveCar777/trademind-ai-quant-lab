"""Download holder / executive trade tables per calendar year (all stocks, paginated). Resumable, threaded, no key."""
from __future__ import print_function

import gzip
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from research_engine.cn_a_share_insider_v38 import RAW, TABLES, YEARS, ensure_v38l4

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
HDR = {"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}
BASE = "https://datacenter-web.eastmoney.com/api/data/v1/get"
THREADS = int(os.environ.get("TRADEMIND_INSIDER_THREADS", "4"))
PAGE = 500


def fetch_page(report, datecol, year, page):
    q = {"reportName": report, "columns": "ALL", "source": "WEB", "client": "WEB", "sortColumns": "%s,SECURITY_CODE" % datecol,
         "sortTypes": "1,1", "pageSize": str(PAGE), "pageNumber": str(page),
         "filter": "(%s>='%d-01-01')(%s<='%d-12-31')" % (datecol, year, datecol, year)}
    url = BASE + "?" + urllib.parse.urlencode(q)
    last = None
    for attempt in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=60, context=CTX) as h:
                return json.loads(h.read().decode("utf-8"))
        except Exception as e:  # noqa
            last = e
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError("fetch failed %s %d p%d: %s" % (report, year, page, last))


def fetch_table(key, year):
    report, datecol = TABLES[key]
    dest = os.path.join(RAW, "%s_%d.json.gz" % (key, year))
    if os.path.isfile(dest):
        return key, year, -1
    rows, page = [], 1
    while True:
        d = fetch_page(report, datecol, year, page)
        r = d.get("result") or {}
        data = r.get("data") or []
        rows.extend(data)
        if page >= int(r.get("pages") or 1) or not data:
            break
        page += 1
    payload = {"table": key, "report": report, "year": year, "n": len(rows), "rows": rows,
               "source": "eastmoney_datacenter " + report, "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    tmp = dest + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
    os.replace(tmp, dest)
    return key, year, len(rows)


def main():
    ensure_v38l4()
    jobs = [(k, y) for y in YEARS for k in TABLES]
    todo = [j for j in jobs if not os.path.isfile(os.path.join(RAW, "%s_%d.json.gz" % j))]
    print("V38L4_DL total", len(jobs), "todo", len(todo), flush=True)
    n_done, n_fail = 0, 0
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        futs = [ex.submit(fetch_table, k, y) for k, y in todo]
        for f in as_completed(futs):
            try:
                k, y, n = f.result()
                n_done += 1
                print("V38L4_DL", n_done, "/", len(todo), k, y, n, flush=True)
            except Exception as e:  # noqa
                n_fail += 1
                print("V38L4_DL_FAIL", repr(e)[:200], flush=True)
    print("V38L4_DL_DONE", n_done, "fail", n_fail, flush=True)
    return n_fail


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
