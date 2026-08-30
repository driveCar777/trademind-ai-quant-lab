#!/usr/bin/env python3
"""V12.2 panel completion supervisor. No purchase. No alpha. One downloader."""
from __future__ import print_function

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=("status", "compile", "supervise"))
    parser.add_argument("--poll", type=int, default=60)
    args = parser.parse_args()
    if args.cmd == "status":
        from research_engine.cn_a_share.guard import count_raw_files, disk_ok_for_download, find_acquire_pids

        ok, flag, d_free, c_free = disk_ok_for_download()
        print("n_raw", count_raw_files(), "pids", find_acquire_pids(), "D", d_free, "C", c_free, flag, flush=True)
    elif args.cmd == "compile":
        from research_engine.cn_a_share.compile_v12_2 import compile_v12_2

        out = compile_v12_2()
        print("PRICE_ALPHA_STATUS", out.get("PRICE_ALPHA_STATUS"), "n", out.get("n_files"), flush=True)
    elif args.cmd == "supervise":
        from research_engine.cn_a_share.supervise import supervise

        out = supervise(poll_s=args.poll)
        print("SUPERVISE_DONE", out.get("PRICE_ALPHA_STATUS"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
