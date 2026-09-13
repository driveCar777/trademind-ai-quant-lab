"""Smoke: GOLD V4 follow STATUS. No train. Does not touch :9000 journal or V4/V5 READ."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from research_engine.hot_mt5_gold_follow import paths as gfpaths  # noqa: E402
from research_engine.hot_mt5_gold_follow.stance import write_status  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = gfpaths.FROZEN_JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    guards = [
        (gfpaths.V4_READ, "V4 READ"),
        (gfpaths.V5_READ, "V5 READ"),
        (gfpaths.V4_GOLD, "V4 GOLD"),
        (gfpaths.V5_GOLD, "V5 GOLD"),
    ]
    saved = [(p, p.read_bytes() if p.is_file() else b"") for p, _ in guards]

    tmp = gfpaths.OUT.parent / "SMOKE40"
    dest = tmp / "STATUS.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    st = write_status(dest)
    check(dest.is_file(), "writes STATUS")
    check(st.get("ok") is True, "status ok")
    check(st.get("candidate") is False and st.get("deploy") is False, "not Candidate, not deploy")
    check(st.get("feeds_grok") is False and st.get("order_send") is False, "no Grok / no order_send")
    check(st.get("writes_9000") is False, "writes_9000 false")
    check(st.get("broker_symbol") == "GOLD", "Ava symbol GOLD", str(st.get("broker_symbol")))
    check(st.get("stance") in ("LONG", "SHORT", "CASH"), "stance enum", str(st.get("stance")))
    check(st.get("last_close") is not None and st.get("last_bar"), "last bar + close")
    check(st.get("v5_weight") is not None, "V5 weight present")
    check("不是 Candidate" in (st.get("disclaimer") or ""), "disclaimer")
    check(st.get("lookback") == 252 and st.get("hold") == 20, "252/20 frozen")
    live = write_status()
    check(gfpaths.STATUS.is_file(), "writes live gold_follow/STATUS.json")
    check(live.get("stance") == st.get("stance"), "live STATUS same stance")

    check((frozen.read_bytes() if frozen.is_file() else b"") == before, "no :9000 JOURNAL")
    for (p, name), old in zip(guards, [s[1] for s in saved]):
        now = p.read_bytes() if p.is_file() else b""
        check(now == old, "does not rewrite %s" % name)

    print("SMOKE 40 gold follow:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
