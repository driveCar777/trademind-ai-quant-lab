"""Orders: paper ticket plus V9 demo send. Never send on live."""

from __future__ import print_function

import json
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config.settings import get_settings
from app.service.exceptions import TaskFailedError, TaskNotFoundError, WorkerBusyError, WorkerNotFoundError
from app.service.mt5_service import probe_mt5 as probe_mt5_live, send_demo_order
from app.service.research_service import get_research, list_research

ORDER_LOCK = threading.Lock()
VOLUME = 0.01


def _orders_dir() -> Path:
    path = get_settings().data_root / "orders"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _next_id() -> str:
    day = datetime.utcnow().strftime("%Y%m%d")
    prefix = "tm-order-%s-" % day
    highest = 0
    for item in _orders_dir().glob(prefix + "*.json"):
        try:
            highest = max(highest, int(item.stem.split("-")[-1]))
        except ValueError:
            continue
    return "%s%06d" % (prefix, highest + 1)


def _save(record: Dict[str, Any]) -> None:
    path = _orders_dir() / ("%s.json" % record["order_id"])
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def _load(order_id: str) -> Dict[str, Any]:
    path = _orders_dir() / ("%s.json" % order_id)
    if not path.is_file():
        raise TaskNotFoundError(order_id)
    return json.loads(path.read_text(encoding="utf-8"))


def probe_mt5() -> Dict[str, Any]:
    return probe_mt5_live()


def _parse_rsi(summary: str) -> Optional[float]:
    match = re.search(r"RSI[^\d]*(\d+(?:\.\d+)?)", summary or "", re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1))


def proposal_from_research(research: Dict[str, Any]) -> Dict[str, Any]:
    preset = research.get("preset") or ""
    summary = research.get("summary") or ""
    probe = probe_mt5()
    base = {
        "research_id": research.get("research_id") or "",
        "volume": VOLUME,
        "mode": "paper",
        "mt5_connected": bool(probe.get("connected")),
        "account_mode": probe.get("account_mode") or "offline",
        "created_at": _now_iso(),
        "wire_test": False,
    }
    if preset != "indicator":
        base.update({
            "symbol": "",
            "side": "HOLD",
            "status": "REFUSED",
            "reason": "not_orderable_preset",
        })
        return base
    rsi = _parse_rsi(summary)
    symbol = (research.get("symbol") or "").strip() or "EURUSD"
    if rsi is None:
        base.update({
            "symbol": symbol,
            "side": "HOLD",
            "status": "REFUSED",
            "reason": "rsi_missing",
            "wire_test": True,
        })
        return base
    if rsi >= 70:
        side, reason = "SELL", "rsi_overbought"
    elif rsi <= 30:
        side, reason = "BUY", "rsi_oversold"
    else:
        base.update({
            "symbol": symbol,
            "side": "HOLD",
            "status": "REFUSED",
            "reason": "rsi_neutral",
            "wire_test": True,
        })
        return base
    base.update({
        "symbol": symbol,
        "side": side,
        "status": "PREVIEW",
        "reason": reason,
    })
    return base


def _accepted_for(research_id: str) -> Optional[Dict[str, Any]]:
    for path in _orders_dir().glob("tm-order-*.json"):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if row.get("research_id") == research_id and row.get("status") == "ACCEPTED":
            return row
    return None


def preview_order(research_id: str) -> Dict[str, Any]:
    research = get_research(research_id)
    ticket = proposal_from_research(research)
    ticket["order_id"] = ""
    ticket["status"] = "PREVIEW" if ticket.get("side") in ("BUY", "SELL") else "REFUSED"
    return ticket


def submit_order(research_id: str, confirm: bool, side: Optional[str] = None) -> Dict[str, Any]:
    if confirm is not True:
        raise WorkerNotFoundError("confirm")
    chosen = (side or "").strip().upper()
    if chosen and chosen not in ("BUY", "SELL"):
        raise WorkerNotFoundError("side")
    if not ORDER_LOCK.acquire(blocking=False):
        raise WorkerBusyError("order")
    try:
        research = get_research(research_id)
        existing = _accepted_for(research_id)
        if existing:
            raise WorkerBusyError("order")
        ticket = proposal_from_research(research)
        ticket["order_id"] = _next_id()
        ticket["mt5_ticket"] = ""
        if chosen:
            if research.get("preset") != "indicator" or not (ticket.get("symbol") or "").strip():
                ticket["status"] = "REFUSED"
                ticket["side"] = "HOLD"
                ticket["reason"] = "not_orderable_preset"
                _save(ticket)
                return ticket
            ticket["side"] = chosen
            ticket["reason"] = "wire_test"
            ticket["wire_test"] = True
        if ticket.get("side") not in ("BUY", "SELL"):
            ticket["status"] = "REFUSED"
            _save(ticket)
            return ticket
        if ticket.get("account_mode") == "live":
            ticket["status"] = "REFUSED"
            ticket["reason"] = "live_blocked"
            _save(ticket)
            return ticket
        if ticket.get("account_mode") == "demo" and ticket.get("mt5_connected"):
            try:
                sent = send_demo_order(ticket.get("symbol") or "EURUSD", ticket["side"], ticket.get("volume") or VOLUME)
            except TaskFailedError as exc:
                ticket["status"] = "REFUSED"
                ticket["mode"] = "paper"
                ticket["reason"] = str(exc)
                _save(ticket)
                return ticket
            if sent.get("sent"):
                ticket["status"] = "ACCEPTED"
                ticket["mode"] = "demo"
                ticket["mt5_ticket"] = sent.get("ticket") or ""
                ticket["symbol"] = sent.get("symbol") or ticket.get("symbol")
                ticket["reason"] = (ticket.get("reason") or "") + ";mt5_demo"
            else:
                ticket["status"] = "ACCEPTED"
                ticket["mode"] = "paper"
                ticket["reason"] = (ticket.get("reason") or "") + ";" + (sent.get("reason") or "paper_only")
        else:
            ticket["status"] = "ACCEPTED"
            ticket["mode"] = "paper"
            ticket["reason"] = (ticket.get("reason") or "") + ";mt5_offline_paper"
        _save(ticket)
        return ticket
    finally:
        ORDER_LOCK.release()


def get_order(order_id: str) -> Dict[str, Any]:
    return _load(order_id)


def list_orders(limit: int = 20) -> List[Dict[str, Any]]:
    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50
    rows = []
    for path in sorted(_orders_dir().glob("tm-order-*.json")):
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            continue
    return rows[-limit:]


def desk_today() -> Dict[str, Any]:
    day = datetime.utcnow().strftime("%Y%m%d")
    research = [
        row for row in list_research(50)
        if (row.get("research_id") or "").find(day) >= 0
    ]
    orders = [
        row for row in list_orders(50)
        if (row.get("order_id") or "").find(day) >= 0
    ]
    return {
        "date": day,
        "research": research,
        "orders": orders,
        "research_count": len(research),
        "order_count": len(orders),
    }
