"""Hot-desk MT5 product books on :9001 only (Ava Trade demo).

Not a Candidate. Does not touch :9000 paper, daily.py, or the A-share journal.
Frequency is sparse (2 Grok calls / weekday): Asia 08:30 and New York 20:30 China time.
Each product has its own logic tag; stocks are one advisory basket and never auto-send
(V30 cost ceiling). Live accounts are refused. TRADEMIND_HOT_SMOKE=1 never sends.

Phase 2: Grok is Research/Hypothesis/News/Regime/Feature only.
LLM → BUY/SELL → order_send is NOT a strategy and is NOT a Candidate.
TRADEMIND_HOT_GROK_SEND defaults to 0 (off). The desk stays; auto-send does not.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.service import cursor_cloud as cc
from app.service import paper_hot as hot
from app.service.exceptions import TaskFailedError
from app.service.mt5_service import ALLOWED, Mt5Session, normalize_symbol, probe_mt5, send_allowed

log = logging.getLogger("app.paper_hot_mt5")

HOT = hot.HOT
SETTINGS_PATH = HOT / "MT5_SETTINGS.json"
JOURNAL_PATH = HOT / "MT5_JOURNAL.json"
LAST_PATH = HOT / "MT5_LAST.json"
RUN_PATH = HOT / "MT5_RUN.json"
SESSIONS_PATH = HOT / "MT5_SESSIONS.json"
LOG_PATH = HOT / "MT5_CRON.log"

PROFILE = "HOT_MT5_DEMO"
MAGIC = 260912
VOLUME = 0.01
MAX_GROK_CALLS_PER_DAY = 2
GROK_TIMEOUT_S = 900.0
SESSIONS = ("asia", "ny", "settle")
SESSION_TIMES = {"asia": "08:30", "ny": "20:30"}
SESSION_LABEL = {"asia": "亚洲盘 08:30", "ny": "纽约盘 20:30", "settle": "只记账"}

# Pre-registered product books. Logic text is a prompt hint, not a searched parameter.
PRODUCTS: Dict[str, Dict[str, Any]] = {
    "XAUUSD": {"label": "黄金", "logic": "实际利率、美元、避险、地缘。趋势品种，不剥头皮。", "send": True},
    "CRUDE": {"label": "原油", "logic": "供需/OPEC/地缘/美元。库存叙事极易已定价。", "send": True},
    "EURUSD": {"label": "欧美", "logic": "欧央行-美联储利差、风险偏好。", "send": True},
    "USDJPY": {"label": "美日", "logic": "美日利差、日央行干预风险。", "send": True},
    "GBPUSD": {"label": "美英", "logic": "英央行、英国数据、风险偏好。", "send": True},
    "USDCAD": {"label": "美加", "logic": "油价、加央行、美加利差。", "send": True},
    "USDCHF": {"label": "美瑞", "logic": "避险、瑞央行、欧系风险。", "send": True},
    "SHARES": {"label": "美股CFD篮子", "logic": "AVA 股票少；V30 成本天花板。只建议，不自动发单。", "send": False},
}

_lock = threading.Lock()
_thread = None


def _smoke() -> bool:
    return os.environ.get("TRADEMIND_HOT_SMOKE") == "1"


def _now() -> datetime:
    return datetime.now()


def _dump(path: Path, obj: Any) -> None:
    hot._dump(path, obj)


def _load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def settings() -> Dict[str, Any]:
    raw = _load(SETTINGS_PATH, None) or {}
    out = {"demo_send": True, "volume": VOLUME}
    if isinstance(raw.get("demo_send"), bool):
        out["demo_send"] = raw["demo_send"]
    try:
        vol = float(raw.get("volume") or VOLUME)
        if 0.01 <= vol <= 0.10:
            out["volume"] = vol
    except (TypeError, ValueError):
        pass
    return out


def save_settings(patch: Dict[str, Any]) -> Dict[str, Any]:
    cur = settings()
    if "demo_send" in patch and patch["demo_send"] is not None:
        cur["demo_send"] = bool(patch["demo_send"])
    if "volume" in patch and patch["volume"] is not None:
        vol = float(patch["volume"])
        if vol < 0.01 or vol > 0.10:
            raise ValueError("手数只允许 0.01–0.10")
        cur["volume"] = vol
    _dump(SETTINGS_PATH, cur)
    return cur


def grok_send_allowed() -> bool:
    """LLM may not order_send as a strategy. Default OFF (TRADEMIND_HOT_GROK_SEND=0)."""
    return os.environ.get("TRADEMIND_HOT_GROK_SEND", "0") == "1"


def want_send() -> bool:
    return bool(
        settings()["demo_send"]
        and send_allowed()
        and grok_send_allowed()
        and not _smoke()
    )


def _journal() -> Dict[str, Any]:
    j = _load(JOURNAL_PATH, None)
    if isinstance(j, dict) and isinstance(j.get("events"), list):
        return j
    return {"events": []}


def _add_event(ev: Dict[str, Any]) -> Dict[str, Any]:
    j = _journal()
    ev = dict(ev)
    ev.setdefault("id", uuid.uuid4().hex[:10])
    ev.setdefault("ts", _now().strftime("%Y-%m-%dT%H:%M:%S"))
    j["events"].append(ev)
    _dump(JOURNAL_PATH, j)
    return ev


def _ticket_snapshot(plan: Dict[str, Any], action: Dict[str, Any], sent: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    snap = plan.get("snapshot") or {}
    probe = snap.get("probe") or {}
    products = []
    for p in (snap.get("products") or [])[:8]:
        products.append({"id": p.get("id"), "bid": p.get("bid"), "ask": p.get("ask"), "broker": p.get("broker")})
    positions = []
    for p in (snap.get("positions") or [])[:16]:
        positions.append({
            "id": p.get("id") or p.get("logical"), "side": p.get("side"),
            "volume": p.get("volume"), "price_open": p.get("price_open"),
        })
    sent = sent or {}
    price = sent.get("price")
    if price is None:
        price = action.get("ask") if action.get("action") == "BUY" else action.get("bid")
    return {
        "session": plan.get("session"),
        "account_mode": probe.get("account_mode"),
        "login_masked": probe.get("login_masked"),
        "products": products,
        "positions": positions,
        "price": price,
        "bid": sent.get("bid", action.get("bid")),
        "ask": sent.get("ask", action.get("ask")),
        "volume": action.get("volume"),
        "kind": action.get("kind"),
        "send": action.get("send"),
        "sent": bool(sent.get("sent")),
        "ticket": sent.get("ticket") or "",
    }


def _record_fill(plan: Dict[str, Any], action: Dict[str, Any], paper: bool, sent: Optional[Dict[str, Any]] = None,
                 note: str = "") -> Dict[str, Any]:
    sent = sent or {}
    price = sent.get("price")
    if price is None:
        price = action.get("ask") if action.get("action") == "BUY" else action.get("bid")
    return _add_event({
        "type": action.get("action"),
        "product": action.get("id"),
        "volume": action.get("volume"),
        "price": price,
        "bid": sent.get("bid", action.get("bid")),
        "ask": sent.get("ask", action.get("ask")),
        "paper": paper,
        "ticket": sent.get("ticket") or "",
        "broker": sent.get("symbol") or action.get("broker"),
        "reason": action.get("reason") or "",
        "session": plan.get("session"),
        "note": note,
        "snapshot": _ticket_snapshot(plan, action, sent),
    })


def plan_path(day: str, session: str) -> Path:
    return HOT / ("MT5_PLAN_%s_%s.json" % (day, session))


def _logical_of_broker(broker: str) -> Optional[str]:
    n = (broker or "").upper().replace(" ", "").replace("_", "")
    for logical, names in ALLOWED.items():
        for alias in names:
            a = alias.upper().replace(" ", "").replace("_", "")
            if n == a or n.startswith(a) or a.startswith(n):
                return logical
    if n == "GOLD" or n.startswith("XAU"):
        return "XAUUSD"
    return None


def snapshot(session: Optional[str] = None) -> Dict[str, Any]:
    """Live MT5 ticks + positions. Independent of A-share evening bars."""
    probe = probe_mt5()
    products: List[Dict[str, Any]] = []
    positions: List[Dict[str, Any]] = []
    shares: List[str] = []
    if _smoke():
        probe = {"available": True, "connected": True, "account_mode": "demo", "login_masked": "****0000",
                 "reason": "SMOKE_STUB", "symbols": []}
        for pid, meta in PRODUCTS.items():
            products.append({"id": pid, "label": meta["label"], "logic": meta["logic"], "send": meta["send"],
                             "broker": pid if pid != "SHARES" else "", "bid": 1.0, "ask": 1.01,
                             "position": None, "bars_m15": [1.0] * 20})
        return {"session": session, "session_label": SESSION_LABEL.get(session or "", session),
                "clock": _now().strftime("%Y-%m-%d %H:%M"), "probe": probe, "products": products,
                "positions": [], "shares": ["AAPL", "MSFT"], "volume": settings()["volume"],
                "note": "SMOKE_STUB：不连终端、不发单。"}
    if probe.get("connected"):
        try:
            with Mt5Session() as sess:
                positions = sess.positions()
                by_logical: Dict[str, Dict[str, Any]] = {}
                for pos in positions:
                    logical = _logical_of_broker(pos.get("symbol") or "")
                    if logical:
                        by_logical[logical] = pos
                try:
                    shares = sess.list_share_symbols(12)
                except Exception:
                    shares = []
                for pid, meta in PRODUCTS.items():
                    row: Dict[str, Any] = {"id": pid, "label": meta["label"], "logic": meta["logic"],
                                           "send": meta["send"], "broker": "", "bid": None, "ask": None,
                                           "position": by_logical.get(pid), "bars_m15": []}
                    if pid == "SHARES":
                        row["candidates"] = shares
                    else:
                        try:
                            q = sess.last_price(pid)
                            row["broker"] = q.get("symbol")
                            row["bid"] = q.get("bid")
                            row["ask"] = q.get("ask")
                        except TaskFailedError as exc:
                            row["error"] = str(exc)[:160]
                        try:
                            pulled = sess.copy_closes(pid, bars=30, timeframe="M15")
                            row["bars_m15"] = (pulled.get("close") or [])[-20:]
                            row["broker"] = row["broker"] or pulled.get("symbol")
                        except TaskFailedError:
                            pass
                    products.append(row)
        except TaskFailedError as exc:
            probe = dict(probe)
            probe["connected"] = False
            probe["reason"] = str(exc)[:200]
            for pid, meta in PRODUCTS.items():
                products.append({"id": pid, "label": meta["label"], "logic": meta["logic"], "send": meta["send"],
                                 "broker": "", "bid": None, "ask": None, "position": None, "bars_m15": [],
                                 "error": "terminal_offline"})
    else:
        for pid, meta in PRODUCTS.items():
            products.append({"id": pid, "label": meta["label"], "logic": meta["logic"], "send": meta["send"],
                             "broker": "", "bid": None, "ask": None, "position": None, "bars_m15": []})
    return {
        "session": session, "session_label": SESSION_LABEL.get(session or "", session),
        "clock": _now().strftime("%Y-%m-%d %H:%M"), "probe": probe, "products": products,
        "positions": positions, "shares": shares, "volume": settings()["volume"],
        "hard_rules": {
            "account": "AVA MT5 demo only; live refused",
            "frequency": "2 sessions/weekday, 1 Grok call each, 1 deal/product/session",
            "volume": settings()["volume"],
            "shares": "advisory, never order_send",
            "not_a_candidate": True,
            "a_share_bars": "unused — MT5 quotes are live from the terminal",
        },
    }


def _prompt(snap: Dict[str, Any]) -> str:
    return (
        "你是 :9001 MT5 模拟盘参谋（Ava Trade demo）。允许联网看宏观/地缘/央行。不是回测，不是 Candidate。\n"
        "每个产品一本账，逻辑不同，不要用同一套 RSI 套所有品种。股票篮子 SHARES 只给建议，系统不会发单。\n"
        "动作：BUY=开多或平空后不再开（若已多则 HOLD）；SELL=开空或平多后不再开（若已空则 HOLD）；"
        "FLAT=只平仓；HOLD=不动。每个产品最多 1 个非 HOLD。默认 HOLD。\n"
        "手数由系统固定 0.01。不要编造终端里没有报价的品种。priced_in=true 的开仓系统会丢掉。\n"
        "只输出一个 JSON，不要前言：\n"
        '{"session":"%s","regime":"一句话","products":[{"id":"XAUUSD","action":"BUY|SELL|FLAT|HOLD","reason":"","source":"宏观|地缘|央行|技术","priced_in":false}],'
        '"avoid":[],"confidence":0-100,"disclaimer":"demo、未回测、不是承诺"}\n'
        "snapshot:\n" % (snap.get("session") or "") + json.dumps(snap, ensure_ascii=False)
    )


def _smoke_brief(snap: Dict[str, Any]) -> Dict[str, Any]:
    names = [{"id": "XAUUSD", "action": "HOLD", "reason": "SMOKE_STUB", "source": "技术", "priced_in": False},
             {"id": "EURUSD", "action": "BUY", "reason": "SMOKE_STUB", "source": "宏观", "priced_in": False},
             {"id": "NOTREAL", "action": "BUY", "reason": "invented", "source": "技术", "priced_in": False},
             {"id": "SHARES", "action": "BUY", "reason": "SMOKE share basket", "source": "宏观", "priced_in": False},
             {"id": "USDJPY", "action": "BUY", "reason": "already priced", "source": "宏观", "priced_in": True}]
    return {"session": snap.get("session"), "regime": "SMOKE_STUB", "products": names, "avoid": [],
            "confidence": 0, "disclaimer": "smoke"}


def grok_call(snap: Dict[str, Any], model_id: str, job_id: str) -> tuple:
    if _smoke():
        return _smoke_brief(snap), {"status": "SMOKE_STUB", "model": model_id}
    catalog, api_id, params = cc.resolve_model(model_id)
    created = cc.create_agent(_prompt(snap), api_id, params, name="TradeMind Hot MT5 Web")
    agent = created.get("agent") or created
    run = created.get("run") or {}
    agent_id = agent.get("id") or created.get("id") or ""
    run_id = run.get("id") or agent.get("latestRunId") or created.get("runId") or ""
    meta = {"model": catalog, "agent_id": agent_id, "run_id": run_id}
    try:
        if not agent_id or not run_id:
            raise RuntimeError("Cursor 没有返回 agent/run id")
        _save_run({"running": True, "job_id": job_id, "stage": "Grok 联网看宏观（MT5）", "agent_id": agent_id,
                   "run_id": run_id, "model": catalog, "started_at": _now().strftime("%Y-%m-%dT%H:%M:%S")})
        done = cc.wait_run(agent_id, run_id, timeout_s=GROK_TIMEOUT_S)
        meta["duration_ms"] = done.get("durationMs")
        if done.get("status") != "FINISHED":
            if str(done.get("status")) == "TIMEOUT":
                try:
                    cc.cancel_run(agent_id, run_id)
                except Exception:
                    pass
            meta["status"] = "GROK_TIMEOUT" if str(done.get("status")) == "TIMEOUT" else str(done.get("status"))
            meta["error"] = str(done.get("error") or done.get("status"))[:300]
            return {}, meta
        text = done.get("result") or ""
        if isinstance(text, dict):
            text = text.get("text") or text.get("result") or json.dumps(text, ensure_ascii=False)
        brief = hot._parse_brief(str(text))
        meta["status"] = "OK" if brief and not brief.get("parse_error") else "PARSE_ERROR"
        return brief, meta
    except Exception as exc:
        log.exception("mt5 grok failed")
        meta["status"] = "FAILED"
        meta["error"] = str(exc)[:300]
        return {}, meta
    finally:
        if agent_id:
            cc.archive_agent(agent_id)


def enforce(brief: Dict[str, Any], snap: Dict[str, Any]) -> Dict[str, Any]:
    known = {p["id"]: p for p in snap.get("products") or []}
    actions: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []
    seen = set()
    for row in brief.get("products") or []:
        pid = str(row.get("id") or "").strip().upper()
        try:
            if pid not in PRODUCTS:
                pid = normalize_symbol(pid)
        except TaskFailedError:
            dropped.append({"id": row.get("id"), "action": row.get("action"), "why": "UNKNOWN_PRODUCT"})
            continue
        if pid not in PRODUCTS:
            dropped.append({"id": row.get("id"), "action": row.get("action"), "why": "UNKNOWN_PRODUCT"})
            continue
        if pid in seen:
            dropped.append({"id": pid, "action": row.get("action"), "why": "DUPLICATE"})
            continue
        seen.add(pid)
        action = str(row.get("action") or "HOLD").strip().upper()
        if action not in ("BUY", "SELL", "FLAT", "HOLD"):
            dropped.append({"id": pid, "action": action, "why": "BAD_ACTION"})
            continue
        if action != "HOLD" and bool(row.get("priced_in")):
            dropped.append({"id": pid, "action": action, "why": "PRICED_IN", "reason": row.get("reason")})
            continue
        prod = known.get(pid) or {"id": pid, "send": PRODUCTS[pid]["send"]}
        pos = prod.get("position")
        side = (pos or {}).get("side")
        if action == "BUY" and side == "BUY":
            dropped.append({"id": pid, "action": action, "why": "ALREADY_LONG"})
            continue
        if action == "SELL" and side == "SELL":
            dropped.append({"id": pid, "action": action, "why": "ALREADY_SHORT"})
            continue
        if action == "FLAT" and not pos:
            dropped.append({"id": pid, "action": action, "why": "FLAT_NO_POSITION"})
            continue
        if action != "HOLD" and pid != "SHARES" and not (prod.get("bid") or prod.get("ask") or prod.get("broker")):
            dropped.append({"id": pid, "action": action, "why": "NO_QUOTE"})
            continue
        send = bool(PRODUCTS[pid]["send"]) and pid != "SHARES"
        if action == "HOLD":
            continue
        actions.append({
            "id": pid, "label": PRODUCTS[pid]["label"], "action": action,
            "kind": "CLOSE" if (action == "FLAT" or (action == "SELL" and side == "BUY") or (action == "BUY" and side == "SELL")) else "OPEN",
            "volume": float(snap.get("volume") or VOLUME),
            "broker": prod.get("broker") or "",
            "bid": prod.get("bid"), "ask": prod.get("ask"),
            "reason": row.get("reason") or "", "source": row.get("source") or "",
            "send": send, "position": pos,
        })
    return {
        "regime": brief.get("regime") or "",
        "actions": actions,
        "dropped": dropped,
        "avoid": brief.get("avoid") or [],
        "confidence": brief.get("confidence"),
        "disclaimer": brief.get("disclaimer") or "demo，不是 Candidate，不是承诺。",
    }


def _send_demo(logical: str, side: str, volume: float) -> Dict[str, Any]:
    from app.service.mt5_service import send_demo_order
    return send_demo_order(logical, side, volume=volume)


def execute(plan: Dict[str, Any], send_fn: Optional[Callable] = None) -> Dict[str, Any]:
    """Apply actions. SHARES/smoke stay paper.

    Demo order_send requires want_send() which now also needs TRADEMIND_HOT_GROK_SEND=1.
    Grok BUY/SELL is not a research Candidate. Phase 2 research must not call this path.
    """
    probe = (plan.get("snapshot") or {}).get("probe") or {}
    mode = probe.get("account_mode")
    filled: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    fn = send_fn or _send_demo
    can = want_send() and mode == "demo"
    if mode == "live":
        can = False
    for a in plan.get("actions") or []:
        rec = {"id": a["id"], "action": a["action"], "kind": a.get("kind"), "volume": a.get("volume")}
        if not a.get("send"):
            rec["status"] = "PAPER_ONLY"
            rec["why"] = "SHARES_NO_SEND" if a["id"] == "SHARES" else "SEND_OFF"
            ev = _record_fill(plan, a, True, note="MT5 paper %s" % a["id"])
            rec["event_id"] = ev.get("id")
            rec["price"] = ev.get("price")
            filled.append(rec)
            continue
        if mode == "live":
            rec["status"] = "BLOCKED_LIVE"
            skipped.append({**rec, "why": "LIVE_ACCOUNT"})
            continue
        if not can:
            rec["status"] = "PAPER_ONLY"
            rec["why"] = "SEND_DISABLED"
            ev = _record_fill(plan, a, True, note="MT5 paper (send off) %s" % a["id"])
            rec["event_id"] = ev.get("id")
            rec["price"] = ev.get("price")
            filled.append(rec)
            continue
        side = "SELL" if a["action"] in ("SELL", "FLAT") and a.get("kind") == "CLOSE" and (a.get("position") or {}).get("side") == "BUY" else (
            "BUY" if a["action"] in ("BUY", "FLAT") and a.get("kind") == "CLOSE" and (a.get("position") or {}).get("side") == "SELL" else a["action"]
        )
        if a["action"] == "FLAT":
            side = "SELL" if (a.get("position") or {}).get("side") == "BUY" else "BUY"
        elif a.get("kind") == "CLOSE":
            side = "SELL" if (a.get("position") or {}).get("side") == "BUY" else "BUY"
        elif a["action"] in ("BUY", "SELL"):
            side = a["action"]
        try:
            sent = fn(a["id"], side, float(a.get("volume") or VOLUME))
            rec["status"] = "SENT" if sent.get("sent") else "NOT_SENT"
            rec["ticket"] = sent.get("ticket") or ""
            rec["reason_send"] = sent.get("reason")
            rec["price"] = sent.get("price")
            ev = _record_fill(plan, a, not sent.get("sent"), sent, note="MT5 demo %s" % a["id"])
            rec["event_id"] = ev.get("id")
            filled.append(rec)
        except Exception as exc:
            rec["status"] = "FAILED"
            rec["why"] = str(exc)[:200]
            skipped.append(rec)
    return {"filled": filled, "skipped": skipped, "sent_any": any(x.get("status") == "SENT" for x in filled)}


def _save_run(st: Dict[str, Any]) -> None:
    _dump(RUN_PATH, st)


def run_state() -> Dict[str, Any]:
    return _load(RUN_PATH, None) or {"running": False}


def _sessions_log() -> Dict[str, Any]:
    return _load(SESSIONS_PATH, None) or {"days": {}}


def _record_session(day: str, session: str, rec: Dict[str, Any]) -> None:
    sl = _sessions_log()
    day_d = sl.setdefault("days", {}).setdefault(day, {})
    prev = day_d.get(session)
    if prev and prev.get("pipeline") == "RAN" and rec.get("pipeline") != "RAN":
        rec = prev
    day_d[session] = rec
    _dump(SESSIONS_PATH, sl)


def sessions_today(today: Optional[str] = None) -> Dict[str, Any]:
    today = today or _now().date().isoformat()
    day = ((_sessions_log().get("days") or {}).get(today) or {})
    n_calls = sum(1 for s in day.values() if s.get("pipeline") == "RAN")
    now_hm = _now().strftime("%H:%M")
    nxt = None
    for s in ("asia", "ny"):
        if SESSION_TIMES[s] > now_hm and s not in day:
            nxt = {"session": s, "time": SESSION_TIMES[s], "label": SESSION_LABEL[s]}
            break
    return {"date": today, "sessions": day, "n_calls_today": n_calls, "max_calls_per_day": MAX_GROK_CALLS_PER_DAY,
            "next": nxt, "schedule": SESSION_TIMES, "recent": _sessions_recent(10),
            "token_note": "MT5 每天最多 2 次 Grok（08:30 / 20:30），报价走终端实时，不依赖 :9000 晚上更新。"}


def _sessions_recent(n: int = 10) -> List[Dict[str, Any]]:
    sl = (_sessions_log().get("days") or {})
    rows: List[Dict[str, Any]] = []
    for day in sorted(sl.keys(), reverse=True)[:n]:
        rec = sl[day] or {}
        item: Dict[str, Any] = {"date": day}
        for k in ("asia", "ny"):
            r = rec.get(k) or {}
            item[k] = r.get("pipeline") or ""
        rows.append(item)
    return rows


def run_session(session: str, job_id: str, model_id: str = "",
                snap_fn: Optional[Callable] = None, grok_fn: Optional[Callable] = None,
                send_fn: Optional[Callable] = None) -> Dict[str, Any]:
    if session not in SESSIONS:
        raise ValueError("session 必须是 asia / ny / settle")
    today = _now().date().isoformat()
    weekday = _now().weekday()
    st: Dict[str, Any] = {"running": True, "job_id": job_id, "session": session, "session_label": SESSION_LABEL.get(session),
                          "stage": "探测 AVA MT5", "started_at": _now().strftime("%Y-%m-%dT%H:%M:%S"), "date": today,
                          "profile": PROFILE, "candidate": False}
    _save_run(st)
    if session == "settle":
        st["pipeline"] = "SETTLE_ONLY"
        st["running"] = False
        st["finished_at"] = _now().strftime("%Y-%m-%dT%H:%M:%S")
        _save_run(st)
        _record_session(today, session, st)
        return st
    if weekday >= 5:
        st["pipeline"] = "SKIPPED_WEEKEND"
        st["note"] = "周末外汇休市，不调 Grok、不发单。"
    elif plan_path(today, session).is_file():
        st["pipeline"] = "SKIPPED_ALREADY_PLANNED"
        st["note"] = "今天的 %s 已跑过。" % SESSION_LABEL.get(session)
    elif sessions_today(today)["n_calls_today"] >= MAX_GROK_CALLS_PER_DAY:
        st["pipeline"] = "SKIPPED_CALL_BUDGET"
    else:
        snap = (snap_fn or snapshot)(session)
        st["probe"] = (snap.get("probe") or {})
        if not snap.get("probe", {}).get("connected") and not _smoke():
            st["pipeline"] = "SKIPPED_MT5_OFFLINE"
            st["note"] = "MT5 终端没连上（Ava Trade）。打开终端后再跑。"
        else:
            st["stage"] = "%s：Grok 分品种诊盘" % SESSION_LABEL.get(session)
            _save_run(st)
            brief, meta = (grok_fn or grok_call)(snap, model_id, job_id)
            enforced = enforce(brief or {}, snap)
            plan = {
                "profile": PROFILE, "candidate": False, "session": session, "session_label": SESSION_LABEL.get(session),
                "date": today, "generated_at": _now().strftime("%Y-%m-%dT%H:%M:%S"), "job_id": job_id,
                "model": meta.get("model") or model_id, "layer": meta, "snapshot": {"probe": snap.get("probe"),
                "products": [{"id": p["id"], "broker": p.get("broker"), "bid": p.get("bid"), "ask": p.get("ask"),
                              "position": p.get("position")} for p in snap.get("products") or []]},
                "regime": enforced["regime"], "actions": enforced["actions"], "dropped": enforced["dropped"],
                "avoid": enforced["avoid"], "confidence": enforced["confidence"],
                "disclaimer": enforced["disclaimer"],
                "honesty": ["不是 Candidate。D1 家族已证伪；这是 demo 观察台，不是新边。",
                            "股票篮子不自动发单。实盘账户拒绝。"],
            }
            exe = execute(plan, send_fn=send_fn)
            plan["fills"] = exe
            _dump(plan_path(today, session), plan)
            _dump(LAST_PATH, plan)
            st["pipeline"] = "RAN"
            st["plan"] = {"session": session, "n_actions": len(plan["actions"]), "n_dropped": len(plan["dropped"]),
                          "sent_any": exe.get("sent_any"), "regime": plan.get("regime")}
            st["fills"] = exe
    st["running"] = False
    st["stage"] = "完成" if st.get("pipeline") != "FAILED" else "失败"
    st["finished_at"] = _now().strftime("%Y-%m-%dT%H:%M:%S")
    _save_run(st)
    _record_session(today, session, {k: st.get(k) for k in ("job_id", "pipeline", "note", "plan", "fills", "started_at", "finished_at")})
    return st


def start_session(session: str, model_id: str = "") -> Dict[str, Any]:
    global _thread
    if session not in SESSIONS:
        raise ValueError("session 必须是 asia / ny / settle")
    with _lock:
        cur = run_state()
        if cur.get("running") and _thread is not None and _thread.is_alive():
            return cur
        job_id = uuid.uuid4().hex[:10]
        catalog = model_id
        if not _smoke() and session != "settle":
            catalog, _a, _p = cc.resolve_model(model_id)
        t = threading.Thread(target=run_session, args=(session, job_id, catalog), daemon=True)
        _thread = t
        _save_run({"running": True, "job_id": job_id, "session": session, "stage": "已提交",
                   "started_at": _now().strftime("%Y-%m-%dT%H:%M:%S")})
        t.start()
    return run_state()


def gold_follow(refresh: bool = False) -> Dict[str, Any]:
    """Read-only V4 stance for the MT5 page. Never appended to Grok prompts."""
    try:
        from research_engine.hot_mt5_gold_follow.stance import read_status, write_status
        if refresh or read_status() is None:
            return write_status()
        return read_status() or {"ok": False, "candidate": False, "feeds_grok": False}
    except Exception as exc:
        log.exception("gold_follow status failed")
        return {"ok": False, "candidate": False, "deploy": False, "feeds_grok": False,
                "order_send": False, "error": str(exc)}


def view() -> Dict[str, Any]:
    probe = probe_mt5() if not _smoke() else {"account_mode": "demo", "connected": True, "reason": "SMOKE_STUB"}
    return {
        "profile": PROFILE, "candidate": False, "orders_sent": False,
        "settings": settings(), "want_send": want_send(),
        "probe": probe, "last": _load(LAST_PATH, None), "run": run_state(),
        "sessions": sessions_today(), "journal": _journal(),
        "gold_follow": gold_follow(False),
        "products": [{"id": k, "label": v["label"], "logic": v["logic"], "send": v["send"]} for k, v in PRODUCTS.items()],
        "honesty": [
            "报价走 Ava MT5 终端，和 :9000 晚上更新的 A 股日线不是一路，不会抢同一份数据。",
            "每个品种一本逻辑；股票篮子只建议、不自动发单（V30 成本死）。",
            "每天最多 2 次 Grok（08:30 / 20:30），每品种每场最多 1 笔。Grok 不是 Candidate，默认不发单（TRADEMIND_HOT_GROK_SEND=0）。",
            "实盘账户拒绝发单。demo_send 关掉就只记账。LLM→BUY→MT5 不是策略。",
            "黄金 V4 跟盘只展示冻结日线状态，不写进 Grok，不发单。LEGACY_FROZEN。",
        ],
    }
