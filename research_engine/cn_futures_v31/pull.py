"""V31 stage A puller (Sina). Continuous series first (fast), then per-contract enumeration (slow, resumable).

python -m research_engine.cn_futures_v31.pull continuous
python -m research_engine.cn_futures_v31.pull contracts [--threads 3]
python -m research_engine.cn_futures_v31.pull manifest
"""
from __future__ import print_function

import argparse
import csv
import hashlib
import json
import os
import re
import ssl
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from research_engine.cn_futures_v31 import ALL_PRODUCTS, CONTRACT_YYMM_FROM, CONTRACT_YYMM_TO, DATA, DATASET_ID, EXCHANGE_OF

TAG = "V31_PULL"
URL = "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20_x=/InnerFuturesNewService.getDailyKLine?symbol={sym}"
HDR = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/futuremarket/"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
COLS = ("date", "open", "high", "low", "close", "volume", "open_interest", "settle")
_lock = threading.Lock()


def fetch(sym, tries=4):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(URL.format(sym=sym), headers=HDR)
            with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
                b = r.read().decode("utf-8", "replace")
            m = re.search(r"var _x=\((.*)\);\s*$", b, re.S)
            if not m:
                return None, "NO_PAYLOAD"
            body = m.group(1).strip()
            if body in ("null", "", "[]"):
                return [], "EMPTY"
            rows = json.loads(body)
            if isinstance(rows, dict):
                return None, "ERR:" + str(rows.get("__ERRORMSG", rows))[:60]
            return rows, "OK"
        except Exception as e:  # SSL EOF / timeouts happen; back off
            last = repr(e)[:80]
            time.sleep(3 + 4 * k)
    return None, "FAIL:" + (last or "")


def write_rows(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in rows:
            w.writerow([r.get("d"), r.get("o"), r.get("h"), r.get("l"), r.get("c"), r.get("v"), r.get("p"), r.get("s")])


def _log(path, rec):
    with _lock:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def pull_continuous():
    d = os.path.join(DATA, "continuous")
    os.makedirs(d, exist_ok=True)
    log = os.path.join(DATA, "continuous_log.jsonl")
    for p in ALL_PRODUCTS:
        out = os.path.join(d, p + "0.csv")
        if os.path.isfile(out):
            continue
        rows, st = fetch(p + "0")
        rec = {"symbol": p + "0", "exchange": EXCHANGE_OF[p], "status": st, "n": len(rows) if rows else 0,
               "first": rows[0]["d"] if rows else None, "last": rows[-1]["d"] if rows else None}
        if rows:
            write_rows(out, rows)
        _log(log, rec)
        print(TAG, "CONT", rec, flush=True)
        time.sleep(1.0)


def _yymm_range():
    y0, m0 = int(CONTRACT_YYMM_FROM[:2]), int(CONTRACT_YYMM_FROM[2:])
    y1, m1 = int(CONTRACT_YYMM_TO[:2]), int(CONTRACT_YYMM_TO[2:])
    out = []
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        out.append("%02d%02d" % (y, m))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def pull_contracts(threads=3):
    d = os.path.join(DATA, "contracts")
    os.makedirs(d, exist_ok=True)
    log = os.path.join(DATA, "contracts_log.jsonl")
    done = set()
    if os.path.isfile(log):
        with open(log, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["symbol"])
                except Exception:
                    pass
    jobs = [p + ym for p in ALL_PRODUCTS for ym in _yymm_range() if (p + ym) not in done]
    print(TAG, "contracts to try", len(jobs), "already", len(done), flush=True)

    def one(sym):
        rows, st = fetch(sym)
        rec = {"symbol": sym, "status": st, "n": len(rows) if rows else 0, "first": rows[0]["d"] if rows else None, "last": rows[-1]["d"] if rows else None}
        if rows:
            write_rows(os.path.join(d, sym + ".csv"), rows)
        _log(log, rec)
        time.sleep(0.5)
        return rec

    n_ok = 0
    with ThreadPoolExecutor(max_workers=threads) as ex:
        for i, rec in enumerate(ex.map(one, jobs)):
            n_ok += 1 if rec["n"] else 0
            if i % 50 == 0:
                print(TAG, "CONTRACTS", i, "/", len(jobs), "with_bars", n_ok, flush=True)
    print(TAG, "CONTRACTS DONE with_bars", n_ok, flush=True)


def manifest():
    files = []
    for sub in ("continuous", "contracts"):
        d = os.path.join(DATA, sub)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            path = os.path.join(d, fn)
            h = hashlib.sha256()
            n = -1
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
                    n += chunk.count(b"\n")
            files.append({"file": sub + "/" + fn, "sha256": h.hexdigest(), "rows": n})
    man = {"dataset_id": DATASET_ID, "source": "sina InnerFuturesNewService.getDailyKLine", "columns": list(COLS), "products_declared": ALL_PRODUCTS,
           "contract_enumeration": [CONTRACT_YYMM_FROM, CONTRACT_YYMM_TO], "n_files": len(files), "row_count": sum(f["rows"] for f in files),
           "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "overwrite_frozen": False, "FINAL_OOS_LOCKED": False, "files": files,
           "note": "continuous XX0 = Sina dominant-contract splice (not roll-adjusted); per-contract series retained by Sina only from ~2019-05"}
    man["sha256"] = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    with open(os.path.join(DATA, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)
    print(TAG, "MANIFEST", man["n_files"], "files", man["row_count"], "rows", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("continuous", "contracts", "manifest"))
    ap.add_argument("--threads", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    if a.stage == "continuous":
        pull_continuous()
    elif a.stage == "contracts":
        pull_contracts(a.threads)
    else:
        manifest()
