"""Score the alpha backlog. Does not run V0.9. Does not read Final OOS."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.alpha_program.pipeline import run


def main():
    payload, meta = run(write=True)
    print("PIPELINE_OK %s n=%s live=%s" % (
        meta["content_hash"][:16],
        payload["n_questions"],
        payload["n_implementable"],
    ))
    for row in payload["top3_clusters"]:
        print("CLUSTER %s %s %s" % (row["cluster"], row["best_id"], row["score"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
