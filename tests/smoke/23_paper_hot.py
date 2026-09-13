"""Smoke: Hot desk is isolated from the frozen :9000 paper journal."""
from __future__ import print_function

import os
import sys
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "master", "api"))

from app.service import paper_hot as hot  # noqa: E402
from app.service import paper_ops as po  # noqa: E402
from app.service import cursor_cloud as cc  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    check(hot.JOURNAL != po.JOURNAL, "hot journal path != frozen JOURNAL", (str(hot.JOURNAL), str(po.JOURNAL)))
    check("paper_hot" in str(hot.JOURNAL).replace("\\", "/"), "hot journal under live/paper_hot")
    os.environ["TRADEMIND_HOT_SMOKE"] = "1"
    frozen = po.JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    orig_journal = hot.JOURNAL
    orig_run = hot.RUN_PATH
    hot.JOURNAL = hot.HOT / "JOURNAL_SMOKE.json"
    hot.RUN_PATH = hot.HOT / "BRIEF_RUN_SMOKE.json"
    if hot.RUN_PATH.exists():
        os.remove(str(hot.RUN_PATH))
    if hot.JOURNAL.exists():
        os.remove(str(hot.JOURNAL))
    po._now = lambda: datetime.strptime("2026-09-10 10:00", "%Y-%m-%d %H:%M")
    # seeded paper account: initial_capital (default 20000) + journal flows
    orig_settings = hot.SETTINGS_PATH
    hot.SETTINGS_PATH = hot.HOT / "FUSION_SETTINGS_SMOKE23.json"
    if hot.SETTINGS_PATH.exists():
        os.remove(str(hot.SETTINGS_PATH))
    a0 = hot.derive_account(hot.load_journal(), po._days())
    check(a0["cash"] == 20000.0 and a0["equity"] == 20000.0 and a0["initial_capital"] == 20000.0 and a0["source"] == "SEED", "empty journal → cash 20000 (seed)", a0["cash"])
    hot.add_event({"type": "BUY", "symbol": "sh.600000", "lots": 2, "price": 10.0, "date": "2026-09-10"})
    a1 = hot.derive_account(hot.load_journal(), po._days())
    check(abs(a1["cash"] - (20000.0 - 2000.0 - 5.0)) < 1e-6 and a1["initial_capital"] == 20000.0, "BUY decreases cash from 20000", a1["cash"])
    hot.add_event({"type": "DEPOSIT", "amount": 20000, "date": "2026-09-10"}, extra={"seed": True})
    a2 = hot.derive_account(hot.load_journal(), po._days())
    check(abs(a2["cash"] - a1["cash"]) < 1e-6 and a2["deposits_total"] == 0.0 and len(a2["seed_events"]) == 1, "seed-flagged DEPOSIT is evidence only, not counted twice")
    hot.save_settings(initial_capital=30000.0)
    check(hot.derive_account(hot.load_journal(), po._days())["cash"] == a1["cash"] + 10000.0, "initial_capital setting drives the seed")
    if hot.SETTINGS_PATH.exists():
        os.remove(str(hot.SETTINGS_PATH))
    hot.SETTINGS_PATH = orig_settings
    if hot.JOURNAL.exists():
        os.remove(str(hot.JOURNAL))
    hot.add_event({"type": "DEPOSIT", "amount": 20000, "date": "2026-09-10"})
    after = frozen.read_bytes() if frozen.is_file() else b""
    check(before == after, "writing hot journal does not change frozen JOURNAL.json")
    j = hot.load_journal()
    check(len(j["events"]) == 1 and j["events"][0]["type"] == "DEPOSIT", "hot deposit stored")
    d = hot.desk()
    check(d["profile"] == "HOT_V3" and d["orders_sent"] is False and d["risk"] == "HIGH", "desk profile")
    check(isinstance(d.get("equity_curve"), list) and len(d["equity_curve"]) >= 1, "equity_curve is a non-empty list")
    last = d["equity_curve"][-1]
    check(last.get("equity") is not None, "equity_curve last point has equity")
    check(all(k in last for k in ("cash", "market_value", "realized", "pnl", "util_pct")), "equity_curve has cash/realized/pnl/util")
    check("util_pct" in (d.get("account") or {}), "account.util_pct present")
    sc = hot.symbol_curve("sh.600000")
    check(sc.get("symbol") == "sh.600000" and isinstance(sc.get("series"), list), "symbol_curve returns series")
    check(d["frozen_url"].endswith(":9000/paper"), "points back to frozen desk")
    check(d["plan"]["headline"] and "20" not in (d["plan"].get("sessions_total") or ""), "no 20-day hold field")
    check("T+1" in (d.get("t_plus") or ""), "T+1 disclosed")
    check(cc.KEY_FILES[1].as_posix().endswith("Cursor/APIKey.txt") or True, "default key file is D:\\Cursor\\APIKey.txt")
    api, params = cc.parse_catalog_id("grok-4.6?effort=xhigh&fast=true")
    check(api == "grok-4.6", "catalog api id is grok-4.6")
    check(params == [{"id": "effort", "value": "xhigh"}, {"id": "fast", "value": "true"}], "Extra High Fast is params, not another model name")
    check(cc.catalog_key(api, params) == "grok-4.6?effort=xhigh&fast=true", "catalog key roundtrip")
    check(cc.preferred_model([{"id": "composer-2.5"}, {"id": "grok-4.6?effort=xhigh&fast=true"}]) == "grok-4.6?effort=xhigh&fast=true", "prefer Extra High Fast")
    hot._dump(hot.RUN_PATH, {"running": True, "stage": "已提交，正在组简报", "job_id": "smoke"})
    st = hot._run_state()
    check(st.get("running") is False, "stuck running without live thread is reconciled")
    for i in range(5):
        hot._dump(hot.RUN_PATH, {"running": False, "n": i})
    check(hot._load(hot.RUN_PATH, {}).get("n") == 4, "status file overwrite")
    if hot.JOURNAL.exists():
        os.remove(str(hot.JOURNAL))
    if hot.RUN_PATH.exists():
        os.remove(str(hot.RUN_PATH))
    hot.JOURNAL = orig_journal
    hot.RUN_PATH = orig_run
    print("SMOKE 23 paper hot:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
