"""Download 业绩预告 / 业绩快报 per report period (all stocks, paginated) from Eastmoney datacenter. Resumable, threaded, no key.

Only report periods <= 2023-12-31 are requested; rows with NOTICE_DATE > NOTICE_CUTOFF or implausible notice lag are dropped
at compile time.
"""
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

from research_engine.cn_a_share_preann_v38 import RAW, REPORTS, REPORT_DATES, ensure_v38l1

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
HDR = {"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}
BASE = "https://datacenter-web.eastmoney.com/api/data/v1/get"
THREADS = int(os.environ.get("TRADEMIND_PREANN_THREADS", "4"))
PAGE = 500


def fetch_page(report, datecol, rdate, page):
    q = {"reportName": report, "columns": "ALL", "source": "WEB", "client": "WEB", "sortColumns": "SECURITY_CODE,NOTICE_DATE",
         "sortTypes": "1,1", "pageSize": str(PAGE), "pageNumber": str(page), "filter": "(%s='%s')" % (datecol, rdate)}
    url = BASE + "?" + urllib.parse.urlencode(q)
    last = None
    for attempt in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=60, context=CTX) as h:
                return json.loads(h.read().decode("utf-8"))
        except Exception as e:  # noqa
            last = e
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError("fetch failed %s %s p%d: %s" % (report, rdate, page, last))


def fetch_table(key, rdate):
    report, datecol = REPORTS[key]
    dest = os.path.join(RAW, "%s_%s.json.gz" % (key, rdate))
    if os.path.isfile(dest):
        return key, rdate, -1
    rows, page = [], 1
    while True:
        d = fetch_page(report, datecol, rdate, page)
        r = d.get("result") or {}
        data = r.get("data") or []
        rows.extend(data)
        if page >= int(r.get("pages") or 1) or not data:
            break
        page += 1
    payload = {"table": key, "report": report, "report_date": rdate, "n": len(rows), "rows": rows,
               "source": "eastmoney_datacenter " + report, "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    tmp = dest + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
    os.replace(tmp, dest)
    return key, rdate, len(rows)


def main(only=None):
    ensure_v38l1()
    dates = [d for d in REPORT_DATES if (only is None or d in only)]
    jobs = [(k, d) for d in dates for k in REPORTS]
    todo = [j for j in jobs if not os.path.isfile(os.path.join(RAW, "%s_%s.json.gz" % j))]
    print("V38L1_DL total", len(jobs), "todo", len(todo), flush=True)
    n_done, n_fail = 0, 0
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        futs = [ex.submit(fetch_table, k, d) for k, d in todo]
        for f in as_completed(futs):
            try:
                k, d, n = f.result()
                n_done += 1
                print("V38L1_DL", n_done, "/", len(todo), k, d, n, flush=True)
            except Exception as e:  # noqa
                n_fail += 1
                print("V38L1_DL_FAIL", repr(e)[:200], flush=True)
    print("V38L1_DL_DONE", n_done, "fail", n_fail, flush=True)
    return n_fail


if __name__ == "__main__":
    only = set(a for a in sys.argv[1:] if a[:1] != "-") or None
    sys.exit(1 if main(only) else 0)
