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

from research_engine.data_sources.databento import DATASET, DatabentoHttpError, HistoricalClient
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
    """Stream a batch file. Clash 7890 if live, else direct. Never a dead proxy."""
    import requests

    from research_engine.data_sources.databento import live_https_proxy

    parent = os.path.dirname(dest)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    tmp = dest + ".part"
    proxy = live_https_proxy()
    proxies = {"http": proxy, "https": proxy} if proxy else {"http": None, "https": None}
    last = None
    for attempt in range(4):
        try:
            sess = requests.Session()
            sess.trust_env = False
            resp = sess.get(
                url,
                auth=(key, ""),
                stream=True,
                timeout=3600,
                proxies=proxies,
            )
            resp.raise_for_status()
            handle = open(tmp, "wb")
            try:
                for chunk in resp.iter_content(1024 * 1024):
                    if chunk:
                        handle.write(chunk)
            finally:
                handle.close()
                resp.close()
                sess.close()
            if os.path.isfile(dest):
                os.remove(dest)
            os.rename(tmp, dest)
            return os.path.getsize(dest)
        except Exception as exc:
            last = exc
            if os.path.isfile(tmp):
                os.remove(tmp)
    raise last


def _log(*parts):
    print(*parts)
    sys.stdout.flush()


def main():
    force_project_temp()
    _log("KEY_PRESENT =", "true" if has_databento_key() else "false")
    if not has_databento_key():
        _log("STOP = CREDENTIAL_REQUIRED")
        return 2
    if not os.path.isdir(RAW_DIR):
        os.makedirs(RAW_DIR)
    key = databento_api_key()
    from research_engine.data_sources.databento import live_https_proxy, _port_open

    proxy = live_https_proxy()
    clash = _port_open("127.0.0.1", 7890)
    _log(
        "HTTPS_ROUTE",
        proxy if proxy else "APP_DIRECT",
        "CLASH_7890",
        "listen" if clash else "down",
    )
    client = HistoricalClient(key, timeout=60)
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
            _log("JOB_REUSE", schema, state["jobs"][schema].get("id"))
            continue
        job = client.submit_batch(DATASET, schema, SYMBOLS, START, END, "parent")
        state["jobs"][schema] = _scrub(job)
        _write(STATE, state)
        _log("JOB_SUBMIT", schema, job.get("id"), job.get("state"))
    downloaded = list(state.get("files") or [])
    have = set()
    for row in downloaded:
        have.add("%s/%s" % (row.get("job_id"), row.get("filename")))
    pending = True
    while pending:
        pending = False
        try:
            listed = client.list_jobs("queued,processing,done")
            by_id = {}
            for item in listed:
                by_id[item.get("id")] = _scrub(item)
            for schema, job in list(state["jobs"].items()):
                jid = job.get("id")
                fresh = by_id.get(jid) or job
                state["jobs"][schema] = fresh
                st = str(fresh.get("state") or "")
                _log("JOB", schema, jid, st, "progress", fresh.get("progress"), "cost", fresh.get("cost_usd"))
                if st == "done":
                    files = client.list_files(jid)
                    for item in files:
                        name = item.get("filename") or "file"
                        key_name = "%s/%s" % (jid, name)
                        dest = os.path.join(RAW_DIR, jid, name)
                        expected = int(item.get("size") or 0)
                        if key_name in have and os.path.isfile(dest):
                            continue
                        urls = item.get("urls") or {}
                        url = urls.get("https")
                        if not url:
                            continue
                        if os.path.isfile(dest) and expected and os.path.getsize(dest) == expected:
                            _log("FILE_REUSE", schema, name, os.path.getsize(dest))
                        else:
                            _log("FILE_GET", schema, name, "bytes", expected)
                            download_url(url, dest, key)
                            _log("FILE_OK", schema, name, os.path.getsize(dest))
                        row = {
                            "schema": schema,
                            "job_id": jid,
                            "filename": name,
                            "path": dest,
                            "bytes": os.path.getsize(dest),
                            "sha256": _sha256_file(dest),
                            "vendor_hash": item.get("hash"),
                        }
                        downloaded.append(row)
                        have.add(key_name)
                        state["files"] = downloaded
                        _write(STATE, state)
                elif st not in ("expired",):
                    pending = True
            _write(STATE, state)
        except Exception as exc:
            _log("POLL_RETRY", type(exc).__name__, str(exc)[:160])
            pending = True
        if pending:
            time.sleep(30)
    state["files"] = downloaded
    state["finished_at_utc"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    state["KEY_PRESENT"] = True
    state["FINAL_OOS_TOUCHED"] = False
    _write(STATE, state)
    _log("ACQUIRED_FILES", len(downloaded))
    _log("RAW_DIR", RAW_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
