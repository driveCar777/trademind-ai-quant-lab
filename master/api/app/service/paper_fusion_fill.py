"""Hot Desk V3 auto paper fills (:9001 only).

Every fusion plan (`FUSION_PLAN_{asof}.json`) is settled automatically once its `fill_date` has an open price on disk:
BUY/SELL events are written to the hot `JOURNAL.json` at that day's OPEN with the same fee estimator paper_ops uses.
Simulated fills only — nothing is sent anywhere, no order_send, not a Candidate. Does not touch :9000 / daily.py /
paper_ops.py / live/paper/JOURNAL.json.
"""
from __future__ import annotations

import csv
import logging
import threading
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.service import paper_fusion as fu
from app.service import paper_hot as hot
from app.service import paper_ops as po

log = logging.getLogger("app.paper_fusion_fill")

HOT = hot.HOT
SETTINGS_PATH = HOT / "FUSION_SETTINGS.json"
FILLS_PATH = HOT / "FUSION_FILLS.json"
DAILY_RUN_PATH = HOT / "FUSION_DAILY_RUN.json"
CASH_RESERVE = fu.CASH_RESERVE
BUY_MIN_YUAN = 200.0  # 1 手 × 约 ¥2：预算不够这一笔就不诊
NOTE_PREFIX = "FUSION auto"

_lock = threading.Lock()
_thread: Optional[threading.Thread] = None


# ----------------------------------------------------------------------------- io
def _load(path: Path, default: Any) -> Any:
    return hot._load(path, default)


def _dump(path: Path, obj: Any) -> None:
    hot._dump(path, obj)


def settings() -> Dict[str, Any]:
    """Shared with paper_hot.settings(); SETTINGS_PATH may be swapped by smoke."""
    hot.SETTINGS_PATH = SETTINGS_PATH
    return hot.settings()


def set_auto_fill(flag: bool) -> Dict[str, Any]:
    hot.SETTINGS_PATH = SETTINGS_PATH
    return hot.save_settings(auto_fill=bool(flag))


def set_initial_capital(cap: float) -> Dict[str, Any]:
    cap = float(cap)
    if cap <= 0:
        raise ValueError("initial_capital 必须 > 0")
    hot.SETTINGS_PATH = SETTINGS_PATH
    return hot.save_settings(initial_capital=cap)


def plan_files() -> List[Path]:
    """Overridable (smoke swaps it). Real plans only; smoke/other files excluded."""
    if not HOT.is_dir():
        return []
    return sorted(p for p in HOT.glob("FUSION_PLAN_20*.json") if "SMOKE" not in p.name)


def _plan_id(plan: Dict[str, Any], path: Path) -> str:
    return str(plan.get("job_id") or path.stem)


