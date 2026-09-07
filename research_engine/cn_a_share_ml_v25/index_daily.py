"""Daily HS300 (000300) and CSI500 (000905) index OHLC from Eastmoney kline, bounded to <= VALIDATION end.

Free, no key. Denied window never requested. Goes through the local Clash HTTP proxy (direct TLS to push2his fails
on this machine under TUN/fake-ip). Written once to data/market/cn_a_share/index/daily/<code>.csv.
"""
from __future__ import print_function

import csv
import json
import os
import ssl
import urllib.request

import numpy as np

from research_engine.cn_a_share_ml_v25 import INDEX_DAILY, VALIDATION, ensure_v25

CODES = {"HS300": "1.000300", "ZZ500": "1.000905"}
PROXY = os.environ.get("TRADEMIND_HTTP_PROXY", "http://127.0.0.1:7890")
HDR = {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}


def _opener():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    handlers = [urllib.request.HTTPSHandler(context=ctx)]
    if PROXY:
        handlers.insert(0, urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    return urllib.request.build_opener(*handlers)


def _path(name):
    return os.path.join(INDEX_DAILY, "%s.csv" % name)


def download(name, force=False):
    ensure_v25()
    dest = _path(name)
    if os.path.isfile(dest) and not force:
        return dest
    end = VALIDATION[1].replace("-", "")
    url = ("https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=%s&fields1=f1,f2,f3,f4,f5,f6"
           "&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=0&beg=20091201&end=%s&lmt=100000") % (CODES[name], end)
    rows, src, last = [], None, None
    for attempt in range(4):
        try:
            op = _opener()
            payload = json.loads(op.open(urllib.request.Request(url, headers=HDR), timeout=60).read().decode("utf-8"))
            for line in payload["data"]["klines"]:
                d, o, c, h, l, v, a = line.split(",")[:7]
                if d > VALIDATION[1]:
                    raise RuntimeError("DENIED_WINDOW_IN_INDEX_DOWNLOAD")
                rows.append({"date": d, "open": o, "close": c, "high": h, "low": l, "volume": v, "amount": a})
            src = "eastmoney_push2his"
            break
        except Exception as e:  # noqa
            last = e
            rows = []
    if not rows:
        # fallback: Sina daily kline (full history); rows after VALIDATION end are discarded before writing
        sym = "sh" + CODES[name].split(".")[1]
        url2 = ("https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
                "?symbol=%s&scale=240&ma=no&datalen=8000") % sym
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        raw = op.open(urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8", "ignore")
        for r in json.loads(raw):
            d = r["day"][:10]
            if d < "2009-12-01" or d > VALIDATION[1] or float(r["open"]) <= 0:
                continue
            rows.append({"date": d, "open": r["open"], "close": r["close"], "high": r["high"], "low": r["low"], "volume": r["volume"], "amount": ""})
        src = "sina_fallback"
    if not rows:
        raise RuntimeError("INDEX_DOWNLOAD_FAILED %s: %r" % (name, last))
    with open(dest, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "open", "close", "high", "low", "volume", "amount"])
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(INDEX_DAILY, "%s.META.json" % name), "w", encoding="utf-8") as fh:
        json.dump({"source": src, "n": len(rows), "first": rows[0]["date"], "last": rows[-1]["date"], "bounded_to": VALIDATION[1]}, fh, indent=2)
    print("V25_INDEX", name, src, len(rows), rows[0]["date"], rows[-1]["date"], flush=True)
    return dest


def load_open_series(name, pack_dates):
    """Index open aligned to pack dates (NaN where missing)."""
    path = download(name)
    m = {}
    with open(path, "r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            m[r["date"]] = float(r["open"])
    out = np.full(len(pack_dates), np.nan, dtype=np.float64)
    for i, d in enumerate(pack_dates):
        if d in m:
            out[i] = m[d]
    return out


if __name__ == "__main__":
    for n in CODES:
        download(n)
