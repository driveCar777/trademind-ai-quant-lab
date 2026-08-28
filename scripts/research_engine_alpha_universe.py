"""Scan the tree into ALPHA_UNIVERSE_DB.json. No Final OOS. No Xavier."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.alpha_program.universe.scanner import dump_universe


def main():
    dests = [
        os.path.join(ROOT, "research_engine", "alpha_program", "universe", "ALPHA_UNIVERSE_DB.json"),
        os.path.join(ROOT, "data", "market", "research_engine", "alpha_program", "universe", "ALPHA_UNIVERSE_DB.json"),
    ]
    payload = None
    for path in dests:
        payload = dump_universe(path)
        print("UNIVERSE", path, "n=%s hash=%s" % (payload["n"], payload["content_hash"][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
