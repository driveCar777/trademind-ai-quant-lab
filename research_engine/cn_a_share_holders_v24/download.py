"""Download per-stock shareholder-count history (all reports) from Eastmoney datacenter. Resumable. Threaded."""
from __future__ import print_function

import gzip
import json
import os
import ssl
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from research_engine.cn_a_share_holders_v24 import RAW, ensure_v24

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
HDR = {"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}
BASE = "https://datacenter-web.eastmoney.com/api/data/v1/get"
THREADS = int(os.environ.get("TRADEMIND_HOLDERS_THREADS", "6"))
CACHE_SYMBOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                             "data", "market", "cn_a_share", "alpha_cache", "v13_000002", "symbols.npy")


def fetch(code):
    q = {"reportName": "RPT_HOLDERNUM_DET", "columns": "ALL", "source": "WEB", "sortColumns": "END_DATE",
         "sortTypes": "-1", "pageSize": "500", "pageNumber": "1", "filter": '(SECURITY_CODE="%s")' % code}
    url = BASE + "?" + urllib.parse.urlencode(q)
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=60, context=CTX) as h:
                j = json.loads(h.read().decode("utf-8"))
            if j.get("success") is False and j.get("code") not in (9201,):  # 9201 = no data
                raise RuntimeError("api %s %s" % (j.get("code"), j.get("message")))
            return j
        except Exception as e:  # noqa
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("fetch failed %s: %s" % (code, last))


def one(symbol):
    code = symbol.split(".")[-1]
    dest = os.path.join(RAW, symbol + ".json.gz")
    if os.path.isfile(dest):
        return symbol, "skip", 0
    j = fetch(code)
    rows = ((j.get("result") or {}).get("data")) or []
    payload = {"symbol": symbol, "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "source": "eastmoney_datacenter RPT_HOLDERNUM_DET", "n": len(rows), "rows": rows}
    tmp = dest + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, dest)
    return symbol, "ok", len(rows)


def main():
    ensure_v24()
    symbols = [str(s) for s in np.load(CACHE_SYMBOLS, allow_pickle=True)]
    todo = [s for s in symbols if not os.path.isfile(os.path.join(RAW, s + ".json.gz"))]
    print("symbols", len(symbols), "todo", len(todo), "threads", THREADS, flush=True)
    done, fails, t0 = 0, [], time.time()
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        futs = {ex.submit(one, s): s for s in todo}
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                _, st, n = fut.result()
                done += 1
                if done % 200 == 0:
                    print("PROGRESS", done, "/", len(todo), s, n, round(time.time() - t0), "s", flush=True)
            except Exception as e:  # noqa
                fails.append({"symbol": s, "err": str(e)[:200]})
                print("FAIL", s, str(e)[:120], flush=True)
    with open(os.path.join(RAW, "_FAILED.json"), "w", encoding="utf-8") as f:
        json.dump(fails, f, indent=1)
    print("DONE", done, "fails", len(fails), round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()
