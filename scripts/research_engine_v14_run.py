#!/usr/bin/env python3
from __future__ import print_function

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=("reload", "run", "compile", "all"))
    args = parser.parse_args()
    if args.cmd == "reload":
        from research_engine.cn_a_share.io_util import dump_json
        from research_engine.cn_a_share_strategy_v14.paths import OUT, ensure_out
        from research_engine.cn_a_share_strategy_v14.reload import reload_contract
        from research_engine.cn_a_share_strategy_v14.spec import build_spec

        ensure_out()
        rec = reload_contract()
        spec = build_spec()
        dump_json(os.path.join(OUT, "CONTRACT_RELOAD.json"), rec)
        dump_json(os.path.join(OUT, "STRATEGY_SPEC.json"), spec)
        print("RELOAD", rec["checks"]["all_ok"], rec["checks"]["live_hash"], spec["spec_hash"], flush=True)
    elif args.cmd == "run":
        from research_engine.cn_a_share_strategy_v14.run import run_v14

        run_v14()
    elif args.cmd == "compile":
        from research_engine.cn_a_share_strategy_v14.compile import compile_v14

        compile_v14()
    else:
        from research_engine.cn_a_share_strategy_v14.compile import compile_v14
        from research_engine.cn_a_share_strategy_v14.run import run_v14

        run_v14()
        compile_v14()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
