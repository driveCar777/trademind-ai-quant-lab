"""Smoke: Paper Ops Desk V2 (SPEC §29.5–29.8) — plan state machine on the real calendar, journal-derived account,
run-manager status, no orders. Offline: uses a scratch journal file; never touches live/paper/JOURNAL.json or any frozen dir."""
from __future__ import print_function

import os
import shutil
import sys
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "master", "api"))

from app.service import paper_ops as po  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def at(s):
    po._now = lambda: datetime.strptime(s, "%Y-%m-%d %H:%M")


def main():
    po.JOURNAL = po.LIVE / "paper" / "JOURNAL_SMOKE.json"
    if po.JOURNAL.exists():
        os.remove(str(po.JOURNAL))
    S = po.SIGNALS
    days = po._days()
    sigs = po.chain_signals(days)
    check(len(sigs) > 0 and all(days.index(b) - days.index(a) == 21 for a, b in zip(sigs, sigs[1:])), "chain signals every 21 sessions", sigs[:3])
    cur = po.chain_signals(days, upto="2026-09-07")[-1]
    per = po.period_of(days, cur)
    check(per["entry"] == days[days.index(cur) + 1] and per["exit_date"] == days[days.index(cur) + 21], "period entry/exit", per)

    at("%s 10:00" % per["entry"])
    d = po.ops()
    check(d["plan"]["phase"] == "BUY_TODAY" and d["plan"]["cash_check"]["source"] == "MODEL", "entry day without journal -> BUY_TODAY on model list", d["plan"]["headline"])
    check(d["orders_sent"] is False and d["run"]["running"] in (True, False), "no orders, run status readable")

    mid = days[days.index(per["entry"]) + 5]
    at("%s 10:00" % mid)
    d = po.ops()
    check(d["plan"]["phase"] == "HOLD" and d["plan"]["sessions_held"] == 5 and d["plan"]["sessions_left"] == 15, "hold day held/left", (d["plan"]["sessions_held"], d["plan"]["sessions_left"]))
    check(all(h["status"] != "PREVIEW_NON_CHAIN" or not h["is_chain"] for h in d["history"]), "forced lists flagged non-chain")

    # journal: deposit + buy the model fills
    po.add_event({"type": "DEPOSIT", "amount": 20000, "date": cur})
    fills = (po._ledger().get("fills_by_period") or {}).get(cur) or []
    for f in fills:
        po.add_event({"type": "BUY", "symbol": f["symbol"], "lots": f["lots"], "price": f["open"], "date": per["entry"]})
    d = po.ops()
    a = d["account"]
    check(a["source"] == "JOURNAL" and len(a["positions"]) == len(fills) and a["cash"] < 20000, "journal-derived account", (a["cash"], a["equity"]))

    at("%s 09:00" % per["exit_date"])
    d = po.ops()
    check(d["plan"]["phase"] == "SELL_TODAY" and len(d["plan"]["sell_list"]) == len(fills), "exit morning -> SELL_TODAY with journal positions")
    at("%s 19:00" % per["exit_date"])
    d = po.ops()
    check(d["plan"]["phase"] == "SIGNAL_TONIGHT" and any("卖出" in w for w in d["plan"]["warnings"]), "signal night before update -> SIGNAL_TONIGHT + unsold warning")

    for p in po.ops()["account"]["positions"]:
        po.add_event({"type": "SELL", "symbol": p["symbol"], "lots": p["lots"], "price": p["mark_price"] or p["avg_price"], "date": per["exit_date"]})
    check(len(po.ops()["account"]["positions"]) == 0, "all sells logged -> flat")

    nxt = per["next_signal"]
    fake = [S / ("SHORTLIST_SHADOW_%s.json" % nxt), S / ("SHADOW_%s.json" % nxt)]
    made = []
    try:
        for src, dst in zip((S / ("SHORTLIST_SHADOW_%s.json" % cur), S / ("SHADOW_%s.json" % cur)), fake):
            if not dst.exists():
                shutil.copy(str(src), str(dst))
                made.append(dst)
        at("%s 19:30" % nxt)
        d = po.ops()
        cc = d["plan"]["cash_check"]
        check(d["plan"]["phase"] == "LIST_READY_BUY_TOMORROW" and cc["source"] == "JOURNAL" and cc["planned_yuan"] <= cc["budget"] + 1e-6, "list ready -> buy list sized to journal cash", (cc["cash_available"], cc["planned_yuan"]))
        at("%s 09:00" % per["next_entry"])
        d = po.ops()
        check(d["plan"]["phase"] == "BUY_TODAY" and len(d["plan"]["buy_list"]) > 0, "next entry day -> BUY_TODAY", len(d["plan"]["buy_list"]))
    finally:
        for f in made:
            os.remove(str(f))
    try:
        po.add_event({"type": "BUY", "symbol": "600000", "lots": 0, "price": 1})
        check(False, "invalid fill rejected")
    except ValueError:
        check(True, "invalid fill rejected")
    ev = po.load_journal()["events"]
    po.delete_event(ev[-1]["id"])
    check(len(po.load_journal()["events"]) == len(ev) - 1, "delete event")
    check(po._est_fee("BUY", 2000) == 5.0 and po._est_fee("SELL", 30000) == 24.0, "fee estimate")
    os.remove(str(po.JOURNAL))
    print("SMOKE 22 paper ops:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
