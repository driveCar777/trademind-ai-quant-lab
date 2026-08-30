#!/usr/bin/env python3
"""Compile V9 master CSV, attribution, and reports."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.v9_master.compile import compile_all


def main():
    metrics = compile_all()
    print(
        "V9_COMPILE",
        "CANDIDATE",
        metrics.get("LEVEL_1_CANDIDATE"),
        "STOP_B",
        metrics.get("STOP_B"),
        "pos_repro",
        metrics.get("positive_reproducible_n"),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
