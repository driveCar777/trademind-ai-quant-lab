"""High-risk hot desk. Isolated journal. Does not touch paper_ops JOURNAL or daily.py."""
from __future__ import annotations

import csv
import json
import logging
import os
import re
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.service import paper_ops as po
from app.service import cursor_cloud as cc

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_ROOT))

HOT = po.LIVE / "paper_hot"
JOURNAL = HOT / "JOURNAL.json"
BRIEF_PATH = HOT / "LAST_BRIEF.json"
RUN_PATH = HOT / "BRIEF_RUN.json"
B1_PATH = HOT / "B1_LEDGER.json"
B1_RUN_PATH = HOT / "B1_RUN.json"
B2_PATH = HOT / "B2_LEDGER.json"
B2_RUN_PATH = HOT / "B2_RUN.json"
B_N5_PATH = HOT / "B_N5_LEDGER.json"
FROZEN_URL = "http://127.0.0.1:9000/paper"
_lock = threading.Lock()
_worker_thread: Optional[threading.Thread] = None
_b1_thread: Optional[threading.Thread] = None
_b2_thread: Optional[threading.Thread] = None
log = logging.getLogger("app.paper_hot")


def _dump(path: Path, obj: Any) -> None:
    """Windows-safe write. os.replace on a watched/polled file often hits WinError 5."""
    HOT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    tmp = path.with_name("%s.%s.%s.tmp" % (path.name, os.getpid(), threading.get_ident()))
    tmp.write_text(text, encoding="utf-8")
    last: Optional[Exception] = None
    for i in range(12):
        try:
            os.replace(str(tmp), str(path))
            return
        except OSError as exc:
            last = exc
            time.sleep(0.05 * (i + 1))
    try:
        path.write_text(text, encoding="utf-8")
        try:
            tmp.unlink()
        except OSError:
            pass
        return
    except OSError as exc:
        last = last or exc
    raise last  # type: ignore[misc]


def _save_run(obj: Dict[str, Any]) -> None:
    try:
        _dump(RUN_PATH, obj)
    except OSError as exc:
        log.warning("BRIEF_RUN write failed: %s", exc)


