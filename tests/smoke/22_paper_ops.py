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
    at("2026-09-06 10:00")
    f = po.freshness(days, {"asof_session": "2026-09-04"})
    check(f["last_completed_session"] == "2026-09-04" and not f["today_is_trading_day"] and not f["needs_update"],
          "Sat 9/6 -> last open 9/4, never a future date")
    at("2026-09-07 10:00")
    f = po.freshness(days, {"asof_session": "2026-09-04"})
    check(f["last_completed_session"] == "2026-09-04" and f["today_is_trading_day"] and not f["needs_update"],
          "Mon morning before 18:00 still 9/4")
    at("2026-09-07 19:00")
    f_stale = po.freshness(["2007-05-21"], {"asof_session": "2026-09-04"})
    check(f_stale.get("calendar_stale") and f_stale["needs_update"] and f_stale["last_completed_session"] == "2026-09-07",
          "truncated calendar is not a holiday; after 18:00 asof is today")
    f = po.freshness(days, {"asof_session": "2026-09-04"})
    check(f["last_completed_session"] == "2026-09-07" and f["needs_update"] and f["stale_sessions"] == 1,
          "Mon after 18:00 target is today 9/7")
    f = po.freshness(days, {"asof_session": "2026-09-07"})
    check(not f["needs_update"], "already at 9/7 -> no calendar gap")
    f_bogus = po.freshness(days, {"asof_session": "2007-05-23"})
    check(f_bogus.get("asof_bogus") and f_bogus["needs_update"] and f_bogus["last_completed_session"] == "2026-09-07",
          "poisoned 2007 STATUS is not treated as current")
    idle = po.stop_update()
    check(idle.get("running") is False, "stop when idle does not error", idle.get("note") or idle.get("stage"))
    cur = po.chain_signals(days, upto="2026-09-07")[-1]
    per = po.period_of(days, cur)
    check(per["entry"] == days[days.index(cur) + 1] and per["exit_date"] == days[days.index(cur) + 21], "period entry/exit", per)

    at("%s 10:00" % per["entry"])
    d = po.ops()
    pm, pa = d["plans"]["model"], d["plans"]["actual"]
    check(pm["phase"] == "BUY_TODAY" and pm["cash_check"]["source"] == "MODEL", "entry day, model view -> BUY_TODAY on model list", pm["headline"])
    check(pa["phase"] == "BUY_TODAY" and pa["cash_check"]["source"] == "JOURNAL" and any("现金为 0" in w for w in pa["warnings"]), "entry day, empty actual account -> BUY_TODAY + cash-0 warning")
    check(d["orders_sent"] is False and d["run"]["running"] in (True, False), "no orders, run status readable")

    mid = days[days.index(per["entry"]) + 5]
    at("%s 10:00" % mid)
    d = po.ops()
    pm, pa = d["plans"]["model"], d["plans"]["actual"]
    check(pm["phase"] == "HOLD" and pm["sessions_held"] == 5 and pm["sessions_left"] == 15, "hold day, model held/left", (pm["sessions_held"], pm["sessions_left"]))
    check(pa["phase"] == "NO_POSITION" and pa["today_action"] == "WAIT" and pa.get("mid_entry_option") and len(pa["buy_list"]) > 0 and per["next_entry"] in pa["sub"],
          "hold day, empty actual (cash 0) -> NO_POSITION, mid-entry option + period list still shown", pa["headline"])
    check(d["history_actual"] and d["history_actual"][-1]["status"] == "NOT_TRADED", "actual history shows NOT_TRADED")
    check(all(h["status"] != "PREVIEW_NON_CHAIN" or not h["is_chain"] for h in d["history_model"]), "forced lists flagged non-chain")

    # journal: deposit + PARTIAL buy (3 of the model fills)
    po.add_event({"type": "DEPOSIT", "amount": 20000, "date": cur})
    fills = (po._ledger().get("fills_by_period") or {}).get(cur) or []
    part = fills[:3]
    for f in part:
        lots = f.get("lots") or f.get("lots_100_est")
        price = f.get("open") or f.get("last_close")
        po.add_event({"type": "BUY", "symbol": f["symbol"], "lots": lots, "price": price, "date": per["entry"]})
    d = po.ops()
    a, pa, pm = d["account"], d["plans"]["actual"], d["plans"]["model"]
    check(a["source"] == "JOURNAL" and len(a["positions"]) == 3 and a["cash"] < 20000, "journal-derived account (3 names)", (a["cash"], a["equity"]))
    check(pa["phase"] == "HOLD" and any("3/%d" % len(fills) in w for w in pa["warnings"]), "partial fill -> HOLD with partial note", pa["warnings"])
    check(len(d["model_positions"]) == len(fills) and pm["phase"] == "HOLD" and not any("只买了" in w for w in (pm.get("warnings") or [])),
          "model view unaffected by partial fill")
    if d["model_positions"]:
        p0 = d["model_positions"][0]
        live_px, live_d = po._last_close(p0["symbol"])
        check((p0.get("mark_missing") and live_px is None) or (p0.get("mark_price") == live_px and p0.get("mark_date") == live_d),
              "model mark_price is live bar close", (p0.get("mark_price"), live_px, p0.get("mark_date"), live_d))
        sm = d.get("model_summary") or {}
        check(not live_d or sm.get("open_mark_date") == max(p.get("mark_date") or "" for p in d["model_positions"]),
              "model_summary open_mark_date follows live bars", sm.get("open_mark_date"))
    check(len(pa.get("buy_list") or []) == len(fills) - 3 and len(pa.get("logged_list") or []) == 3 and pa.get("continue_register"),
          "partial fill keeps remaining names on the list", (len(pa.get("buy_list") or []), len(pa.get("logged_list") or [])))
    ev0 = next(e for e in po.load_journal()["events"] if e.get("type") == "BUY")
    old_amt, old_px = ev0["amount"], ev0["price"]
    po.update_event(ev0["id"], {"price": round(old_px + 0.02, 2)})
    ev1 = next(e for e in po.load_journal()["events"] if e["id"] == ev0["id"])
    check(ev1["price"] == round(old_px + 0.02, 2) and ev1["amount"] != old_amt and ev1["id"] == ev0["id"], "edit fill in place", (ev1["price"], ev1["amount"]))
    po.update_event(ev0["id"], {"price": old_px, "fee": ev0["fee"]})
    ha = d["history_actual"][-1]
    check(ha["status"] == "OPEN" and ha["n_names"] == 3 and ha["invested"] > 0, "actual history period OPEN with 3 names", (ha["n_names"], ha["invested"]))
    # the rest of the fills
    for f in fills[3:]:
        lots = f.get("lots") or f.get("lots_100_est")
        price = f.get("open") or f.get("last_close")
        po.add_event({"type": "BUY", "symbol": f["symbol"], "lots": lots, "price": price, "date": per["entry"]})

    at("%s 09:00" % per["exit_date"])
    d = po.ops()
    check(d["plan"]["phase"] == "SELL_TODAY" and len(d["plan"]["sell_list"]) == len(fills), "exit morning -> SELL_TODAY with journal positions")
    at("%s 19:00" % per["exit_date"])
    d = po.ops()
    check(d["plan"]["phase"] == "SIGNAL_TONIGHT" and any("卖出" in w for w in d["plan"]["warnings"]), "signal night before update -> SIGNAL_TONIGHT + unsold warning")

    for p in po.ops()["account"]["positions"]:
        po.add_event({"type": "SELL", "symbol": p["symbol"], "lots": p["lots"], "price": p["mark_price"] or p["avg_price"], "date": per["exit_date"]})
    d = po.ops()
    check(len(d["account"]["positions"]) == 0, "all sells logged -> flat")
    ha = next(h for h in d["history_actual"] if h["signal_date"] == cur)
    check(ha["status"] == "CLOSED" and ha["proceeds"] > 0 and ha["pnl"] is not None, "actual history period CLOSED with proceeds", (ha["proceeds"], ha["pnl"]))
    check(d["history_actual"][-1]["status"] == "PENDING_ENTRY", "new period on signal night -> PENDING_ENTRY")

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
