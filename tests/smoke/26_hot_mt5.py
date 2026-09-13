"""Smoke: :9001 AVA MT5 product desk. Never sends, never writes :9000 journals."""
from __future__ import print_function

import os
import sys
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "master", "api"))
os.environ["TRADEMIND_HOT_SMOKE"] = "1"
os.environ["TRADEMIND_MT5_SEND"] = "0"

from app.service import paper_hot as hot  # noqa: E402
from app.service import paper_hot_mt5 as mx  # noqa: E402
from app.service import paper_ops as po  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = po.JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    orig = (mx.JOURNAL_PATH, mx.LAST_PATH, mx.RUN_PATH, mx.SESSIONS_PATH, mx.SETTINGS_PATH)
    orig_plan = mx.plan_path
    smoke = hot.HOT
    mx.JOURNAL_PATH = smoke / "MT5_JOURNAL_SMOKE.json"
    mx.LAST_PATH = smoke / "MT5_LAST_SMOKE.json"
    mx.RUN_PATH = smoke / "MT5_RUN_SMOKE.json"
    mx.SESSIONS_PATH = smoke / "MT5_SESSIONS_SMOKE.json"
    mx.SETTINGS_PATH = smoke / "MT5_SETTINGS_SMOKE.json"
    for p in (mx.JOURNAL_PATH, mx.LAST_PATH, mx.RUN_PATH, mx.SESSIONS_PATH, mx.SETTINGS_PATH):
        if p.exists():
            os.remove(str(p))
    mx.plan_path = lambda day, s: smoke / ("MT5_PLAN_SMOKE_%s_%s.json" % (day, s))

    check("paper_hot" in str(mx.JOURNAL_PATH).replace("\\", "/"), "mt5 journal under live/paper_hot")
    check(mx.JOURNAL_PATH != po.JOURNAL, "mt5 journal != :9000 JOURNAL")

    snap = mx.snapshot("asia")
    check(snap["probe"]["account_mode"] == "demo" and len(snap["products"]) == 8, "smoke snapshot: 8 product books")
    brief = mx._smoke_brief(snap)
    out = mx.enforce(brief, snap)
    by = {a["id"]: a for a in out["actions"]}
    why = {d["id"]: d["why"] for d in out["dropped"]}
    check("EURUSD" in by and by["EURUSD"]["action"] == "BUY" and by["EURUSD"]["send"] is True, "EURUSD BUY kept")
    check("SHARES" in by and by["SHARES"]["send"] is False, "SHARES action kept but send=false")
    check(why.get("NOTREAL") == "UNKNOWN_PRODUCT", "invented product dropped")
    check(why.get("USDJPY") == "PRICED_IN", "priced_in open dropped")

    sent = []

    def boom(*a, **k):
        sent.append(1)
        raise AssertionError("send must not run in smoke")

    plan = {"session": "asia", "actions": out["actions"], "snapshot": {"probe": {"account_mode": "demo"}}}
    exe = mx.execute(plan, send_fn=boom)
    check(sent == [] and not exe["sent_any"], "smoke execute never calls order_send")
    check(all(x.get("status") == "PAPER_ONLY" for x in exe["filled"]), "smoke fills are paper-only")
    evs = mx._journal()["events"]
    check(len(evs) >= 1 and all(e.get("reason") is not None and isinstance(e.get("snapshot"), dict) for e in evs),
          "mt5 fills record reason + snapshot")
    check(all("price" in e and "volume" in e and e.get("session") == "asia" for e in evs),
          "mt5 fills record price / volume / time session")

    live_plan = {"session": "asia", "actions": [a for a in out["actions"] if a["id"] == "EURUSD"],
                 "snapshot": {"probe": {"account_mode": "live"}}}
    live_exe = mx.execute(live_plan, send_fn=boom)
    check(sent == [] and live_exe["skipped"] and live_exe["skipped"][0]["why"] == "LIVE_ACCOUNT", "live account blocked")

    mx._now = lambda: datetime.strptime("2026-09-12 10:00", "%Y-%m-%d %H:%M")  # Saturday
    st = mx.run_session("asia", "jobS", "", snap_fn=lambda s: snap, grok_fn=lambda *a: (brief, {"status": "SMOKE_STUB"}),
                        send_fn=boom)
    check(st["pipeline"] == "SKIPPED_WEEKEND", "weekend skips Grok", st.get("pipeline"))

    mx._now = lambda: datetime.strptime("2026-09-14 08:40", "%Y-%m-%d %H:%M")  # Monday
    st2 = mx.run_session("asia", "jobA", "", snap_fn=lambda s: snap, grok_fn=lambda *a: (brief, {"status": "SMOKE_STUB"}),
                         send_fn=boom)
    check(st2["pipeline"] == "RAN" and st2.get("plan", {}).get("n_actions") >= 1, "weekday asia session RAN")
    st3 = mx.run_session("asia", "jobB", "", snap_fn=lambda s: snap, grok_fn=lambda *a: (brief, {"status": "SMOKE_STUB"}),
                         send_fn=boom)
    check(st3["pipeline"] == "SKIPPED_ALREADY_PLANNED", "same-day asia not repeated")
    st4 = mx.run_session("settle", "jobC")
    check(st4["pipeline"] == "SETTLE_ONLY", "settle never calls Grok")

    v = mx.view()
    check(v["profile"] == "HOT_MT5_DEMO" and v["candidate"] is False, "view profile")
    check(os.path.isfile(os.path.join(ROOT, "scripts", "hot_mt5_session.bat")), "session bat exists")

    after = frozen.read_bytes() if frozen.is_file() else b""
    check(after == before, ":9000 JOURNAL bytes unchanged")

    for p in (mx.JOURNAL_PATH, mx.LAST_PATH, mx.RUN_PATH, mx.SESSIONS_PATH, mx.SETTINGS_PATH,
              smoke / "MT5_PLAN_SMOKE_2026-09-14_asia.json"):
        if p.exists():
            os.remove(str(p))
    mx.JOURNAL_PATH, mx.LAST_PATH, mx.RUN_PATH, mx.SESSIONS_PATH, mx.SETTINGS_PATH = orig
    mx.plan_path = orig_plan
    print("SMOKE 26 hot mt5:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
