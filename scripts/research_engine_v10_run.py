#!/usr/bin/env python3
"""V10 model discovery. Local sklearn. No purchase. No Final OOS."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.v10_model.compile import compile_reports
from research_engine.v10_model.run import run_v10


def main():
    summary = run_v10()
    reports = compile_reports()
    program = summary.get("program") or {}
    print("V10_DONE", program.get("stop"), "LEVEL", program.get("LEVEL"), "CANDIDATE", program.get("CANDIDATE"), "n", summary.get("n"))
    print("V10_REPORTS", reports.get("decision"))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
