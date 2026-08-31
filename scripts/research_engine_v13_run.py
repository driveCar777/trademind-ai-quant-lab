#!/usr/bin/env python3
"""V13 A-share CS alpha. Frozen panel only."""
from __future__ import print_function

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=("prepare", "run", "compile", "all"))
    args = parser.parse_args()
    if args.cmd == "prepare":
        from research_engine.cn_a_share_alpha.pack import pack_panel

        pack_panel()
    elif args.cmd == "run":
        from research_engine.cn_a_share_alpha.run import run_all

        run_all()
    elif args.cmd == "compile":
        from research_engine.cn_a_share_alpha.compile import compile_v13

        compile_v13()
    else:
        from research_engine.cn_a_share_alpha.run import run_all
        from research_engine.cn_a_share_alpha.compile import compile_v13

        out = run_all()
        compile_v13()
        print("V13", out.get("decision"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
