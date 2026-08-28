"""Classify mechanisms into ALPHA_BACKLOG_V2.json."""
from __future__ import print_function

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.alpha_program.scoring.catalog import all_mechanisms
from research_engine.alpha_program.scoring.classifier import rank_mechanisms
from research_protocol.hashing import canonical_hash


def main():
    scored, live = rank_mechanisms(all_mechanisms())
    payload = {
        "program_id": "ALPHA_BACKLOG_V2",
        "n": len(scored),
        "n_implementable": len(live),
        "top_ids": [r["id"] for r in live[:10]],
        "mechanisms": scored,
        "FINAL_OOS_TOUCHED": False,
    }
    payload["content_hash"] = canonical_hash({"n": payload["n"], "top": payload["top_ids"]})
    dests = [
        os.path.join(ROOT, "research_engine", "alpha_program", "scoring", "ALPHA_BACKLOG_V2.json"),
        os.path.join(ROOT, "data", "market", "research_engine", "alpha_program", "scoring", "ALPHA_BACKLOG_V2.json"),
    ]
    body = json.dumps(payload, indent=2, sort_keys=True)
    for path in dests:
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        handle = open(path, "w")
        try:
            handle.write(body)
            handle.write("\n")
        finally:
            handle.close()
        print("BACKLOG", path, "n=%s live=%s" % (payload["n"], payload["n_implementable"]))
    for row in live[:8]:
        print("LIVE", row["id"], row["family"], row["score"], row["status"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