def _load(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def load_journal() -> Dict[str, Any]:
    j = _load(JOURNAL, None) or {"account": {"base_cash": 0.0}, "events": []}
    j.setdefault("account", {"base_cash": 0.0})
    j.setdefault("events", [])
    return j


# ----------------------------------------------------------------------------- hot account (seeded)
SETTINGS_PATH = HOT / "FUSION_SETTINGS.json"
INITIAL_CAPITAL_DEFAULT = 20000.0


def settings() -> Dict[str, Any]:
    """Hot-desk settings (shared with paper_fusion_fill). initial_capital = paper seed of the :9001 account."""
    s = _load(SETTINGS_PATH, None) or {}
    try:
        cap = float(s.get("initial_capital", INITIAL_CAPITAL_DEFAULT))
    except (TypeError, ValueError):
        cap = INITIAL_CAPITAL_DEFAULT
    return {"auto_fill": bool(s.get("auto_fill", True)), "initial_capital": cap, "updated_at": s.get("updated_at")}


def save_settings(**kw: Any) -> Dict[str, Any]:
    s = _load(SETTINGS_PATH, None) or {}
    for k, v in kw.items():
        if v is not None:
            s[k] = v
    s["updated_at"] = po._now().strftime("%Y-%m-%dT%H:%M:%S")
    _dump(SETTINGS_PATH, s)
    return settings()


def derive_account(journal: Dict[str, Any], days: List[str]) -> Dict[str, Any]:
    """Hot account = initial_capital seed + cash-flow of journal events. Events flagged `seed: true` are the seed
    itself (kept as evidence, not counted again). Paper only; reuses paper_ops.derive_account read-only."""
    cap = settings()["initial_capital"]
    events = journal.get("events") or []
    seed_events = [e for e in events if e.get("seed")]
    j2 = {"account": {"base_cash": cap}, "events": [e for e in events if not e.get("seed")]}
    acct = po.derive_account(j2, days)
    acct["initial_capital"] = cap
    acct["seed_events"] = [e.get("id") for e in seed_events]
    acct["n_events"] = len(events)
    acct["source"] = "JOURNAL" if events else "SEED"
    acct["overspent"] = round(-float(acct.get("cash") or 0.0), 2) if float(acct.get("cash") or 0.0) < 0 else 0.0
    acct["pnl_vs_initial"] = round(float(acct.get("equity") or 0.0) - cap - float(acct.get("deposits_total") or 0.0)
                                   + float(acct.get("withdrawals_total") or 0.0), 2)
    eq = float(acct.get("equity") or 0.0)
    mv = float(acct.get("market_value") or 0.0)
    acct["util_pct"] = round(100.0 * mv / eq, 1) if eq > 0 else 0.0
    return acct


def ticket_snapshot() -> Dict[str, Any]:
    """Account + clocks at write time. Small enough to pin on every journal event."""
    try:
        days = po._days()
        status = po._load(po.STATUS, {}) or {}
        fresh = po.freshness(days, status, with_gap=False)
        acc = derive_account(load_journal(), days)
    except Exception:
        return {"error": "snapshot_failed"}
    pos = []
    for p in (acc.get("positions") or [])[:20]:
        pos.append({
            "symbol": p.get("symbol"), "lots": p.get("lots"), "avg_price": p.get("avg_price"),
            "buy_date": p.get("buy_date"), "sellable_today": p.get("sellable_today"),
        })
    return {
        "today": fresh.get("today"),
        "asof_session": fresh.get("asof_session"),
        "cash": acc.get("cash"),
        "equity": acc.get("equity"),
        "market_value": acc.get("market_value"),
        "pnl_vs_initial": acc.get("pnl_vs_initial"),
        "n_positions": len(acc.get("positions") or []),
        "positions": pos,
    }


def add_event(body: Dict[str, Any], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """`extra` = audit fields kept verbatim on the event (e.g. auto=True, plan_id) that _make_event would drop."""
    extra = dict(extra or {})
    if "snapshot" not in extra:
        extra["snapshot"] = ticket_snapshot()
    ev = po._make_event(body)
    for k, v in extra.items():
        if k not in ev:
            ev[k] = v
    j = load_journal()
    j["events"].append(ev)
    j["events"].sort(key=lambda e: (e.get("date") or "", e.get("ts") or ""))
    _dump(JOURNAL, j)
    return ev


def update_event(event_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    j = load_journal()
    idx = next((i for i, e in enumerate(j["events"]) if e.get("id") == event_id), None)
    if idx is None:
        raise KeyError(event_id)
    old = j["events"][idx]
    merged = dict(old)
    for k, v in (body or {}).items():
        if k in ("id", "ts"):
            continue
        if v is not None:
            merged[k] = v
    reestimate = "fee" not in (body or {}) or body.get("fee") is None
    if reestimate:
        merged.pop("fee", None)
    ev = po._make_event(merged, keep_id=old["id"], keep_ts=old.get("ts"), reestimate_fee=reestimate)
    j["events"][idx] = ev
    j["events"].sort(key=lambda e: (e.get("date") or "", e.get("ts") or ""))
    _dump(JOURNAL, j)
    return ev


def delete_event(event_id: str) -> None:
    j = load_journal()
    before = len(j["events"])
    j["events"] = [e for e in j["events"] if e.get("id") != event_id]
    if len(j["events"]) == before:
        raise KeyError(event_id)
    _dump(JOURNAL, j)


def _sellable(buy_date: Optional[str], fresh: Dict[str, Any]) -> bool:
    today = fresh.get("today") or ""
    if not buy_date or not today:
        return False
    return bool(fresh.get("today_is_trading_day")) and buy_date < today


def _ml1_ref() -> Dict[str, Any]:
    sigs = po.SIGNALS
    latest = None
    if sigs.is_dir():
        cands = sorted([p for p in sigs.glob("SHORTLIST_SHADOW_*.json")] + [p for p in sigs.glob("SHORTLIST_20*.json")])
        if cands:
            latest = cands[-1]
    if latest is None:
        return {"signal_date": None, "names": [], "note": "还没有主线短名单"}
    sl = _load(latest, {}) or {}
    sd = sl.get("signal_date") or latest.stem.replace("SHORTLIST_SHADOW_", "").replace("SHORTLIST_", "")
    names = []
    for n in (sl.get("names") or [])[:10]:
        names.append({
            "rank": n.get("rank"), "symbol": n.get("symbol"), "name": n.get("name") or "",
            "score": n.get("score"), "last_close": n.get("last_close"),
            "lots_100_est": n.get("lots_100_est"),
        })
    return {"signal_date": sd, "names": names, "note": "主线 V26.8 短名单，账本3 候选池，不是必须买"}


def _parse_brief(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    block = text
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        block = m.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            block = text[start:end + 1]
    try:
        obj = json.loads(block)
    except ValueError:
        return {"raw": text[:4000], "parse_error": True}
    return obj if isinstance(obj, dict) else {"raw": text[:4000], "parse_error": True}


def _thread_alive() -> bool:
    t = _worker_thread
    return t is not None and t.is_alive()


def _run_age_s(cur: Dict[str, Any]) -> float:
    ts = str(cur.get("started_at") or "")
    try:
        started = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return 1e9
    return max(0.0, (po._now() - started).total_seconds())


def _run_state() -> Dict[str, Any]:
    cur = _load(RUN_PATH, {}) or {"running": False}
    if cur.get("running") and not _thread_alive() and _run_age_s(cur) > 5:
        cur["running"] = False
        cur["stage"] = "失败"
        if not cur.get("error"):
            cur["error"] = "后台线程已退出（写状态文件失败或进程重启）。可以再点一次出简报。"
        _save_run(cur)
    return cur


def _cursor_models() -> List[Dict[str, str]]:
    if not cc.key_present():
        return []
    try:
        return cc.list_models()
    except Exception as exc:
        return [{"id": "", "label": "目录暂时拉不到：%s" % str(exc)[:80]}]


def _plan(brief: Dict[str, Any], account: Dict[str, Any], fresh: Dict[str, Any]) -> Dict[str, Any]:
    warnings = [
        "纸面诊股台。工作日自动诊股、自动记账。不是 Candidate。",
        "A 股普通账户 T+1：今天买的股票今天不能卖。系统不发 A 股单。",
    ]
    if not brief:
        return {
            "headline": "还没有简报（日常看自动诊股，不用点这里）",
            "sub": "名单来自 :9000 的 ML1。这里自动诊股并记账。",
            "exposure_pct": None, "themes": [], "recs": [], "warnings": warnings,
        }
    recs = []
    held = {p["symbol"]: p for p in account.get("positions") or []}
    for n in brief.get("names") or []:
        sym = n.get("symbol") or ""
        if sym and "." not in str(sym):
            s = str(sym)
            sym = ("sh." if s.startswith("6") else "sz.") + s
        pos = held.get(sym)
        recs.append({
            "symbol": sym, "name": n.get("name") or (pos or {}).get("name") or "",
            "action": n.get("action") or "HOLD", "horizon": n.get("horizon") or "",
            "tag": n.get("tag") or "", "reason": n.get("reason") or "",
            "lots_hint": n.get("lots_hint"),
            "held": bool(pos), "sellable_today": _sellable((pos or {}).get("buy_date"), fresh) if pos else False,
            "mark_price": (pos or {}).get("mark_price"),
        })
    expo = brief.get("exposure_pct")
    try:
        expo = max(0, min(100, int(expo))) if expo is not None else None
    except (TypeError, ValueError):
        expo = None
    return {
        "headline": brief.get("regime") or "已有简报，自己决定听不听",
        "sub": brief.get("disclaimer") or "建议不是指令。登记成交后才进本台账本。",
        "exposure_pct": expo, "themes": brief.get("themes") or [], "recs": recs,
        "warnings": warnings + list(brief.get("avoid") or []),
        "asof": brief.get("asof"),
    }


def _bar_closes(symbol: str) -> List[tuple]:
    """All (date, close) from live/bars — same files derive_account already uses. Not a new price source."""
    p = po.BARS / ("%s.csv" % symbol)
    if not p.is_file():
        return []
    out: List[tuple] = []
    try:
        with open(p, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                d = r.get("date") or ""
                try:
                    c = float(r.get("close") or 0)
                except (TypeError, ValueError):
                    continue
                if d and c > 0:
                    out.append((d, c))
    except OSError:
        return []
    return out


def _close_asof(series: List[tuple], asof: str) -> Optional[float]:
    if not series or not asof:
        return None
    px = None
    last_d = ""
    for d, c in series:
        if d <= asof and d >= last_d:
            px = c
            last_d = d
    return px


def _norm_sym(sym: str) -> str:
    s = (sym or "").strip()
    if not s:
        return ""
    if "." in s:
        return s
    return ("sh." if s.startswith("6") else "sz.") + s


def symbol_curve(symbol: str) -> Dict[str, Any]:
    """One name: live/bars close + invested/pnl if the hot journal holds it. SPEC §29.13."""
    sym = _norm_sym(symbol)
    days = po._days()
    status = po._load(po.STATUS, {}) or {}
    fresh = po.freshness(days, status, with_gap=False)
    asof = (fresh or {}).get("asof_session") or (fresh or {}).get("today") or ""
    account = derive_account(load_journal(), days)
    pos = None
    for p in account.get("positions") or []:
        if _norm_sym(p.get("symbol") or "") == sym:
            pos = p
            break
    bars = _bar_closes(sym)
    if asof:
        bars = [(d, c) for d, c in bars if d <= asof]
    bars = bars[-40:]
    lot = getattr(po, "LOT", 100)
    series: List[Dict[str, Any]] = []
    for d, c in bars:
        pt: Dict[str, Any] = {"date": d, "close": round(float(c), 4)}
        if pos and (pos.get("buy_date") or "") and d >= pos["buy_date"]:
            lots = float(pos.get("lots") or 0)
            cost = float(pos.get("cost_in") or 0)
            if not cost and pos.get("avg_price"):
                cost = float(pos["avg_price"]) * lots * lot
            pt["invested"] = round(cost, 2)
            pt["pnl"] = round(float(c) * lots * lot - cost, 2)
        series.append(pt)
    return {
        "symbol": sym,
        "name": (pos or {}).get("name") or "",
        "held": bool(pos),
        "series": series,
    }


def _curve_point(date: str, cash: float, mv: float, realized: float, cost_left: float,
                 cap: float, deposits: float, withdrawals: float) -> Dict[str, Any]:
    equity = cash + mv
    unreal = mv - cost_left
    pnl = equity - cap - deposits + withdrawals
    util = (100.0 * mv / equity) if equity > 0 else 0.0
    return {
        "date": date,
        "equity": round(equity, 2),
        "cash": round(cash, 2),
        "market_value": round(mv, 2),
        "realized": round(realized, 2),
        "unrealized": round(unreal, 2),
        "pnl": round(pnl, 2),
        "util_pct": round(util, 1),
    }


def equity_curve(journal: Dict[str, Any], days: List[str], fresh: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Paper equity from seed + journal, marked with live/bars close on/before that day. SPEC §29.13."""
    cap = settings()["initial_capital"]
    events = [e for e in (journal.get("events") or []) if not e.get("seed")]
    asof = (fresh or {}).get("asof_session") or (fresh or {}).get("today") or ""
    start = None
    for e in events:
        d = e.get("date") or ""
        if d and (start is None or d < start):
            start = d
    if not start:
        d0 = asof or (fresh or {}).get("today") or "seed"
        return [_curve_point(d0, cap, 0.0, 0.0, 0.0, cap, 0.0, 0.0)]
    day_list = [d for d in (days or []) if d >= start and (not asof or d <= asof)]
    if not day_list:
        day_list = sorted(set(e.get("date") for e in events if e.get("date")))
    if asof and asof not in day_list and (not days or asof >= start):
        day_list = list(day_list) + [asof]
    prev = [d for d in (days or []) if d < start]
    if prev and (not day_list or prev[-1] != day_list[0]):
        day_list = [prev[-1]] + list(day_list)
    if len(day_list) > 60:
        day_list = day_list[-60:]
    cache: Dict[str, List[tuple]] = {}
    lot = getattr(po, "LOT", 100)
    out: List[Dict[str, Any]] = []
    for day in day_list:
        cash = cap
        deposits = 0.0
        withdrawals = 0.0
        realized = 0.0
        pos: Dict[str, Dict[str, float]] = {}
        for e in events:
            if (e.get("date") or "") > day:
                continue
            t = e.get("type")
            if t == "DEPOSIT":
                amt = float(e.get("amount") or 0)
                cash += amt
                deposits += amt
            elif t == "WITHDRAW":
                amt = float(e.get("amount") or 0)
                cash -= amt
                withdrawals += amt
            elif t == "BUY":
                cash -= float(e.get("amount") or 0) + float(e.get("fee") or 0)
                p = pos.setdefault(e.get("symbol") or "", {"lots": 0.0, "cost": 0.0})
                p["lots"] += float(e.get("lots") or 0)
                p["cost"] += float(e.get("amount") or 0) + float(e.get("fee") or 0)
            elif t == "SELL":
                proceeds = float(e.get("amount") or 0) - float(e.get("fee") or 0)
                cash += proceeds
                p = pos.get(e.get("symbol") or "")
                ev_lots = float(e.get("lots") or 0)
                if p and p["lots"] > 0:
                    take = min(ev_lots, p["lots"]) if ev_lots > 0 else p["lots"]
                    avg = p["cost"] / p["lots"] if p["lots"] else 0.0
                    cost_taken = avg * take
                    part = (take / ev_lots) if ev_lots > 0 else 1.0
                    realized += proceeds * part - cost_taken
                    p["lots"] -= take
                    p["cost"] -= cost_taken
        mv = 0.0
        cost_left = 0.0
        for sym, p in pos.items():
            if not sym or p["lots"] <= 0:
                continue
            cost_left += p["cost"]
            if sym not in cache:
                cache[sym] = _bar_closes(sym)
            px = _close_asof(cache[sym], day)
            if px:
                mv += px * p["lots"] * lot
        out.append(_curve_point(day, cash, mv, realized, cost_left, cap, deposits, withdrawals))
    return out


def desk() -> Dict[str, Any]:
    days = po._days()
    status = po._load(po.STATUS, {}) or {}
    fresh = po.freshness(days, status, with_gap=False)
    journal = load_journal()
    account = derive_account(journal, days)
    for p in account.get("positions") or []:
        p["sellable_today"] = _sellable(p.get("buy_date"), fresh)
    brief = _load(BRIEF_PATH, None) or {}
    models = []
    err = None
    if cc.key_present() and not os.environ.get("TRADEMIND_HOT_SMOKE"):
        try:
            models = cc.list_models()
        except Exception as exc:
            err = str(exc)[:200]
    selected = cc.preferred_model(models)
    run = _run_state()
    return {
        "profile": "HOT_V3", "frozen_url": FROZEN_URL, "risk": "HIGH",
        "fusion_url": "/api/v1/hot/fusion",
        "t_plus": "普通账户股票 T+1。当天买的不能当天卖。做T = 底仓或隔日回转。",
        "freshness": fresh, "account": account,
        "equity_curve": equity_curve(journal, days, fresh),
        "brief": brief or None, "brief_run": run,
        "cursor": {"key_present": cc.key_present(), "models": models, "selected": selected, "error": err},
        "ml1_ref": _ml1_ref(), "plan": _plan(brief, account, fresh),
        "books": _books_summary(),
        "book1_run": _load(B1_RUN_PATH, {}) or {},
        "book2_run": _load(B2_RUN_PATH, {}) or {},
        "journal_events": list(reversed(journal.get("events") or []))[:50],
        "orders_sent": False,
        "faq": FAQ,
    }


def _brief_snapshot() -> Dict[str, Any]:
    days = po._days()
    status = po._load(po.STATUS, {}) or {}
    fresh = po.freshness(days, status, with_gap=False)
    journal = load_journal()
    account = derive_account(journal, days)
    for p in account.get("positions") or []:
        p["sellable_today"] = _sellable(p.get("buy_date"), fresh)
    return {
        "today": fresh.get("today"),
        "asof": fresh.get("asof_session"),
        "account": {
            "cash": account.get("cash"), "equity": account.get("equity"),
            "positions": [{"symbol": p.get("symbol"), "name": p.get("name"), "lots": p.get("lots"),
                           "avg_price": p.get("avg_price"), "mark_price": p.get("mark_price"),
                           "unrealized": p.get("unrealized"), "buy_date": p.get("buy_date"),
                           "sellable_today": p.get("sellable_today")} for p in account.get("positions") or []],
        },
        "ml1_pool": _ml1_ref(),
        "constraints": {
            "market": "CN_A_SHARE", "account": "普通账户 T+1 股票，无量化权限，本金约 2 万级",
            "fill": "next_open", "t_plus_one": True,
            "goal": "在 ML1 短名单池上，可联网补充或替换，给出下一交易日开盘要买/要卖的名单",
            "not_a_backtest": True, "not_a_promise": True,
        },
    }


def _brief_prompt(model_id: str) -> str:
    snap = _brief_snapshot()
    return (
        "你是账本3纸面参谋。允许联网，允许使用股票代码、新闻、板块。这不是回测。\n"
        "候选池优先用 snapshot.ml1_pool（冻结 ML1 短名单）。可以反对它、只留重叠、或另推最多 8 只。\n"
        "成交假设 = 下一交易日开盘价。普通账户 T+1：今天买的今天不能卖。\n"
        "只输出一个 JSON 对象，不要前言。字段：\n"
        '{"asof":"YYYY-MM-DD","exposure_pct":0-100,"regime":"一句话市场判断",'
        '"themes":[{"tag":"板块或事件","note":"为何热"}],'
        '"names":[{"symbol":"600000或sh.600000","name":"","action":"BUY|SELL|HOLD|T_BUY|T_SELL",'
        '"horizon":"next_open","tag":"龙头|跟风|回避","reason":"","lots_hint":1}],'
        '"avoid":["不要碰的理由"],"disclaimer":"账本3纸面、未回测、不是承诺"}\n'
        "names 最多 8 只。symbol 用 A 股 6 位代码。\n"
        "snapshot:\n" + json.dumps(snap, ensure_ascii=False)
    )


def _worker(model_id: str, job_id: str) -> None:
    agent_id = run_id = ""
    started = po._now().strftime("%Y-%m-%dT%H:%M:%S")
    try:
        catalog, api_id, params = cc.resolve_model(model_id)
        _save_run({"running": True, "job_id": job_id, "model": catalog, "stage": "正在提交 Cursor",
                   "started_at": started})
        created = cc.create_agent(_brief_prompt(catalog), api_id, params)
        agent = created.get("agent") or created
        run = created.get("run") or {}
        agent_id = agent.get("id") or created.get("id") or ""
        run_id = run.get("id") or agent.get("latestRunId") or created.get("runId") or ""
        _save_run({"running": True, "job_id": job_id, "agent_id": agent_id, "run_id": run_id,
                   "model": catalog, "stage": "Cursor 正在联网写简报", "started_at": started})
        if not agent_id or not run_id:
            raise RuntimeError("Cursor 没有返回 agent/run id：%s" % str(created)[:240])
        done = cc.wait_run(agent_id, run_id)
        text = done.get("result") or ""
        brief = _parse_brief(text)
        brief["_meta"] = {"model": catalog, "api_id": api_id, "agent_id": agent_id, "run_id": run_id,
                          "status": done.get("status"), "duration_ms": done.get("durationMs"),
                          "ts": po._now().strftime("%Y-%m-%dT%H:%M:%S")}
        if done.get("status") != "FINISHED":
            raise RuntimeError(done.get("error") or ("Cursor run " + str(done.get("status"))))
        _dump(BRIEF_PATH, brief)
        _save_run({"running": False, "job_id": job_id, "agent_id": agent_id, "run_id": run_id,
                   "model": catalog, "stage": "完成",
                   "finished_at": po._now().strftime("%Y-%m-%dT%H:%M:%S")})
    except Exception as exc:
        log.exception("hot brief worker failed")
        _save_run({"running": False, "job_id": job_id, "agent_id": agent_id, "run_id": run_id,
                   "model": model_id, "stage": "失败", "error": str(exc)[:400]})
    finally:
        if agent_id:
            cc.archive_agent(agent_id)


def start_brief(model_id: str = "") -> Dict[str, Any]:
    global _worker_thread
    if not cc.key_present():
        raise RuntimeError("没有 Cursor 密钥。应在 D:\\Cursor\\APIKey.txt")
    try:
        catalog, _api, _params = cc.resolve_model(model_id)
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(str(exc)[:300]) from exc
    with _lock:
        cur = _run_state()
        if cur.get("running") and _thread_alive():
            return cur
        job_id = uuid.uuid4().hex[:10]
        started = po._now().strftime("%Y-%m-%dT%H:%M:%S")
        t = threading.Thread(target=_worker, args=(catalog, job_id), daemon=True)
        _worker_thread = t
        _save_run({"running": True, "job_id": job_id, "model": catalog,
                   "stage": "已提交，正在组简报", "started_at": started})
        t.start()
    return _run_state()


def stop_brief() -> Dict[str, Any]:
    cur = _run_state()
    if cur.get("agent_id") and cur.get("run_id") and cur.get("running"):
        try:
            cc.cancel_run(cur["agent_id"], cur["run_id"])
        except Exception as exc:
            cur["error"] = str(exc)[:200]
    cur["running"] = False
    cur["stage"] = "已停止"
    _save_run(cur)
    return cur


def brief_status() -> Dict[str, Any]:
    return _run_state()


def _slim_book(obj: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not obj:
        return {"ready": False}
    daily = obj.get("daily") or []
    return {
        "ready": True, "profile": obj.get("profile"), "candidate": False,
        "twr": obj.get("twr"), "frozen_twr": obj.get("frozen_twr"), "aligned": obj.get("aligned"),
        "cagr": obj.get("cagr"), "equity_end": obj.get("equity_end"),
        "n_periods": obj.get("n_periods"), "note": obj.get("note"),
        "n_timeout": obj.get("n_timeout"), "total_expected": obj.get("total_expected"), "complete": obj.get("complete"),
        "window": obj.get("window"), "start": obj.get("start"), "end": obj.get("end"),
        "daily_tail": daily[-40:],
        "periods": [{k: v for k, v in p.items() if k != "names"} for p in (obj.get("periods") or [])[-12:]],
    }


def _books_summary() -> Dict[str, Any]:
    n5_raw = _load(B_N5_PATH, None)
    n5 = _slim_book(n5_raw)
    if n5_raw:
        n5.update({"label": n5_raw.get("label"), "viable_historical": n5_raw.get("viable_historical"),
                   "b1_twr": n5_raw.get("b1_twr"), "twr_minus_b1": n5_raw.get("twr_minus_b1"),
                   "daily_maxdd": n5_raw.get("daily_maxdd"), "periods_beaten_b1": n5_raw.get("periods_beaten_b1"),
                   "periods_compared": n5_raw.get("periods_compared"), "mean_excess_vs_b1": n5_raw.get("mean_excess_vs_b1"),
                   "t_excess_vs_b1": n5_raw.get("t_excess_vs_b1"), "n_target": n5_raw.get("n_target"), "read_once": True,
                   "maxdd_daily": n5_raw.get("maxdd_daily"), "beat_book1_periods": n5_raw.get("beat_book1_periods")})
    return {
        "b1": _slim_book(_load(B1_PATH, None)),
        "b2": _slim_book(_load(B2_PATH, None)),
        "b3": {"ready": True, "profile": "HOT_B3_WEB_PAPER", "candidate": False,
               "note": "联网纸面。不回测。成交按下一开盘登记。"},
        "n5": n5,
    }


def start_book1() -> Dict[str, Any]:
    global _b1_thread
    if _b1_thread is not None and _b1_thread.is_alive():
        return _load(B1_RUN_PATH, {}) or {"running": True, "stage": "账本1 正在回放"}
    def work():
        try:
            from research_engine.hot_three_books import book1
            book1.build()
            _dump(B1_RUN_PATH, {"running": False, "stage": "完成"})
        except Exception as exc:
            log.exception("book1 failed")
            _dump(B1_RUN_PATH, {"running": False, "stage": "失败", "error": str(exc)[:400]})
    _dump(B1_RUN_PATH, {"running": True, "stage": "账本1 已提交"})
    _b1_thread = threading.Thread(target=work, daemon=True)
    _b1_thread.start()
    return _load(B1_RUN_PATH, {}) or {"running": True}


def start_book2(limit: Optional[int] = None, tail: Optional[int] = None) -> Dict[str, Any]:
    global _b2_thread
    if _b2_thread is not None and _b2_thread.is_alive():
        return _load(B2_RUN_PATH, {}) or {"running": True, "stage": "账本2 进行中"}
    def work():
        try:
            from research_engine.hot_three_books import book2
            book2.run_window(limit=limit, tail=tail, resume=True)
        except Exception as exc:
            log.exception("book2 failed")
            _dump(B2_RUN_PATH, {"running": False, "stage": "失败", "error": str(exc)[:400]})
    _dump(B2_RUN_PATH, {"running": True, "stage": "账本2 已提交", "limit": limit, "tail": tail})
    _b2_thread = threading.Thread(target=work, daemon=True)
    _b2_thread.start()
    return _load(B2_RUN_PATH, {}) or {"running": True}


def stop_book2() -> Dict[str, Any]:
    cur = _load(B2_RUN_PATH, {}) or {}
    cur["stop"] = True
    cur["running"] = False
    cur["stage"] = "已停止"
    _dump(B2_RUN_PATH, cur)
    return cur


FAQ = [
    {"q": "这个页面要我点什么？", "a": "日常不用点。能买卖时工作日 09:35 / 11:30 / 15:05 最多看三次；不能买卖白天跳过，19:30 仍至少看一次并按下一开盘自动记台账。不是问你批不批。你晚上在 :9000 更新一次数据；真金白银在同花顺手点。"},
    {"q": "账户多少钱、今天要不要动手？", "a": "看「今日」：钱和曲线在上面。有买卖会出现在右侧，纸面台账到开盘日自动登记。周六日一般空着。"},
    {"q": "卖完之后买什么？会不会再出一批评票？", "a": "合适就从 :9001 当前池买。不合适就刷新热台自己的池（live/paper_hot/POOL.json），不改 :9000 的 SIGNAL/SHORTLIST。本场不再问第二次。手里的票先不动，周一新行情才启用自有池。"},
    {"q": "和 :9000 什么关系？", "a": ":9000 是冻结的 ML1 纸面台。两边池子从现在起分开。:9000 名单只当只读井，热台不写回去。"},
    {"q": "账本1 / 账本2 去哪了？", "a": "页面上撤了。要看冻结模型去 :9000。"},
    {"q": "会自动下真实单吗？", "a": "A 股不会，只写纸面日志。MT5 仅 Ava 模拟盘、开关开着才发 0.01 手；实盘拒绝。"},
    {"q": "Cursor 会改研究仓库吗？", "a": "不会。Cloud Agent 不传仓库。"},
    {"q": "设置里能改什么？", "a": "只能改纸面开关：到点自动记账、初始资金（改了只重算数字，不改已有成交）、MT5 是否模拟发单和手数。不能改名单模型。"},
]
