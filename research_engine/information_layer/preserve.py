"""Confirm Pack E bytes still match acquire hashes. No network."""
from __future__ import print_function

import hashlib
import json
import os

from research_engine.data_expansion.paths import repo_root


def _load(path):
    handle = open(path, encoding="utf-8")
    try:
        return json.load(handle)
    finally:
        handle.close()


def _sha256(path):
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


def preserve_pack_e():
    root = repo_root()
    state = _load(
        os.path.join(root, "data", "market", "research_engine", "external", "V61_ACQUIRE_STATE.json")
    )
    missing = []
    mismatch = []
    checked = 0
    for row in state.get("files") or []:
        path = row.get("path")
        expected = (row.get("sha256") or "").replace("sha256:", "")
        if not path or not os.path.isfile(path):
            missing.append(row.get("filename"))
            continue
        checked += 1
        if expected and _sha256(path) != expected:
            mismatch.append(row.get("filename"))
    jobs = state.get("jobs") or {}
    return {
        "complete": not missing and not mismatch and checked >= 60,
        "checked": checked,
        "missing": missing,
        "hash_mismatch": mismatch,
        "jobs": dict((k, {"id": v.get("id"), "state": v.get("state")}) for k, v in jobs.items()),
        "re_purchase_forbidden": True,
        "note": "Raw stays on D:. Git keeps hashes only.",
    }
