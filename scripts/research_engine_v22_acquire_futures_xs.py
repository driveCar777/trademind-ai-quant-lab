#!/usr/bin/env python3
"""V22 acquire: 30 CME roots, ohlcv-1d, all contract months, 2010-06-06 -> 2026-08-29.

Re-quotes, refuses if cost > HARD_CAP, refuses if the immutable dataset already exists
(no double charge), submits ONE batch job, polls, downloads, hashes, freezes.
Never prints the key.
"""
from __future__ import print_function

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.data_sources.databento import HistoricalClient, _basic_auth  # noqa: E402
from research_engine.io_util import dump_json  # noqa: E402
from research_engine.local_fs import force_project_temp  # noqa: E402
from research_engine.v6_external.env import databento_api_key, has_databento_key  # noqa: E402

try:
    from urllib.request import Request
except ImportError:  # pragma: no cover
    from urllib2 import Request

DATASET = "GLBX.MDP3"
SCHEMA = "ohlcv-1d"
START = "2010-06-06"
END = "2026-08-29"
ROOTS = [
    "ES.FUT", "NQ.FUT", "YM.FUT", "RTY.FUT",
    "ZN.FUT", "ZB.FUT", "ZF.FUT", "ZT.FUT",
    "6E.FUT", "6J.FUT", "6B.FUT", "6A.FUT", "6C.FUT", "6S.FUT",
    "GC.FUT", "SI.FUT", "HG.FUT", "PL.FUT",
    "CL.FUT", "NG.FUT", "HO.FUT", "RB.FUT",
    "ZC.FUT", "ZS.FUT", "ZW.FUT", "ZM.FUT", "ZL.FUT",
    "LE.FUT", "HE.FUT", "GF.FUT",
]
HARD_CAP_USD = 50.0
DATASET_ID = "tm-fut-GLBX-XS30-D1-20260904-000001"
IMM = os.path.join(ROOT, "data", "market", "immutable", DATASET_ID)
STATE = os.path.join(ROOT, "data", "market", "research_engine", "databento_eval_v22", "ACQUIRE_STATE.json")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def save_state(d):
    d["utc"] = now()
    dump_json(STATE, d)


def download(client, job_id, filename, dest, url=None):
    url = url or "https://hist.databento.com/v0/batch.download/%s/%s" % (job_id, filename)
    req = Request(url)
    req.add_header("Authorization", _basic_auth(client.api_key))
    h = hashlib.sha256()
    size = 0
    handle = client.opener.open(req, timeout=900)
    try:
        with open(dest, "wb") as f:
            while True:
                chunk = handle.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                h.update(chunk)
                size += len(chunk)
    finally:
        handle.close()
    return h.hexdigest(), size


def main():
    force_project_temp()
    if not has_databento_key():
        print("STOP CREDENTIAL_REQUIRED")
        return 2
    if os.path.isdir(IMM) and os.path.isfile(os.path.join(IMM, "manifest.json")):
        print("STOP IMMUTABLE_EXISTS", DATASET_ID)
        return 3
    client = HistoricalClient(databento_api_key(), timeout=300)
    state = {}
    if os.path.isfile(STATE):
        with open(STATE, "r", encoding="utf-8") as f:
            state = json.load(f)
    job_id = state.get("job_id")
    if not job_id:
        cost = float(client.get_cost(DATASET, SCHEMA, ROOTS, START, END, "parent"))
        print("QUOTE_USD", cost)
        if cost > HARD_CAP_USD:
            save_state({"status": "PAYMENT_REQUIRED", "cost_usd": cost, "cap": HARD_CAP_USD})
            print("STOP PAYMENT_REQUIRED")
            return 4
        job = client.submit_batch(DATASET, SCHEMA, ROOTS, START, END, "parent")
        job_id = job.get("id")
        save_state({"status": "SUBMITTED", "job_id": job_id, "cost_usd": cost, "job": job})
        print("SUBMITTED", job_id, job.get("state"))
    # poll
    deadline = time.time() + 3600
    files = None
    while time.time() < deadline:
        jobs = client.list_jobs("received,queued,processing,done")
        mine = [j for j in jobs if j.get("id") == job_id]
        st = mine[0].get("state") if mine else "unknown"
        print("POLL", now(), st)
        if st == "done":
            files = client.list_files(job_id)
            break
        if st in ("expired", "failed"):
            save_state({"status": "JOB_" + st.upper(), "job_id": job_id})
            return 5
        time.sleep(20)
    if files is None:
        save_state({"status": "TIMEOUT_POLL", "job_id": job_id})
        return 6
    raw_dir = os.path.join(IMM, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    got = []
    for fmeta in files:
        fn = fmeta.get("filename")
        dest = os.path.join(raw_dir, fn)
        if os.path.isfile(dest) and fmeta.get("size") and os.path.getsize(dest) == fmeta.get("size"):
            digest = hashlib.sha256(open(dest, "rb").read()).hexdigest()
            size = os.path.getsize(dest)
        else:
            digest, size = download(client, job_id, fn, dest, (fmeta.get("urls") or {}).get("https"))
        vendor_hash = (fmeta.get("hash") or "")
        got.append({"filename": fn, "bytes": size, "sha256": digest, "vendor_hash": vendor_hash})
        print("GOT", fn, size)
    manifest = {
        "dataset_id": DATASET_ID,
        "acquisition": "V22_FUTURES_XS30",
        "source": "databento",
        "vendor": "Databento",
        "dataset": DATASET,
        "schema": SCHEMA,
        "symbols": ROOTS,
        "stype_in": "parent",
        "stype_out": "instrument_id",
        "map_symbols": True,
        "start": START,
        "end": END,
        "encoding": "csv",
        "compression": "zstd",
        "split_duration": "year",
        "job_id": job_id,
        "cost_usd": state.get("cost_usd"),
        "retrieval_time_utc": now(),
        "license": "Databento + CME historical internal research; no raw redistribution",
        "knowledge_time_rule": "ohlcv-1d session bar known at session close T 21:00Z (electronic); front contract = max volume per root per day",
        "overwrite_frozen": False,
        "FINAL_OOS_LOCKED": False,
        "files": got,
    }
    dump_json(os.path.join(IMM, "manifest.json"), manifest)
    dump_json(os.path.join(ROOT, "data", "market", "manifests", DATASET_ID + ".json"), manifest)
    save_state({"status": "ACQUIRED", "job_id": job_id, "cost_usd": state.get("cost_usd"), "n_files": len(got), "dataset_id": DATASET_ID})
    print("ACQUIRED", DATASET_ID, len(got), "files")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
