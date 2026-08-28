"""Run discovery pipeline: score backlog, write artifacts, refuse OOS, leave frozen hashes alone."""
from __future__ import print_function

import json
import os
from datetime import datetime

from research_engine.alpha_program import MIN_BACKLOG, PROGRAM_ID, PROGRAM_SEED
from research_engine.alpha_program.backlog_data import all_questions
from research_engine.alpha_program.guards import assert_no_final_oos, v09_hash_lock, xa_hash_untouched
from research_engine.alpha_program.score import cluster_best, rank_implementable
from research_protocol.hashing import canonical_hash


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(ROOT, "data", "market", "research_engine", "alpha_program")


def _dump(path, payload):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    body = json.dumps(payload, sort_keys=True, indent=2, separators=(",", ": "))
    with open(path, "w") as handle:
        handle.write(body)
        handle.write("\n")


def run(write=True):
    assert_no_final_oos()
    rows = all_questions()
    if len(rows) < MIN_BACKLOG:
        raise RuntimeError("BACKLOG_TOO_SMALL:%s" % len(rows))
    scored, live = rank_implementable(rows)
    clusters = cluster_best(live)
    top20 = live[:20]
    top3_clusters = clusters[:3]
    payload = {
        "program_id": PROGRAM_ID,
        "seed": PROGRAM_SEED,
        "n_questions": len(scored),
        "n_implementable": len(live),
        "v09_hash_lock": v09_hash_lock(),
        "xa_search_space_hash": xa_hash_untouched(),
        "FINAL_OOS_TOUCHED": False,
        "top20_ids": [r["id"] for r in top20],
        "top3_clusters": [
            {
                "cluster": r["cluster"],
                "best_id": r["id"],
                "score": r["score"],
                "keep_v09": r["cluster"] == "REGIME_TRANSITION",
            }
            for r in top3_clusters
        ],
        "scored": scored,
    }
    payload["content_hash"] = canonical_hash(
        {
            "n": payload["n_questions"],
            "top20": payload["top20_ids"],
            "top3": payload["top3_clusters"],
            "seed": PROGRAM_SEED,
        }
    )
    run_meta = {
        "utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "program_id": PROGRAM_ID,
        "content_hash": payload["content_hash"],
        "n_questions": payload["n_questions"],
        "n_implementable": payload["n_implementable"],
        "top3_clusters": payload["top3_clusters"],
        "FINAL_OOS_TOUCHED": False,
        "executed_v09": False,
        "note": "Scoring only. No Xavier. No V0.9 jobs.",
    }
    if write:
        _dump(os.path.join(OUT_DIR, "RESEARCH_BACKLOG_V1.json"), {"questions": scored})
        _dump(os.path.join(OUT_DIR, "RANKING_V1.json"), payload)
        _dump(os.path.join(OUT_DIR, "PIPELINE_RUN.json"), run_meta)
    return payload, run_meta