# ----------------------------------------------------------------------------- bars
def open_price(symbol: str, date: str) -> Optional[float]:
    """Open of `symbol` on `date` from live/bars (read-only). None if the bar is not on disk yet."""
    p = po.BARS / (symbol + ".csv")
    if not p.is_file() or not date:
        return None
    try:
        with open(p, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if (r.get("date") or "") == date:
                    try:
                        o = float(r.get("open") or 0)
                    except ValueError:
                        return None
                    return o if o > 0 else None
    except OSError:
        return None
    return None


# ----------------------------------------------------------------------------- capacity (ops, not a strategy)
def action_capacity(fresh: Dict[str, Any], days: Optional[List[str]] = None) -> Dict[str, Any]:
    """Can this session change the book? Sellable T+1 names, or cash enough for one cheap lot."""
    days = days or po._days()
    acc = hot.derive_account(hot.load_journal(), days)
    sellable = []
    for p in acc.get("positions") or []:
        if hot._sellable(p.get("buy_date"), fresh):
            sellable.append({"symbol": p.get("symbol"), "lots": p.get("lots")})
    cash = float(acc.get("cash") or 0.0)
    budget = cash - CASH_RESERVE
    can_sell = len(sellable) > 0
    can_buy = budget >= BUY_MIN_YUAN
    return {
        "can_sell": can_sell, "can_buy": can_buy, "can_act": can_sell or can_buy,
        "cash": round(cash, 2), "budget": round(budget, 2),
        "n_sellable": len(sellable), "sellable": sellable,
    }


def _fill_extra(plan: Dict[str, Any], action: Dict[str, Any], pid: str, fill_date: str, px: float) -> Dict[str, Any]:
    snap = hot.ticket_snapshot()
    snap.update({
        "asof": plan.get("asof"), "fill_date": fill_date, "session": plan.get("session"),
        "price_source": "live_bars_open", "fill_price": px,
        "kind": action.get("kind"), "lots_requested": action.get("lots"),
    })
    return {
        "auto": True, "plan_id": pid, "reason": action.get("reason") or "",
        "session": plan.get("session"), "snapshot": snap,
        "name_source": action.get("name_source"), "pool_age": action.get("pool_age"),
        "pool_signal_date": (plan.get("pool") or {}).get("signal_date"),
    }


# ----------------------------------------------------------------------------- settle
def _lots_bought_on(journal: Dict[str, Any], symbol: str, date: str) -> int:
    return sum(int(e.get("lots") or 0) for e in journal.get("events") or []
               if e.get("type") == "BUY" and e.get("symbol") == symbol and e.get("date") == date)


def _settle_one(plan: Dict[str, Any], path: Path, days: List[str], now_iso: str) -> Dict[str, Any]:
    pid = _plan_id(plan, path)
    fill_date = plan.get("fill_date") or ""
    actions = [a for a in (plan.get("actions") or []) if a.get("action") in ("BUY", "SELL")]
    rec: Dict[str, Any] = {"plan_id": pid, "asof": plan.get("asof"), "session": plan.get("session"), "fill_date": fill_date, "plan_file": path.name,
                           "requested": [{"symbol": a["symbol"], "action": a["action"], "lots": a.get("lots")} for a in actions],
                           "filled": [], "skipped": [], "status": None, "settled_at": None}
    if not fill_date:
        rec["status"] = "NO_FILL_DATE"
        return rec
    # any bar for fill_date on disk? (plans with only HOLD still settle trivially once the day exists)
    probe_syms = [a["symbol"] for a in actions] or [r.get("symbol") for r in plan.get("actions") or [] if r.get("symbol")]
    have_bar = any(open_price(s, fill_date) is not None for s in probe_syms)
    if not have_bar:
        if actions:
            rec["status"] = "PENDING_NO_BAR"
            return rec
        rec["status"] = "SETTLED_NOTHING_TO_DO"
        rec["settled_at"] = now_iso
        return rec
    journal = hot.load_journal()
    account = hot.derive_account(journal, days)  # seeded with initial_capital
    cash = float(account.get("cash") or 0.0)
    held = {p["symbol"]: p for p in account.get("positions") or []}
    # SELL first (releases cash), then BUY
    for a in sorted(actions, key=lambda r: 0 if r["action"] == "SELL" else 1):
        sym, act = a["symbol"], a["action"]
        want = int(a.get("lots") or 0)
        px = open_price(sym, fill_date)
        base = {"symbol": sym, "action": act, "lots_requested": want}
        if px is None:
            rec["skipped"].append(dict(base, why="NO_BAR_AT_FILL_DATE"))
            continue
        if want <= 0:
            rec["skipped"].append(dict(base, why="ZERO_LOTS"))
            continue
        if act == "SELL":
            pos = held.get(sym)
            if not pos or int(pos.get("lots") or 0) <= 0:
                rec["skipped"].append(dict(base, why="SELL_NOT_HELD"))
                continue
            locked = _lots_bought_on(journal, sym, fill_date)  # T+1: lots bought on fill_date cannot be sold
            sellable = int(pos.get("lots") or 0) - locked
            if sellable <= 0:
                rec["skipped"].append(dict(base, why="T_PLUS_ONE_LOCKED"))
                continue
            lots = min(want, sellable)
            amount = round(lots * po.LOT * px, 2)
            fee = po._est_fee("SELL", amount)
            ev = hot.add_event({"type": "SELL", "symbol": sym, "lots": lots, "price": px, "date": fill_date, "fee": fee,
                                "note": "%s %s" % (NOTE_PREFIX, plan.get("asof"))},
                               extra=_fill_extra(plan, a, pid, fill_date, px))
            cash += amount - fee
            held[sym]["lots"] = int(held[sym]["lots"]) - lots
            rec["filled"].append(dict(base, lots=lots, price=px, amount=amount, fee=fee, event_id=ev["id"],
                                      partial=lots < want))
            journal = hot.load_journal()
            continue
        # BUY: cash floor
        budget = cash - CASH_RESERVE
        lots = want
        while lots > 0 and lots * po.LOT * px + po._est_fee("BUY", lots * po.LOT * px) > budget:
            lots -= 1
        if lots <= 0:
            rec["skipped"].append(dict(base, why="CASH_FLOOR", cash=round(cash, 2)))
            continue
        amount = round(lots * po.LOT * px, 2)
        fee = po._est_fee("BUY", amount)
        ev = hot.add_event({"type": "BUY", "symbol": sym, "lots": lots, "price": px, "date": fill_date, "fee": fee,
                            "note": "%s %s" % (NOTE_PREFIX, plan.get("asof"))},
                           extra=_fill_extra(plan, a, pid, fill_date, px))
        cash -= amount + fee
        rec["filled"].append(dict(base, lots=lots, price=px, amount=amount, fee=fee, event_id=ev["id"], partial=lots < want))
        journal = hot.load_journal()
    rec["status"] = "SETTLED"
    rec["settled_at"] = now_iso
    rec["cash_after"] = round(cash, 2)
    return rec


def settle_pending() -> Dict[str, Any]:
    """Settle every unsettled plan whose fill_date bar exists. Idempotent: settled plans carry `settled_at` and are
    also listed in FUSION_FILLS.json; both guards are checked before writing anything."""
    now_iso = po._now().strftime("%Y-%m-%dT%H:%M:%S")
    fills = _load(FILLS_PATH, None) or {"items": []}
    done_ids = {it.get("plan_id") for it in fills.get("items") or [] if it.get("settled_at")}
    days = po._days()
    out: Dict[str, Any] = {"at": now_iso, "enabled": settings()["auto_fill"], "settled": [], "pending": [], "skipped_plans": [],
                           "superseded": []}
    if not out["enabled"]:
        out["note"] = "自动纸面登记已关闭（FUSION_SETTINGS.auto_fill=false）；计划照出，不登记。"
        return out
    # Later plan for the same fill_date supersedes earlier unsettled ones (open → lunch → close revise each other).
    open_plans: List[Tuple[Path, Dict[str, Any]]] = []
    for path in plan_files():
        plan = _load(path, None)
        if isinstance(plan, dict) and not plan.get("settled_at") and _plan_id(plan, path) not in done_ids:
            open_plans.append((path, plan))
    by_fill: Dict[str, List[Tuple[Path, Dict[str, Any]]]] = {}
    for path, plan in open_plans:
        by_fill.setdefault(plan.get("fill_date") or "", []).append((path, plan))
    for fd, group in by_fill.items():
        if not fd or len(group) < 2:
            continue
        group.sort(key=lambda t: str(t[1].get("generated_at") or ""))
        latest_id = _plan_id(group[-1][1], group[-1][0])
        with _lock:
            for path, plan in group[:-1]:
                pid = _plan_id(plan, path)
                plan["settled_at"] = now_iso
                plan["superseded_by"] = latest_id
                plan["fills"] = {"n_filled": 0, "n_skipped": 0, "status": "SUPERSEDED"}
                _dump(path, plan)
                rec = {"plan_id": pid, "asof": plan.get("asof"), "session": plan.get("session"), "fill_date": fd, "plan_file": path.name,
                       "requested": [{"symbol": a["symbol"], "action": a["action"], "lots": a.get("lots")} for a in plan.get("actions") or [] if a.get("action") != "HOLD"],
                       "filled": [], "skipped": [], "status": "SUPERSEDED", "superseded_by": latest_id, "settled_at": now_iso}
                fills.setdefault("items", []).append(rec)
                out["superseded"].append({"plan_id": pid, "by": latest_id, "session": plan.get("session")})
                done_ids.add(pid)
            _dump(FILLS_PATH, fills)
    for path in plan_files():
        plan = _load(path, None)
        if not isinstance(plan, dict):
            continue
        pid = _plan_id(plan, path)
        if plan.get("settled_at") or pid in done_ids:
            continue
        with _lock:
            rec = _settle_one(plan, path, days, now_iso)
            if rec["status"] in ("PENDING_NO_BAR",):
                out["pending"].append({"plan_id": pid, "asof": plan.get("asof"), "fill_date": plan.get("fill_date")})
                continue
            if rec["status"] == "NO_FILL_DATE":
                out["skipped_plans"].append({"plan_id": pid, "why": rec["status"]})
                continue
            plan["settled_at"] = rec["settled_at"]
            plan["fills"] = {"n_filled": len(rec["filled"]), "n_skipped": len(rec["skipped"]), "status": rec["status"]}
            _dump(path, plan)
            last = _load(fu.LAST_PATH, None)
            if isinstance(last, dict) and _plan_id(last, path) == pid:
                last["settled_at"] = plan["settled_at"]
                last["fills"] = plan["fills"]
                _dump(fu.LAST_PATH, last)
            fills.setdefault("items", []).append(rec)
            fills["items"] = fills["items"][-200:]
            _dump(FILLS_PATH, fills)
            out["settled"].append(rec)
    return out


# ----------------------------------------------------------------------------- daily driver
def _save_daily(obj: Dict[str, Any]) -> None:
    try:
        _dump(DAILY_RUN_PATH, obj)
    except OSError as exc:
        log.warning("FUSION_DAILY_RUN write failed: %s", exc)


def _thread_alive() -> bool:
    t = _thread
    return t is not None and t.is_alive()


def daily_state() -> Dict[str, Any]:
    cur = _load(DAILY_RUN_PATH, {}) or {"running": False}
    if cur.get("running") and not _thread_alive() and hot._run_age_s(cur) > 5:
        cur["running"] = False
        cur["stage"] = "失败"
        cur.setdefault("error", "后台线程已退出（进程重启）。可以再跑一次。")
        _save_daily(cur)
    return cur


SESSIONS = ("open", "lunch", "close", "daily", "settle")
SESSION_TIMES = {"open": "09:35", "lunch": "11:30", "close": "15:05", "daily": "19:30"}
SESSIONS_PATH = HOT / "FUSION_SESSIONS.json"
MAX_GROK_CALLS_PER_DAY = 3


def _sessions_log() -> Dict[str, Any]:
    return _load(SESSIONS_PATH, None) or {"days": {}}


def _record_session(day: str, session: str, rec: Dict[str, Any]) -> None:
    sl = _sessions_log()
    day_d = sl.setdefault("days", {}).setdefault(day, {})
    prev = day_d.get(session)
    if prev and prev.get("pipeline") == "RAN" and rec.get("pipeline") != "RAN":
        prev["last_repeat"] = {"job_id": rec.get("job_id"), "pipeline": rec.get("pipeline"), "at": rec.get("finished_at")}
        rec = prev  # never lose the record of a billable call
    day_d[session] = rec
    keys = sorted(sl["days"].keys())
    for k in keys[:-90]:
        sl["days"].pop(k, None)
    _dump(SESSIONS_PATH, sl)


def sessions_today(today: Optional[str] = None) -> Dict[str, Any]:
    today = today or po._now().date().isoformat()
    sl = _sessions_log()
    day = (sl.get("days") or {}).get(today) or {}
    n_calls = sum(1 for s in day.values() if s.get("pipeline") == "RAN")
    now_hm = po._now().strftime("%H:%M")
    nxt = None
    for s in ("open", "lunch", "close", "daily"):
        if SESSION_TIMES[s] > now_hm and s not in day:
            nxt = {"session": s, "time": SESSION_TIMES[s], "label": fu.SESSION_LABEL.get(s)}
            break
    return {"date": today, "sessions": day, "n_calls_today": n_calls, "max_calls_per_day": MAX_GROK_CALLS_PER_DAY,
            "next": nxt, "schedule": SESSION_TIMES, "recent": _sessions_recent(10),
            "token_note": "能买卖时白天最多 3 次。不能买卖则白天跳过，晚上 19:30 仍至少看一次。计划按下一开盘自动记台账，不是等人点头。"}


def _sessions_recent(n: int = 10) -> List[Dict[str, Any]]:
    sl = (_sessions_log().get("days") or {})
    rows: List[Dict[str, Any]] = []
    for day in sorted(sl.keys(), reverse=True)[:n]:
        rec = sl[day] or {}
        item: Dict[str, Any] = {"date": day}
        for k in ("open", "lunch", "close", "daily"):
            r = rec.get(k) or {}
            item[k] = r.get("pipeline") or ""
        rows.append(item)
    return rows


def run_session(session: str, job_id: str, model_id: str = "", pipeline: Optional[Callable[..., Dict[str, Any]]] = None) -> Dict[str, Any]:
    """One scheduled session. Always settles first. Then:
    open/lunch/close: if can sell or buy, one Grok (T-1 bars OK); if cannot act → SKIPPED_NO_CAPACITY.
    daily (19:30): if the day had zero Grok calls, MUST look once even when stale / no cash / all T+1 locked
    (writes the close plan; fills stay next open). If daytime already looked and bars are stale → SKIPPED_STALE_DATA.
    settle: never calls Grok. Auto-fill writes the journal; this is not an approval prompt."""
    if session not in SESSIONS:
        raise ValueError("session 必须是 open / lunch / close / daily / settle")
    started = po._now().strftime("%Y-%m-%dT%H:%M:%S")
    days = po._days()
    status = po._load(po.STATUS, {}) or {}
    fresh = po.freshness(days, status, with_gap=False)
    today = fresh.get("today") or po._now().date().isoformat()
    st: Dict[str, Any] = {"running": True, "job_id": job_id, "session": session, "session_label": fu.SESSION_LABEL.get(session),
                          "stage": "结算待成交计划（下一开盘）", "started_at": started, "date": today}
    _save_daily(st)
    settle = settle_pending()
    st["settle"] = {"n_settled": len(settle["settled"]), "n_pending": len(settle["pending"]), "n_superseded": len(settle.get("superseded") or []),
                    "n_filled": sum(len(r["filled"]) for r in settle["settled"]),
                    "n_skipped": sum(len(r["skipped"]) for r in settle["settled"]), "enabled": settle["enabled"]}
    asof = fresh.get("asof_session") or ""
    last_done = fresh.get("last_completed_session") or ""
    stale = bool(fresh.get("needs_update") or not asof or (last_done and asof < last_done))
    st["freshness"] = {"asof_session": asof, "last_completed_session": last_done, "needs_update": fresh.get("needs_update"),
                       "stale_sessions": fresh.get("stale_sessions"), "today_is_trading_day": fresh.get("today_is_trading_day")}
    n_calls = sessions_today(today)["n_calls_today"]
    grok_session = "close" if session == "daily" else session
    plan_file = fu.session_plan_path(today, grok_session) if grok_session in fu.LIVE_SESSIONS else None
    must_evening = session == "daily" and n_calls == 0 and bool(fresh.get("today_is_trading_day"))
    cap = action_capacity(fresh, days)
    st["capacity"] = {k: cap[k] for k in ("can_act", "can_sell", "can_buy", "cash", "budget", "n_sellable")}
    if session == "settle":
        st["pipeline"] = "SETTLE_ONLY"
    elif not fresh.get("today_is_trading_day"):
        st["pipeline"] = "SKIPPED_NOT_TRADING_DAY"
        st["note"] = "%s 不是交易日，不调 Grok。" % today
    elif plan_file is not None and plan_file.is_file():
        st["pipeline"] = "SKIPPED_ALREADY_PLANNED"
        st["note"] = "今天的 %s 计划已存在（%s），不重复调 Grok。" % (fu.SESSION_LABEL.get(grok_session), plan_file.name)
    elif n_calls >= MAX_GROK_CALLS_PER_DAY:
        st["pipeline"] = "SKIPPED_CALL_BUDGET"
        st["note"] = "今天已调 Grok %d 次，达到上限 %d。" % (n_calls, MAX_GROK_CALLS_PER_DAY)
    elif session == "daily" and n_calls >= 1 and stale:
        st["pipeline"] = "SKIPPED_STALE_DATA"
        st["note"] = "白天已经诊过。19:30 补收盘需要今天的日线（asof %s < %s）。先在 :9000 更新。不调 Grok。" % (asof or "—", last_done or "—")
    elif fu.run_state().get("running") and fu._thread_alive():
        st["pipeline"] = "SKIPPED_RUN_IN_PROGRESS"
    elif session in ("open", "lunch", "close") and not cap["can_act"]:
        st["pipeline"] = "SKIPPED_NO_CAPACITY"
        st["note"] = "白天：没有可卖的票也买不起 1 手，这场跳过。晚上仍会至少看一次。"
    else:
        st["stage"] = "%s：出计划并记台账（1 次）" % fu.SESSION_LABEL.get(grok_session)
        if must_evening:
            st["note"] = "白天没诊过，晚上至少看一次（T-1+联网）。不能买卖也出计划：不合适就拿现金；有买卖按下一开盘自动记台账。"
        elif stale:
            st["note"] = "盘中计划基于 T-1 日线（asof %s）+ 持仓 + 联网；下一开盘自动记台账。" % asof
        _save_daily(st)
        fn = pipeline or fu.run_pipeline
        try:
            plan = fn(model_id, job_id, True, grok_session)
            la, lb = plan["layer_a"].get("status"), plan["layer_b"].get("status")
            st["pipeline"] = "RAN"
            st["plan"] = {"asof": plan.get("asof"), "session": grok_session, "fill_date": plan.get("fill_date"),
                          "exposure_pct": plan.get("exposure_pct"), "counts": plan.get("counts"), "layer_a": la, "layer_b": lb,
                          "cash_policy": plan.get("cash_policy"),
                          "n_actions": sum(1 for a in plan.get("actions") or [] if a.get("action") != "HOLD")}
        except Exception as exc:
            log.exception("session pipeline failed")
            st["pipeline"] = "FAILED"
            st["error"] = str(exc)[:400]
    st["running"] = False
    st["stage"] = "完成" if st.get("pipeline") != "FAILED" else "失败"
    st["finished_at"] = po._now().strftime("%Y-%m-%dT%H:%M:%S")
    _save_daily(st)
    _record_session(today, session, {k: st.get(k) for k in ("job_id", "pipeline", "note", "error", "started_at", "finished_at", "plan", "settle")})
    return st


def run_daily(job_id: str, model_id: str = "", pipeline: Optional[Callable[..., Dict[str, Any]]] = None) -> Dict[str, Any]:
    return run_session("daily", job_id, model_id, pipeline)


def start_session(session: str, model_id: str = "") -> Dict[str, Any]:
    global _thread
    if session not in SESSIONS:
        raise ValueError("session 必须是 open / lunch / close / daily / settle")
    with _lock:
        cur = daily_state()
        if cur.get("running") and _thread_alive():
            return cur
        job_id = uuid.uuid4().hex[:10]
        catalog = model_id
        if not fu._smoke() and session != "settle":
            catalog, _a, _p = __import__("app.service.cursor_cloud", fromlist=["resolve_model"]).resolve_model(model_id)
        t = threading.Thread(target=run_session, args=(session, job_id, catalog), daemon=True)
        _thread = t
        _save_daily({"running": True, "job_id": job_id, "session": session, "stage": "已提交", "started_at": po._now().strftime("%Y-%m-%dT%H:%M:%S")})
        t.start()
    return daily_state()


def start_daily(model_id: str = "") -> Dict[str, Any]:
    return start_session("daily", model_id)


# ----------------------------------------------------------------------------- view
def auto_fill_view() -> Dict[str, Any]:
    j = hot.load_journal()
    today = po._now().date().isoformat()
    auto_ev = [e for e in j.get("events") or [] if e.get("auto")]
    fills = _load(FILLS_PATH, None) or {"items": []}
    items = fills.get("items") or []
    last = items[-1] if items else None
    today_items = [it for it in items if str(it.get("settled_at") or "")[:10] == today]
    return {
        "enabled": settings()["auto_fill"],
        "last_daily": daily_state(),
        "sessions": sessions_today(today),
        "last_settle": last,
        "n_auto_events": len(auto_ev),
        "today": {"n_filled": sum(len(it.get("filled") or []) for it in today_items),
                  "n_skipped": sum(len(it.get("skipped") or []) for it in today_items),
                  "skipped": [s for it in today_items for s in (it.get("skipped") or [])]},
        "skipped": (last or {}).get("skipped") or [],
        "pending_plans": [{"asof": p.get("asof"), "fill_date": p.get("fill_date")} for p in
                          (_load(x, None) or {} for x in plan_files()) if isinstance(p, dict) and not p.get("settled_at")],
        "note": "自动纸面登记 = 模拟成交：按 fill_date 当天开盘价、估算费用写进热台 JOURNAL。没有真实下单。不是 Candidate。",
    }
