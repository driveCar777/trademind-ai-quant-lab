"""Append-only research ledger. Never rewrite a prior experiment row."""
from __future__ import print_function

import os
from datetime import datetime, timezone

from research_engine.io_util import dump_json, load_json


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LEDGER_PATH = os.path.join(ROOT, "docs", "research_engine", "RESEARCH_LEDGER_V1.json")


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_ledger():
    if os.path.isfile(LEDGER_PATH):
        return load_json(LEDGER_PATH)
    return {
        "ledger_id": "RESEARCH_LEDGER_V1",
        "FINAL_OOS_TOUCHED": False,
        "n": 0,
        "rows": [],
    }


def append_row(tag, experiment, contract, commit, dataset, result, decision, extra=None):
    payload = load_ledger()
    row = {
        "tag": tag,
        "experiment": experiment,
        "contract": contract,
        "commit": commit,
        "dataset": dataset,
        "result": result,
        "decision": decision,
        "utc": utc_now(),
    }
    if extra:
        row["extra"] = extra
    payload["rows"].append(row)
    payload["n"] = len(payload["rows"])
    dump_json(LEDGER_PATH, payload)
    return row
