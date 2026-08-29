#!/usr/bin/env python3
"""Submit Pack E batch jobs and download to D: raw/. Never prints the key."""
from __future__ import print_function

import hashlib
import json
import os
import sys
import time
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.data_sources.databento import DATASET, HistoricalClient
from research_engine.local_fs import force_project_temp
from research_engine.v6_external.env import databento_api_key, has_databento_key


START = "2010-06-06"
END = "2026-08-29"
SYMBOLS = ["GC.FUT", "CL.FUT"]
SCHEMAS = ("ohlcv-1d", "definition", "statistics")
RAW_DIR = os.path.join(ROOT, "data", "market", "raw", "databento", "pack_e")
STATE = os.path.join(
    ROOT, "data", "market", "research_engine", "external", "V61_ACQUIRE_STATE.json"
)


def _write(path, payload):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(path, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()


def _scrub(job):
    if not isinstance(job, dict):
        return job
    out = dict(job)
    out.pop("api_key", None)
    return out


def _sha256_file(path):
    digest = hashlib.sha256()
    handle = open(path, "rb")
    try:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        handle.close()
    return digest.hexdigest()


def download_url(url, dest, key):
    import requests

    if not os.path.isdir(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    resp = requests.get(url, auth=(key, ""), stream=True, timeout=3600)
    resp.raise_for_status()
    handle = open(dest, "wb")
    try:
        for chunk in resp.iter_content(1024 * 1024):
            if chunk:
                handle.write(chunk)
    finally:
        handle.close()
        resp.close()
    return os.path.getsize(dest)


def main():
    force_project_temp()
    print("KEY_PRESENT =", "true" if has_databento_key() else "false")
    if not has_databento_key():
        print("STOP = CREDENTIAL_REQUIRED")
        return 2
    if not os.path.isdir(RAW_DIR):
        os.makedirs(RAW_DIR)
    key = databento_api_key()
    client = HistoricalClient(key, timeout=180)
    if os.path.isfile(STATE):
        handle = open(STATE, encoding="utf-8")
        try:
            state = json.load(handle)
        finally:
            handle.close()
    else:
        state = {
            "jobs": {},
            "files": [],
            "started_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    for schema in SCHEMAS:
        if schema in state.get("jobs") or {}:
            print("JOB_REUSE", schema, state["jobs"][schema].get("id"))
            continue
        job = client.submit_batch(DATASET, schema, SYMBOLS, START, END, "parent")
        state["jobs"][schema] = _scrub(job)
        _write(STATE, state)
        print("JOB_SUBMIT", schema, job.get("id"), job.get("state"))
    pending = True
    while pending:
        pending = False
        listed = client.list_jobs("queued,processing,done")
        by_id = {}
        for item in listed:
            by_id[item.get("id")] = _scrub(item)
        for schema, job in list(state["jobs"].items()):
            jid = job.get("id")
            fresh = by_id.get(jid) or job
            state["jobs"][schema] = fresh
            st = str(fresh.get("state") or "")
            print("JOB", schema, jid, st, "progress", fresh.get("progress"), "cost", fresh.get("cost_usd"))
            if st not in ("done", "expired"):
                pending = True
        _write(STATE, state)
        if pending:
            time.sleep(30)
    downloaded = []
    for schema, job in state["jobs"].items():
        jid = job.get("id")
        files = client.list_files(jid)
        for item in files:
            name = item.get("filename") or "file"
            urls = item.get("urls") or {}
            url = urls.get("https")
            if not url:
                continue
            dest = os.path.join(RAW_DIR, jid, name)
            if os.path.isfile(dest) and os.path.getsize(dest) == int(item.get("size") or 0):
                print("FILE_REUSE", schema, name, os.path.getsize(dest))
            else:
                print("FILE_GET", schema, name)
                download_url(url, dest, key)
            downloaded.append(
                {
                    "schema": schema,
                    "job_id": jid,
                    "filename": name,
                    "path": dest,
                    "bytes": os.path.getsize(dest),
                    "sha256": _sha256_file(dest),
                    "vendor_hash": item.get("hash"),
                }
            )
    state["files"] = downloaded
    state["finished_at_utc"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    state["KEY_PRESENT"] = True
    state["FINAL_OOS_TOUCHED"] = False
    _write(STATE, state)
    print("ACQUIRED_FILES", len(downloaded))
    print("RAW_DIR", RAW_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
