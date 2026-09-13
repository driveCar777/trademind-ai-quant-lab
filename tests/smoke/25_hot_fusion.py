"""Smoke: Hot Desk V3 fusion pipeline (:9001). All Grok calls are canned under TRADEMIND_HOT_SMOKE=1."""
from __future__ import print_function

import json
import os
import sys
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "master", "api"))
os.environ["TRADEMIND_HOT_SMOKE"] = "1"

from app.service import paper_fusion as fu  # noqa: E402
from app.service import paper_hot as hot  # noqa: E402
from app.service import paper_ops as po  # noqa: E402
from research_engine.hot_three_books import anon  # noqa: E402
from research_engine.hot_three_books import book2 as b2  # noqa: E402
from research_engine.hot_three_books import grok_keep  # noqa: E402
from research_engine.hot_three_books import paths  # noqa: E402

FAILED = [0]


def check(ok, label, extra=""):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, extra))
    if not ok:
        FAILED[0] += 1


def main():
    frozen = po.JOURNAL
    before = frozen.read_bytes() if frozen.is_file() else b""
    smoke_dir = hot.HOT
    orig = (hot.JOURNAL, fu.LAST_PATH, fu.RUN_PATH, fu.ANON_LOG, fu.plan_path, fu.POOL_PATH)
    hot.JOURNAL = smoke_dir / "JOURNAL_SMOKE25.json"
    fu.LAST_PATH = smoke_dir / "FUSION_LAST_SMOKE.json"
    fu.RUN_PATH = smoke_dir / "FUSION_RUN_SMOKE.json"
    fu.ANON_LOG = smoke_dir / "FUSION_ANON_LOG_SMOKE.json"
    fu.POOL_PATH = smoke_dir / "POOL_SMOKE.json"
    fu.plan_path = lambda asof: smoke_dir / ("FUSION_PLAN_SMOKE_%s.json" % asof)
    for p in (hot.JOURNAL, fu.LAST_PATH, fu.RUN_PATH, fu.ANON_LOG, fu.POOL_PATH):
        if p.exists():
            os.remove(str(p))
    po._now = lambda: datetime.strptime("2026-09-11 20:00", "%Y-%m-%d %H:%M")

    # 1. file isolation
    check(fu.LAST_PATH != po.JOURNAL and "paper_hot" in str(fu.HOT).replace("\\", "/"), "fusion files under live/paper_hot")
    check(str(paths.FROZEN_JOURNAL).replace("\\", "/").endswith("live/paper/JOURNAL.json"), "frozen journal path recorded")

    # 2. pool from ML1 only
    pool = fu.build_pool()
    check(pool["n_pool"] > 0, "pool non-empty", "n=%s shortlist=%s ext=%s" % (pool["n_pool"], pool["n_shortlist"], pool["n_extended"]))
    check(pool["n_extended"] <= fu.EXT_POOL_N, "extended pool ≤ 30")
    check(all(fu._is_main_board(n["symbol"]) for n in pool["names"] if n["source"] == "SIGNAL_TOP30"), "extended pool main board only")
    check(all(float(n["last_close"] or 0) <= fu.MAX_PRICE for n in pool["names"] if n["source"] == "SIGNAL_TOP30"), "extended pool ≤ ¥100")
    check(set(n["source"] for n in pool["names"]) <= {"SHORTLIST", "SIGNAL_TOP30"}, "pool sources are ML1 files only")
    fu._dump(fu.LAST_PATH, {"pool": {"signal_date": "2020-01-01"}, "pool_names": [{"symbol": pool["names"][0]["symbol"]}]})
    stamped = fu.stamp_pool({"signal_date": "2026-08-28", "names": [
        {"symbol": pool["names"][0]["symbol"], "source": "SHORTLIST"},
        {"symbol": "sz.000001", "source": "SIGNAL_TOP30"},
    ]})
    check(stamped["pool_rotated"] is True and stamped["n_old"] == 1 and stamped["n_new"] == 1, "stamp_pool marks NEW vs last plan")
    check(stamped["names"][0]["pool_age"] == "OLD" and stamped["names"][1]["pool_age"] == "NEW", "pool_age OLD/NEW")
    if fu.LAST_PATH.exists():
        os.remove(str(fu.LAST_PATH))
    check(fu.hot_pool_owned({"asof_session": "2026-09-11"}) is False, "asof Fri → hot pool not owned yet")
    check(fu.hot_pool_owned({"asof_session": "2026-09-14"}) is True, "asof Mon → hot pool owned")
    r_wait = fu.refresh_hot_pool({"asof_session": "2026-09-11", "today": "2026-09-11"})
    check(r_wait["status"] == "WAIT_MONDAY" and r_wait["refreshed"] is False and r_wait["writes_9000"] is False,
          "refresh before Monday is a no-op")
    sig_path = None
    well = fu.ml1_well()
    if well.get("file"):
        sig_path = po.SIGNALS / well["file"]
    sig_before = sig_path.read_bytes() if sig_path and sig_path.is_file() else b""
    sl_files = sorted(po.SIGNALS.glob("SHORTLIST_20*.json")) + sorted(po.SIGNALS.glob("SHORTLIST_SHADOW_*.json"))
    sl_before = [(p, p.read_bytes()) for p in sl_files if p.is_file()]
    r1 = fu.refresh_hot_pool({"asof_session": "2026-09-14", "today": "2026-09-14"}, reason="HOLD_CASH")
    check(r1["refreshed"] is True and r1["writes_9000"] is False and r1.get("generation") == 1, "Monday refresh writes :9001 POOL only")
    r2 = fu.refresh_hot_pool({"asof_session": "2026-09-14", "today": "2026-09-14"}, reason="HOLD_CASH")
    check(r2["refreshed"] is True and r2.get("generation") == 2, "second refresh same day allowed")
    r3 = fu.refresh_hot_pool({"asof_session": "2026-09-14", "today": "2026-09-14"}, reason="HOLD_CASH")
    check(r3["status"] == "SKIPPED_REFRESH_BUDGET" and r3["refreshed"] is False, "third refresh same day blocked")
    check(not sig_path or sig_path.read_bytes() == sig_before, ":9000 SIGNAL bytes unchanged after refresh")
    check(all(p.read_bytes() == b for p, b in sl_before), ":9000 SHORTLIST bytes unchanged after refresh")
    st_pool = fu._load(fu.POOL_PATH, {}) or {}
    check(st_pool.get("owner") == "hot_9001" and st_pool.get("writes_9000") is False, "POOL.json is :9001-owned")
    if fu.POOL_PATH.exists():
        os.remove(str(fu.POOL_PATH))

    # 3. anon payload on live bars
    syms = [n["symbol"] for n in pool["names"]][:6]
    payload, mapping, used = fu.anon_payload(syms, None)
    blob = json.dumps(payload, ensure_ascii=False)
    check(len(payload["series"]) == len(used) and len(used) > 0, "anon series built from live bars", "n=%d" % len(used))
    check(not anon.leak_hits(blob), "live anon payload has no leak tokens")
    check("sh." not in blob and "sz." not in blob and not any(s.split(".")[1] in blob for s in used), "no codes in live payload")
    check(all(len(s["bars"]) <= fu.LOOKBACK for s in payload["series"]), "≤ 60 bars")
    check(payload.get("protocol") == "v1.1" and all(isinstance(b, list) and len(b) == 4 for s in payload["series"] for b in s["bars"]), "anon protocol v1.1: bars are [o,h,l,c] arrays")
    check(all(abs(next((b[3] for b in s["bars"] if b[3] > 0), 100.0) - 100.0) < 1e-6 for s in payload["series"]), "first close normalised to 100")
    check(len(blob) < 3000 * len(used), "compact payload (< 3 KB per series)", "%d bytes / %d series" % (len(blob), len(used)))

    # 4. hard rules: T+1, exposure cap, max names, pool-only buys, sell-only-held
    kept = [{"symbol": "sh.600%03d" % i, "name": "K%d" % i, "last_close": 10.0, "source": "SHORTLIST", "rank": i, "score": 0.1} for i in range(12)]
    account = {"equity": 20000.0, "cash": 15000.0, "positions": [
        {"symbol": "sh.600000", "name": "K0", "lots": 2, "market_value": 2000.0, "mark_price": 10.0, "buy_date": "2026-09-11", "sellable_at_fill": False},
        {"symbol": "sz.000999", "name": "OLD", "lots": 3, "market_value": 3000.0, "mark_price": 10.0, "buy_date": "2026-09-01", "sellable_at_fill": True},
    ]}
    brief = {"exposure_pct": 50, "names": [
        {"symbol": "600000", "action": "SELL", "lots_hint": 2},                # T+1 blocked → HOLD
        {"symbol": "sz.000999", "action": "SELL", "lots_hint": 3},             # allowed
        {"symbol": "sz.300001", "action": "BUY", "lots_hint": 5},              # not main board / not in pool
        {"symbol": "sh.601398", "action": "BUY", "lots_hint": 1},              # out of pool
        {"symbol": "sh.600123", "action": "SELL"},                             # sell not held
    ] + [{"symbol": "sh.600%03d" % i, "action": "BUY", "lots_hint": 3} for i in range(1, 12)]}
    out = fu.enforce(brief, kept, account, "2026-09-14", "OK")
    by = {r["symbol"]: r for r in out["actions"]}
    check(by["sh.600000"]["action"] == "HOLD" and "T+1" in by["sh.600000"].get("blocked", ""), "T+1: same-day buy cannot be sold at fill")
    check(by["sz.000999"]["action"] == "SELL", "held & sellable → SELL kept")
    whys = set(d["why"] for d in out["dropped"])
    n_univ = sum(1 for d in out["dropped"] if d["why"] == "OUT_OF_UNIVERSE")
    check(n_univ == 3 and "MAX_8_NAMES" in whys, "universe clamp drops not-pool/not-held (board, out-of-pool, sell-not-held)", str(sorted(whys)))
    n_pos = sum(1 for r in out["actions"] if r["action"] in ("BUY", "HOLD"))
    check(n_pos <= fu.MAX_NAMES, "≤ 8 BUY/HOLD names", "n=%d" % n_pos)
    cap = 0.5 * 20000.0
    total = out["budget"]["post_plan_notional"]
    check(total <= cap + 1e-6, "notional ≤ exposure × equity", "%.2f ≤ %.2f" % (total, cap))
    check(out["budget"]["planned_buy_notional"] <= 15000.0 - fu.CASH_RESERVE + 1e-6, "buys ≤ cash − reserve")
    out0 = fu.enforce({"exposure_pct": 90, "names": [{"symbol": "sh.600001", "action": "BUY", "lots_hint": 1}]}, kept, account, "2026-09-14", "GROK_TIMEOUT")
    check(out0["exposure_pct"] == 0 and not [r for r in out0["actions"] if r["action"] == "BUY"], "Layer B failure → exposure 0, no BUY")
    # consult-adopted: priced_in=true → BUY dropped, SELL → HOLD; audit block present
    outp = fu.enforce({"exposure_pct": 50, "names": [
        {"symbol": "sh.600001", "action": "BUY", "lots_hint": 1, "claim_class": "narrative", "priced_in": True},
        {"symbol": "sz.000999", "action": "SELL", "claim_class": "narrative", "priced_in": "true"},
        {"symbol": "sh.600002", "action": "BUY", "lots_hint": 1, "claim_class": "hard_event", "priced_in": False},
    ]}, kept, account, "2026-09-14", "OK")
    byp = {r["symbol"]: r for r in outp["actions"]}
    check("PRICED_IN_NEXT_OPEN" in set(d["why"] for d in outp["dropped"]) and byp["sz.000999"]["action"] == "HOLD" and byp["sh.600002"]["action"] == "BUY",
          "priced_in → BUY dropped / SELL→HOLD; hard_event BUY kept")
    check(outp["audit"]["n_narrative_actions"] == 0 and outp["audit"]["hold_all"] is False and len(fu.prompt_hash()) == 12, "audit block + prompt hash")

    # 5. pipeline end-to-end with canned Grok
    hot.add_event({"type": "DEPOSIT", "amount": 20000, "date": "2026-09-10"})
    plan = fu.run_pipeline("grok-4.6?effort=xhigh&fast=true", job_id="smoke25", write=True)
    check(plan["profile"] == "HOT_V3_FUSION" and plan["candidate"] is False and plan["orders_sent"] is False, "plan profile / not candidate / no orders")
    check(plan["layer_a"]["status"] == "SMOKE_STUB" and plan["layer_b"]["status"] == "SMOKE_STUB", "smoke stubs used for both Grok layers")
    check(plan["layer_a"]["leak_hits"] == [], "pipeline anon payload no leak")
    check(fu.LAST_PATH.is_file() and fu.plan_path(plan["asof"]).is_file(), "FUSION_LAST + FUSION_PLAN written")
    check(fu.ANON_LOG.is_file() and not anon.leak_hits(json.dumps(json.load(open(str(fu.ANON_LOG), encoding="utf-8"))["items"][-1]["sent"])), "FUSION_ANON_LOG clean")
    check("账本2 未读完" in " ".join(plan["warnings"]) or plan["book2"]["complete"], "book2 gate text present until 29 periods")
    check(plan["counts"]["buy"] <= fu.MAX_NAMES, "plan ≤ 8 buys")
    check(plan["budget"]["post_plan_notional"] <= plan["exposure_pct"] / 100.0 * plan["budget"]["equity"] + 1e-6, "plan respects cap")
    check(all(r["action"] in ("BUY", "HOLD", "SELL") for r in plan["actions"]), "plan actions valid")
    after = frozen.read_bytes() if frozen.is_file() else b""
    check(before == after, "fusion never writes frozen live/paper/JOURNAL.json")

    # 6. dead-thread reconcile
    fu._dump(fu.RUN_PATH, {"running": True, "stage": "Layer B", "started_at": "2026-09-11T19:00:00", "job_id": "dead"})
    st = fu.run_state()
    check(st["running"] is False and st["stage"] == "失败" and st.get("error"), "FUSION_RUN dead thread reconciled")
    v = fu.view()
    check(v["profile"] == "HOT_V3_FUSION" and v["plan"] is not None and v["book2"]["candidate"] is False, "fusion view")

    # 7. book2 GROK_TIMEOUT handling (resume-safe, excluded from TWR)
    smoke_b2 = paths.HOT / "B2_LEDGER_SMOKE25.json"
    smoke_log = paths.HOT / "B2_ANON_LOG_SMOKE25.json"
    smoke_run = paths.HOT / "B2_RUN_SMOKE25.json"
    b2.B2_PATH, b2.B2_LOG, b2.B2_RUN = smoke_b2, smoke_log, smoke_run
    calls = [0]

    def flaky(payload, ids):
        calls[0] += 1
        if calls[0] == 2:
            raise grok_keep.GrokTimeout("GROK_TIMEOUT simulated")
        return list(ids)

    out = b2.run_window(limit=2, keep_fn=flaky, resume=False)
    check(out["n_periods"] == 1 and out["n_timeout"] == 1, "timeout period counted separately", "n=%s to=%s" % (out["n_periods"], out["n_timeout"]))
    check(out["periods"][-1]["status"] == "GROK_TIMEOUT" and out["periods"][-1]["keep"] is None, "timeout period keep=None")
    run = json.loads(smoke_run.read_text(encoding="utf-8"))
    check(run["running"] is False and run.get("stopped_reason") == "GROK_TIMEOUT", "run marked stopped on timeout")
    out2 = b2.run_window(limit=2, keep_fn=lambda p, ids: list(ids), resume=True)
    check(out2["n_periods"] == 2 and out2["n_timeout"] == 0 and out2["complete"], "resume retries the timeout period")
    for p in (smoke_b2, smoke_log, smoke_run):
        if p.exists():
            os.remove(str(p))

    # 8. auto paper fills (settle at next open) on the smoke journal
    from app.service import paper_fusion_fill as ff
    ff.FILLS_PATH = smoke_dir / "FUSION_FILLS_SMOKE.json"
    ff.SETTINGS_PATH = smoke_dir / "FUSION_SETTINGS_SMOKE.json"
    ff.DAILY_RUN_PATH = smoke_dir / "FUSION_DAILY_RUN_SMOKE.json"
    plan_a = smoke_dir / "FUSION_PLAN_SMOKE_A.json"
    plan_b = smoke_dir / "FUSION_PLAN_SMOKE_B.json"
    for p in (ff.FILLS_PATH, ff.SETTINGS_PATH, ff.DAILY_RUN_PATH, plan_a, plan_b, hot.JOURNAL):
        if p.exists():
            os.remove(str(p))
    opens = {("sh.600001", "2026-09-14"): 11.0, ("sz.000999", "2026-09-14"): 10.0, ("sh.600002", "2026-09-14"): 50.0,
             ("sh.600003", "2026-09-14"): 20.0, ("sh.600004", "2026-09-14"): 30.0, ("sh.600777", "2026-09-14"): 12.0}
    orig_open, orig_files = ff.open_price, ff.plan_files
    ff.open_price = lambda sym, d: opens.get((sym, d))
    ff.plan_files = lambda: [plan_a, plan_b]
    hot.SETTINGS_PATH = ff.SETTINGS_PATH  # seed = default initial_capital 20000 (no real settings file)
    hot.add_event({"type": "DEPOSIT", "amount": 20000, "date": "2026-09-10"}, extra={"seed": True})  # evidence only; seed counted once
    check(hot.derive_account(hot.load_journal(), po._days())["cash"] == 20000.0, "settle account starts from the 20000 seed")
    hot.add_event({"type": "BUY", "symbol": "sh.600001", "lots": 2, "price": 10.0, "date": "2026-09-11"})
    hot.add_event({"type": "BUY", "symbol": "sz.000999", "lots": 1, "price": 10.0, "date": "2026-09-14"})  # same-day buy → T+1 lock
    fu._dump(plan_a, {"job_id": "planA", "asof": "2026-09-11", "fill_date": "2026-09-14", "actions": [
        {"symbol": "sh.600001", "action": "SELL", "lots": 2, "reason": "smoke sell"}, {"symbol": "sz.000999", "action": "SELL", "lots": 1},
        {"symbol": "sh.600777", "action": "SELL", "lots": 1}, {"symbol": "sh.600002", "action": "BUY", "lots": 3},
        {"symbol": "sh.600003", "action": "BUY", "lots": 5}, {"symbol": "sh.600004", "action": "BUY", "lots": 2},
        {"symbol": "sh.600005", "action": "HOLD", "lots": 1}]})
    fu._dump(plan_b, {"job_id": "planB", "asof": "2026-09-14", "fill_date": "2026-09-15", "actions": [{"symbol": "sh.600002", "action": "BUY", "lots": 1}]})
    s1 = ff.settle_pending()
    check(s1["enabled"] is True and len(s1["settled"]) == 1 and len(s1["pending"]) == 1, "plan A settled, plan B pending (no bar yet)")
    rec = s1["settled"][0]
    filled = {f["symbol"]: f for f in rec["filled"]}
    skipped = {s["symbol"]: s["why"] for s in rec["skipped"]}
    check(filled.get("sh.600001", {}).get("price") == 11.0 and filled["sh.600001"]["lots"] == 2, "SELL filled at next open (11.0)")
    check(skipped.get("sz.000999") == "T_PLUS_ONE_LOCKED", "T+1: same-day lot not sold")
    check(skipped.get("sh.600777") == "SELL_NOT_HELD", "SELL of unheld name skipped with reason")
    check(filled.get("sh.600002", {}).get("lots") == 3 and filled["sh.600002"]["price"] == 50.0, "BUY filled 3 lots @ open 50")
    check(filled.get("sh.600003", {}).get("lots") == 1 and filled["sh.600003"]["partial"] is True, "BUY rounded down by cash (5 → 1 lot)")
    check(skipped.get("sh.600004") == "CASH_FLOOR", "BUY beyond cash − ¥200 skipped")
    acct = po.derive_account(hot.load_journal(), po._days())
    check(acct["cash"] >= fu.CASH_RESERVE - 1e-6, "cash never below reserve", "cash=%.2f" % acct["cash"])
    ev_auto = [e for e in hot.load_journal()["events"] if e.get("auto")]
    check(len(ev_auto) == 3 and all(e.get("plan_id") == "planA" and e["note"].startswith("FUSION auto") for e in ev_auto), "auto events carry auto/plan_id/note")
    check(all(isinstance(e.get("snapshot"), dict) and "cash" in e["snapshot"] for e in ev_auto), "auto fills pin account snapshot")
    sell_ev = [e for e in ev_auto if e.get("symbol") == "sh.600001"]
    check(sell_ev and sell_ev[0].get("reason") == "smoke sell", "auto fill copies plan reason")
    check(all(abs(e["fee"] - po._est_fee(e["type"], e["amount"])) < 1e-6 for e in ev_auto), "fees via paper_ops estimator")
    check(json.load(open(str(plan_a), encoding="utf-8")).get("settled_at") and ff.FILLS_PATH.is_file(), "plan marked settled + FUSION_FILLS written")
    n_before = len(hot.load_journal()["events"])
    s2 = ff.settle_pending()
    check(len(s2["settled"]) == 0 and len(hot.load_journal()["events"]) == n_before, "rerun is idempotent (no double fill)")
    ff.set_auto_fill(False)
    s3 = ff.settle_pending()
    check(s3["enabled"] is False and not s3["settled"], "toggle off → nothing registered")
    ff.set_auto_fill(True)
    called = [0]
    sessions_seen = []

    def fake_pipeline(model_id, job_id, write, session=None):
        called[0] += 1
        sessions_seen.append(session)
        plan = {"asof": "2026-09-12", "fill_date": "2026-09-14", "exposure_pct": 0, "counts": {}, "actions": [],
                "layer_a": {"status": "SKIPPED_LIVE_SESSION"}, "layer_b": {"status": "SMOKE_STUB"},
                "settled_at": "x", "cash_policy": "HOLD_CASH"}
        if write and session:
            fu._dump(fu.session_plan_path(fake_pipeline.day, session), plan)
        return plan
    fake_pipeline.day = "2026-09-11"

    ff.SESSIONS_PATH = smoke_dir / "FUSION_SESSIONS_SMOKE.json"
    orig_spp = fu.session_plan_path
    fu.session_plan_path = lambda asof, s: smoke_dir / ("FUSION_PLAN_SMOKE_%s_%s.json" % (asof, s))
    for p in (ff.SESSIONS_PATH,):
        if p.exists():
            os.remove(str(p))
    orig_fresh = po.freshness
    po.freshness = lambda days, status, with_gap=False: {"today": "2026-09-11", "today_is_trading_day": True, "asof_session": "2026-09-10", "last_completed_session": "2026-09-11", "needs_update": True, "stale_sessions": 1}
    d1 = ff.run_daily("dailyA", "", pipeline=fake_pipeline)
    check(d1["pipeline"] == "RAN" and called[0] == 1 and sessions_seen[-1] == "close" and "晚上至少看一次" in (d1.get("note") or ""),
          "stale evening with 0 looks → RAN (must 1/day)")
    d_open = ff.run_session("open", "openA", "", pipeline=fake_pipeline)
    check(d_open["pipeline"] == "RAN" and sessions_seen[-1] == "open" and "T-1" in (d_open.get("note") or ""), "open session runs on T-1 bars, fills next open")
    d_open2 = ff.run_session("open", "openB", "", pipeline=fake_pipeline)
    check(d_open2["pipeline"] == "SKIPPED_ALREADY_PLANNED" and called[0] == 2, "second open session same day → no second Grok call")
    d_close_stale = ff.run_session("close", "closeA", "", pipeline=fake_pipeline)
    check(d_close_stale["pipeline"] == "SKIPPED_ALREADY_PLANNED" and called[0] == 2, "close already written by evening must-look")
    po.freshness = lambda days, status, with_gap=False: {"today": "2026-09-11", "today_is_trading_day": True, "asof_session": "2026-09-11", "last_completed_session": "2026-09-11", "needs_update": False, "stale_sessions": 0}
    d_close = ff.run_session("close", "closeB", "", pipeline=fake_pipeline)
    check(d_close["pipeline"] == "SKIPPED_ALREADY_PLANNED" and called[0] == 2, "second close same day → no second Grok call")
    d2 = ff.run_daily("dailyB", "", pipeline=fake_pipeline)
    check(d2["pipeline"] == "SKIPPED_ALREADY_PLANNED" and called[0] == 2, "19:30 daily after close plan → settle only, no 4th call")
    d_settle = ff.run_session("settle", "settleA", "", pipeline=fake_pipeline)
    check(d_settle["pipeline"] == "SETTLE_ONLY" and called[0] == 2, "settle session never calls Grok")
    try:
        ff.run_session("teatime", "x", "", pipeline=fake_pipeline)
        check(False, "bad session rejected")
    except ValueError:
        check(True, "bad session rejected")
    st = ff.sessions_today("2026-09-11")
    check(st["n_calls_today"] == 2 and st["max_calls_per_day"] == 3 and set(st["sessions"].keys()) >= {"open", "close", "daily", "settle"}, "sessions log: n_calls_today counts RAN only")
    j_keep = hot.load_journal()
    hot._dump(hot.JOURNAL, {"events": []})
    ff.set_initial_capital(200)
    d_cap = ff.run_session("lunch", "capA", "", pipeline=fake_pipeline)
    check(d_cap["pipeline"] == "SKIPPED_NO_CAPACITY" and called[0] == 2, "daytime: no sellable and no buy cash → skip Grok")
    fake_pipeline.day = "2026-09-15"
    po.freshness = lambda days, status, with_gap=False: {"today": "2026-09-15", "today_is_trading_day": True, "asof_session": "2026-09-14", "last_completed_session": "2026-09-15", "needs_update": True, "stale_sessions": 1}
    d_o15 = ff.run_session("open", "cap15o", "", pipeline=fake_pipeline)
    check(d_o15["pipeline"] == "SKIPPED_NO_CAPACITY" and called[0] == 2, "isolated day daytime still skips when no capacity")
    d_e15 = ff.run_daily("cap15d", "", pipeline=fake_pipeline)
    check(d_e15["pipeline"] == "RAN" and called[0] == 3 and sessions_seen[-1] == "close" and "晚上至少看一次" in (d_e15.get("note") or ""),
          "cannot trade: daytime skip, evening still looks")
    ff.set_initial_capital(20000)
    hot._dump(hot.JOURNAL, j_keep)
    po.freshness = orig_fresh
    fu.session_plan_path = orig_spp
    av = ff.auto_fill_view()
    check(av["enabled"] is True and av["n_auto_events"] == 3 and av["last_settle"]["plan_id"] == "planA" and "sessions" in av, "auto_fill view (+sessions)")

    # 9. live session pipeline with stubs: Layer A skipped, universe clamp, ADD/REDUCE/REPLACE math
    plan_s = fu.run_pipeline("grok-4.6?effort=xhigh&fast=true", job_id="smoke25s", write=False, session="lunch")
    check(plan_s["layer_a"]["status"] == "SKIPPED_LIVE_SESSION" and plan_s["layer_a"]["n_keep"] == plan_s["layer_a"]["n_in"], "live session: Layer A not called, pool not shrunk")
    check(plan_s["session"] == "lunch" and plan_s["layer_b"]["status"] == "SMOKE_STUB", "live session plan tagged, one Grok (stub) call")
    check(any(d["symbol"] == "sh.999999" and d["why"] == "OUT_OF_UNIVERSE" for d in plan_s["dropped"]), "invented ticker dropped OUT_OF_UNIVERSE")
    check(plan_s.get("cash_policy") in ("HOLD_CASH", "DEPLOY_IN_POOL", "ROTATE_IN_POOL", "SELL_TO_CASH"), "plan has cash_policy")
    check("n_new" in (plan_s.get("pool") or {}) and "refill_rule" in (plan_s.get("pool") or {}), "pool stamped NEW/OLD + refill rule")
    pr = fu.layer_b_prompt({"session": "open", "__template__": True})
    check("本场不再调你第二次" in pr and "不写 :9000" in pr and "记台账" in pr, "live prompt: refresh :9001 pool, no second Grok, no :9000 write")
    kept2 = [{"symbol": "sh.600%03d" % i, "name": "K%d" % i, "last_close": 10.0, "source": "SHORTLIST", "rank": i, "score": 0.1} for i in range(1, 6)]
    acct2 = {"equity": 30000.0, "cash": 5000.0, "positions": [
        {"symbol": "sz.000999", "name": "OLD", "lots": 4, "market_value": 8000.0, "mark_price": 20.0, "buy_date": "2026-09-01", "sellable_at_fill": True},
        {"symbol": "sz.000888", "name": "OLD2", "lots": 3, "market_value": 3000.0, "mark_price": 10.0, "buy_date": "2026-09-01", "sellable_at_fill": True},
    ]}
    out3 = fu.enforce({"exposure_pct": 80, "names": [
        {"symbol": "sz.000999", "action": "REDUCE", "lots_hint": 1},
        {"symbol": "sz.000888", "action": "REPLACE", "replace_with": "sh.600001", "lots_hint": 2},
        {"symbol": "sh.600002", "action": "ADD", "lots_hint": 1},                       # not held → dropped
        {"symbol": "sh.600003", "action": "BUY", "lots_hint": 2},
        {"symbol": "sh.777777", "action": "BUY", "lots_hint": 1},                       # not in universe
    ]}, kept2, acct2, "2026-09-14", "OK")
    by3 = {r["symbol"]: r for r in out3["actions"]}
    w3 = {d["symbol"]: d["why"] for d in out3["dropped"]}
    check(by3["sz.000999"]["action"] == "SELL" and by3["sz.000999"]["kind"] == "REDUCE" and by3["sz.000999"]["lots"] == 1, "REDUCE → partial SELL 1 lot")
    check(by3["sz.000888"]["action"] == "SELL" and by3["sz.000888"]["kind"] == "REPLACE_OUT" and by3["sh.600001"]["action"] == "BUY" and by3["sh.600001"]["kind"] == "REPLACE_IN", "REPLACE → SELL old + BUY new (pool)")
    check(w3.get("sh.600002") == "ADD_NOT_HELD" and w3.get("sh.777777") == "OUT_OF_UNIVERSE", "ADD on unheld dropped; out-of-universe dropped")
    check(out3["budget"]["sell_proceeds_net"] > 0 and out3["budget"]["planned_buy_notional"] <= out3["budget"]["buy_budget"] + 1e-6, "buy budget counts SELL proceeds (settle sells first)")
    check(out3["budget"]["post_plan_notional"] <= 0.8 * 30000.0 + 1e-6, "ADD/REDUCE/REPLACE respect exposure cap")
    check(out3["cash_policy"] == "ROTATE_IN_POOL", "sell+buy → ROTATE_IN_POOL")
    check(by3["sz.000999"].get("name_source") == "HELD" and by3["sz.000999"].get("pool_age") == "HELD_OUT_OF_POOL", "held-out-of-pool tagged")
    check(by3["sh.600001"].get("name_source") == "SHORTLIST", "pool buy tagged SHORTLIST")
    out_hold = fu.enforce({"exposure_pct": 0, "names": []}, kept2, acct2, "2026-09-14", "OK")
    check(out_hold["cash_policy"] == "HOLD_CASH", "no buy/sell → HOLD_CASH (refresh is a later file write, not a second model)")
    out4 = fu.enforce({"exposure_pct": 80, "names": [{"symbol": "sz.000999", "action": "ADD", "lots_hint": 1}]}, kept2, acct2, "2026-09-14", "OK")
    add = [r for r in out4["actions"] if r["symbol"] == "sz.000999" and r["action"] == "BUY"]
    check(len(add) == 1 and add[0]["kind"] == "ADD" and add[0]["lots"] == 1 and abs(add[0]["est_yuan"] - 2000.0) < 1e-6, "ADD on held name → BUY 1 lot = 100 shares at mark")
    check(os.path.isfile(os.path.join(ROOT, "scripts", "hot_fusion_session.bat")) and os.path.isfile(os.path.join(ROOT, "scripts", "hot_fusion_daily.bat")), "session/daily bat scripts exist")
    fd = fu.resolve_fill_date({"today": "2026-09-11", "next_trading_day": None, "asof_session": "2026-09-10"}, [])
    check(fd == "2026-09-14", "fill_date weekday walk when calendar has no future dates", fd)
    check(fu.resolve_fill_date({"today": "2026-09-11", "next_trading_day": "2026-09-14"}, ["2026-09-14"]) == "2026-09-14", "fill_date prefers freshness.next_trading_day")
    clk = fu.clocks_block({"today": "2026-09-11", "asof_session": "2026-09-10", "clock": "2026-09-11 15:05", "stale_sessions": 1, "next_trading_day": "2026-09-14"})
    check(clk["conflict"] == "EXPECTED" and clk["local_marks_are_today"] is False and clk["fill_date"] == "2026-09-14", "clocks split T-1 local vs next-open fill")
    ff.open_price, ff.plan_files = orig_open, orig_files
    for p in (ff.FILLS_PATH, ff.SETTINGS_PATH, ff.DAILY_RUN_PATH, ff.SESSIONS_PATH, plan_a, plan_b,
              smoke_dir / "FUSION_PLAN_SMOKE_2026-09-11_open.json", smoke_dir / "FUSION_PLAN_SMOKE_2026-09-11_close.json",
              smoke_dir / "FUSION_PLAN_SMOKE_2026-09-15_close.json"):
        if p.exists():
            os.remove(str(p))

    for p in (hot.JOURNAL, fu.LAST_PATH, fu.RUN_PATH, fu.ANON_LOG, fu.POOL_PATH, fu.plan_path(plan["asof"])):
        if p.exists():
            os.remove(str(p))
    hot.JOURNAL, fu.LAST_PATH, fu.RUN_PATH, fu.ANON_LOG, fu.plan_path, fu.POOL_PATH = orig
    print("SMOKE 25 hot fusion:", "PASS" if not FAILED[0] else "FAIL %d" % FAILED[0])
    return 1 if FAILED[0] else 0


if __name__ == "__main__":
    sys.exit(main())
