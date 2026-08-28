"""Append a family failure. Do not rewrite frozen experiment files."""
from __future__ import print_function

import json
import os
from datetime import datetime


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def write_failure(family, outcome, why, path=None):
    dest = path or os.path.join(
        ROOT, "data", "market", "research_engine", "alpha_program", "FAILED_ALPHA_DATABASE.json"
    )
    parent = os.path.dirname(dest)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    rows = []
    if os.path.isfile(dest):
        handle = open(dest, "r")
        try:
            payload = json.load(handle)
            rows = list(payload.get("records") or [])
        finally:
            handle.close()
    rows.append(
        {
            "family": family,
            "outcome": outcome,
            "why": why,
            "utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "do_not_repeat": True,
        }
    )
    out = {"n": len(rows), "records": rows, "FINAL_OOS_TOUCHED": False}
    handle = open(dest, "w")
    try:
        json.dump(out, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    return out
