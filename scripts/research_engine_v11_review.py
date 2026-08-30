#!/usr/bin/env python3
"""V11 capital allocation review. No purchase. No experiment."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.v11_alloc.compile import compile_v11


def main():
    out = compile_v11()
    print("V11_DONE", out.get("NEXT_PRIMARY_RESEARCH_PATH"))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
