"""Download 中登 weekly pledge snapshots (RPT_CSDC_LIST) per calendar year, paginated. Resumable, threaded, no key."""
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

from research_engine.cn_a_share_pledge_v38 import RAW, REPORT, YEARS, ensure_v38l7

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
HDR = {"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}
BASE = "https://datacenter-web.eastmoney.com/api/data/v1/get"
THREADS = int(os.environ.get("TRADEMIND_PLEDGE_THREADS", "6"))
PAGE = 500
KEEP = ("SECURITY_CODE", "TRADE_DATE", "PLEDGE_RATIO", "REPURCHASE_BALANCE", "PLEDGE_DEAL_NUM", "PLEDGE_MARKET_CAP",
        "REPURCHASE_UNLIMITED_BALANCE", "REPURCHASE_LIMITED_BALANCE")


def fetch_page(year, page):
    report, datecol = REPORT
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
    raise RuntimeError("fetch failed %d p%d: %s" % (year, page, last))


def fetch_year_part(year, first_page, last_page):
    rows = []
    for page in range(first_page, last_page + 1):
        d = fetch_page(year, page)
        data = (d.get("result") or {}).get("data") or []
        rows.extend([dict((k, r.get(k)) for k in KEEP) for r in data])
        if not data:
            break
    return rows


def fetch_year(year):
    dest = os.path.join(RAW, "PLEDGE_%d.json.gz" % year)
    if os.path.isfile(dest):
        return year, -1
    d0 = fetch_page(year, 1)
    r0 = d0.get("result") or {}
    pages = int(r0.get("pages") or 1)
    rows = [dict((k, r.get(k)) for k in KEEP) for r in (r0.get("data") or [])]
    if pages > 1:
        chunks, step = [], max(1, (pages - 1) // THREADS + 1)
        p = 2
        while p <= pages:
            chunks.append((p, min(pages, p + step - 1)))
            p += step
        with ThreadPoolExecutor(max_workers=THREADS) as ex:
            for part in ex.map(lambda c: fetch_year_part(year, c[0], c[1]), chunks):
                rows.extend(part)
    payload = {"report": REPORT[0], "year": year, "n": len(rows), "expected": int(r0.get("count") or 0), "rows": rows,
               "source": "eastmoney_datacenter " + REPORT[0], "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    tmp = dest + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
    os.replace(tmp, dest)
    return year, len(rows)


def main():
    ensure_v38l7()
    todo = [y for y in YEARS if not os.path.isfile(os.path.join(RAW, "PLEDGE_%d.json.gz" % y))]
    print("V38L7_DL total", len(YEARS), "todo", len(todo), flush=True)
    n_fail = 0
    for y in todo:
        try:
            yy, n = fetch_year(y)
            print("V38L7_DL", yy, n, flush=True)
        except Exception as e:  # noqa
            n_fail += 1
            print("V38L7_DL_FAIL", y, repr(e)[:200], flush=True)
    print("V38L7_DL_DONE fail", n_fail, flush=True)
    return n_fail


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
