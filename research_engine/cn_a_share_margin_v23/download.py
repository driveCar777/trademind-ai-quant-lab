"""Download per-date margin detail (all stocks) from Eastmoney datacenter. Resumable. Threaded. No key."""
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

from research_engine.cn_a_share_margin_v23 import RAW, CALENDAR, START, END

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
HDR = {"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}
BASE = "https://datacenter-web.eastmoney.com/api/data/v1/get"
THREADS = int(os.environ.get("TRADEMIND_MARGIN_THREADS", "6"))


def trading_days():
    days = []
    with open(CALENDAR, "r", encoding="utf-8") as f:
        hdr = f.readline().strip().split(",")
        ix = {h: i for i, h in enumerate(hdr)}
        dcol = ix.get("calendar_date", ix.get("date", 0))
        tcol = ix.get("is_trading_day", ix.get("is_trading", None))
        for line in f:
            p = line.strip().split(",")
            d = p[dcol][:10]
            if tcol is not None and p[tcol] not in ("1", "True", "true"):
                continue
            if START <= d <= END:
                days.append(d)
    return sorted(set(days))


def fetch_page(date, page):
    q = {
        "reportName": "RPTA_WEB_RZRQ_GGMX", "columns": "ALL", "source": "WEB",
        "sortColumns": "SCODE", "sortTypes": "1", "pageSize": "500", "pageNumber": str(page),
        "filter": "(DATE='%s')" % date,
    }
    url = BASE + "?" + urllib.parse.urlencode(q)
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=60, context=CTX) as h:
                return json.loads(h.read().decode("utf-8"))
        except Exception as e:  # noqa
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("fetch failed %s p%d: %s" % (date, page, last))


def fetch_date(date):
    dest = os.path.join(RAW, date + ".json.gz")
    if os.path.isfile(dest):
        return date, "skip", 0
    j = fetch_page(date, 1)
    res = j.get("result")
    rows = []
    if res and res.get("data"):
        rows.extend(res["data"])
        for p in range(2, int(res.get("pages", 1)) + 1):
            jp = fetch_page(date, p)
            rp = jp.get("result")
            if rp and rp.get("data"):
                rows.extend(rp["data"])
    payload = {"date": date, "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "source": "eastmoney_datacenter RPTA_WEB_RZRQ_GGMX", "n": len(rows), "rows": rows}
    tmp = dest + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, dest)
    return date, "ok", len(rows)


def main():
    os.makedirs(RAW, exist_ok=True)
    days = trading_days()
    todo = [d for d in days if not os.path.isfile(os.path.join(RAW, d + ".json.gz"))]
    print("trading days", len(days), "todo", len(todo), "threads", THREADS, flush=True)
    done = 0
    fails = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        futs = {ex.submit(fetch_date, d): d for d in todo}
        for fut in as_completed(futs):
            d = futs[fut]
            try:
                _, st, n = fut.result()
                done += 1
                if done % 50 == 0:
                    print("PROGRESS", done, "/", len(todo), d, n, "rows", round(time.time() - t0), "s", flush=True)
            except Exception as e:  # noqa
                fails.append({"date": d, "err": str(e)[:200]})
                print("FAIL", d, str(e)[:120], flush=True)
    with open(os.path.join(RAW, "_FAILED.json"), "w", encoding="utf-8") as f:
        json.dump(fails, f, indent=1)
    print("DONE", done, "fails", len(fails), round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()
