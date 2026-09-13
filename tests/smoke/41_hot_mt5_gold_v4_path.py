"""Smoke: GOLD V4 path/exit diagnostic. No train. Does not touch READ or :9000 journal."""
from __future__ import print_function

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_tsmom import path_exits  # noqa: E402
from research_engine.hot_mt5_tsmom.paths import FROZEN_JOURNAL, RES, V1_READ  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    read_p = RES / "READ.json"
    gold_p = RES / "GOLD.json"
    trades_p = RES / "GOLD_trades.json"
    before_read = read_p.read_bytes() if read_p.is_file() else b""
    before_gold = gold_p.read_bytes() if gold_p.is_file() else b""
    before_tr = trades_p.read_bytes() if trades_p.is_file() else b""
    before_v1 = V1_READ.read_bytes() if V1_READ.is_file() else b""
    before_j = FROZEN_JOURNAL.read_bytes() if FROZEN_JOURNAL.is_file() else b""

    out = path_exits.run()
    check(out.get("n") == 102, "n=102", str(out.get("n")))
    check(out.get("candidate") is False, "not Candidate")
    check(out.get("not_a_book") is True and out.get("do_not_write_into_follow") is True, "diagnostic only")
    base = (out.get("base") or {}).get("all") or {}
    res = (out.get("base") or {}).get("research") or {}
    gold = json.loads(gold_p.read_text(encoding="utf-8"))
    check(abs((res.get("net_twr") or 0) - gold["research_70"]["twr"]) < 1e-12, "research TWR matches GOLD.json")
    check(abs((base.get("net_twr") or 0) - gold["long_sample"]["twr"]) < 1e-12, "full TWR matches GOLD.json")
    check((out.get("n_losers") or 0) == 47, "47 losers", str(out.get("n_losers")))
    check((RES / "GOLD_PATH_EXITS.json").is_file() and (RES / "GOLD_PATH_TRADES.json").is_file(), "writes path JSON")
    check((read_p.read_bytes() if read_p.is_file() else b"") == before_read, "does not rewrite V4 READ")
    check((gold_p.read_bytes() if gold_p.is_file() else b"") == before_gold, "does not rewrite GOLD.json")
    check((trades_p.read_bytes() if trades_p.is_file() else b"") == before_tr, "does not rewrite GOLD_trades")
    check((V1_READ.read_bytes() if V1_READ.is_file() else b"") == before_v1, "does not rewrite V1 READ")
    check((FROZEN_JOURNAL.read_bytes() if FROZEN_JOURNAL.is_file() else b"") == before_j, "no :9000 JOURNAL")

    print("SMOKE 41 gold V4 path:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
