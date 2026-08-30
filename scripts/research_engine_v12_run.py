#!/usr/bin/env python3
"""V12 A-share PIT foundation. No purchase. No alpha. No backtest."""
from __future__ import print_function

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.cn_a_share.compile import compile_v12
from research_engine.cn_a_share.factory import load_or_wait_delist, run_factory
from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share.paths import RESEARCH


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-universe", action="store_true")
    parser.add_argument("--compile-only", action="store_true")
    args = parser.parse_args()
    if args.compile_only:
        from research_engine.cn_a_share.io_util import load_json

        art = load_json(os.path.join(RESEARCH, "FACTORY_RUN_V12.json"))
        art["delist_census"] = load_or_wait_delist()
        dump_json(os.path.join(RESEARCH, "FACTORY_RUN_V12.json"), art)
        out = compile_v12(art)
    else:
        art = run_factory(include_universe=not args.skip_universe)
        art["delist_census"] = load_or_wait_delist()
        dump_json(os.path.join(RESEARCH, "FACTORY_RUN_V12.json"), art)
        out = compile_v12(art)
    print("A_SHARE_DATA_STATUS", out.get("A_SHARE_DATA_STATUS"), flush=True)
    print("NEXT_PRIMARY_ACTION", out.get("NEXT_PRIMARY_ACTION"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
