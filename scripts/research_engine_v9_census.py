#!/usr/bin/env python3
"""V9 data census. Read-only. No purchase."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.v9_master.census import write_index


def main():
    path, payload = write_index()
    print("V9_CENSUS", path, payload.get("n_datasets"), payload.get("counts"))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
