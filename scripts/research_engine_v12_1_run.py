#!/usr/bin/env python3
"""V12.1 full A-share equity daily panel. No purchase. No alpha. No backtest."""
from __future__ import print_function

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.cn_a_share.acquire import acquire, load_checkpoint
from research_engine.cn_a_share.forensic import write_forensic
from research_engine.cn_a_share.paths import REFERENCE, ensure_tree
from research_engine.cn_a_share.universe_daily import build_universe_history, write_universe_v12_1


def cmd_universe():
    ensure_tree()
    payload = build_universe_history(
        os.path.join(REFERENCE, "tm-cn-a-CALENDAR-20260830-000001.csv"),
        os.path.join(REFERENCE, "tm-cn-a-BASIC-20260830-000001.csv"),
    )
    out = write_universe_v12_1(payload)
    print("UNIVERSE_DAYS", out["n_days"], "jumps", len(payload.get("jumps") or []), flush=True)
    return out


def cmd_forensic():
    path, body = write_forensic()
    print("FORENSIC", body.get("status"), path, flush=True)
    return body


def cmd_acquire(args):
    state = acquire(limit=args.limit, only_failed=args.retry_failed, sleep_s=args.sleep)
    print("DONE", len(state.get("done") or {}), "EMPTY", len(state.get("empty") or {}), "FAILED", len(state.get("failed") or {}), flush=True)
    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=("universe", "forensic", "acquire", "status", "bootstrap"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.05)
    args = parser.parse_args()
    if args.cmd == "universe":
        cmd_universe()
    elif args.cmd == "forensic":
        cmd_forensic()
    elif args.cmd == "acquire":
        cmd_acquire(args)
    elif args.cmd == "status":
        st = load_checkpoint()
        print("n_done", len(st.get("done") or {}), "empty", len(st.get("empty") or {}), "failed", len(st.get("failed") or {}), flush=True)
    elif args.cmd == "bootstrap":
        cmd_universe()
        cmd_forensic()
        cmd_acquire(args)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
