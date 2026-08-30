#!/usr/bin/env python3
"""V9 local replay. No Xavier required. No purchase. No Final OOS."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.v9_master.run import run_replay


def main(argv=None):
    payload = run_replay(include_v06_sensitivity=True, family_iters=1, resume=True)
    print("V9_REPLAY", payload.get("n_rows"), "STOP_A", payload.get("STOP_A"), "%.1f" % payload.get("elapsed_seconds"))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
