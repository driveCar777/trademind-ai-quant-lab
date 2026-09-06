"""Pull SHFE/INE warehouse receipts DIRECT. python -m research_engine.cn_warehouse_v37.pull"""
from __future__ import print_function

import json
import os
import ssl
import time
import urllib.request

import numpy as np

from research_engine.cn_futures_v31.pack import load_pack
from research_engine.cn_warehouse_v37 import RAW, WH_MAP, ensure, map_varname

TAG = "V37_PULL"
URL = "https://www.shfe.com.cn/data/tradedata/future/dailydata/{d}dailystock.dat"
HDR = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.shfe.com.cn/"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
START = "2014-05-19"


def _opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=CTX))


def fetch_day(opener, ymd):
    path = os.path.join(RAW, ymd + ".json")
    if os.path.isfile(path) and os.path.getsize(path) > 20:
        return json.load(open(path, encoding="utf-8")), "CACHE"
    url = URL.format(d=ymd.replace("-", ""))
    try:
        req = urllib.request.Request(url, headers=HDR)
        with opener.open(req, timeout=25) as r:
            raw = r.read()
        j = json.loads(raw.decode("utf-8", "replace"))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(raw.decode("utf-8", "replace"))
        return j, "OK"
    except Exception as e:
        return None, type(e).__name__ + ":" + str(e)[:80]


def parse_totals(j):
    out = dict((p, 0.0) for p in WH_MAP.values())
    seen = set()
    rows = (j or {}).get("o_cursor") or []
    for x in rows:
        p = map_varname(str(x.get("VARNAME") or ""))
        if not p:
            continue
        try:
            w = float(x.get("WRTWGHTS") or 0)
        except (TypeError, ValueError):
            w = 0.0
        out[p] += w
        seen.add(p)
    return out, seen


def main():
    ensure()
    P = load_pack()
    dates = [d for d in P["dates"] if d >= START]
    opener = _opener()
    ok = miss = 0
    for i, d in enumerate(dates):
        j, st = fetch_day(opener, d)
        if j is None:
            miss += 1
        else:
            ok += 1
        if i % 200 == 0:
            print(TAG, i, "/", len(dates), d, st, "ok", ok, "miss", miss, flush=True)
        if st not in ("CACHE", "OK") and "HTTPError" not in st:
            time.sleep(0.4)
        elif st == "OK":
            time.sleep(0.05)
    print(TAG, "DONE days", len(dates), "ok", ok, "miss", miss, flush=True)


if __name__ == "__main__":
    main()
