"""True paper/demo ledger: signal → order → deal → position → close deal.

SPEC §30.3. Same signal_id must map to an MT5 deal when one exists.
Write-once unless TRADEMIND_PHASE2_FORCE=1.
Never stores raw login / account number.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from research_engine.phase2_mt5.contract import validate as validate_signal
from research_engine.phase2_mt5.paths import LEDGER_DIR, ensure


def _force() -> bool:
    return os.environ.get("TRADEMIND_PHASE2_FORCE") == "1"


def empty_ledger() -> Dict[str, Any]:
    return {
        "profile": "PHASE2_TRUE_LEDGER",
        "candidate": False,
        "order_send": False,
        "events": [],
        "open_positions": {},
        "by_signal": {},
    }


def load(path: Optional[Path] = None) -> Dict[str, Any]:
    ensure()
    path = path or (LEDGER_DIR / "LEDGER.json")
    if not path.is_file():
        return empty_ledger()
    return json.loads(path.read_text(encoding="utf-8"))


def dump(ledger: Dict[str, Any], path: Optional[Path] = None) -> Path:
    ensure()
    path = path or (LEDGER_DIR / "LEDGER.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_once(obj: Any, path: Path) -> Path:
    if path.is_file() and not _force():
        raise RuntimeError("WRITE_ONCE_REFUSED %s" % path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def mask_login(login: Any) -> str:
    text = str(login or "")
    if len(text) >= 4:
        return "****" + text[-4:]
    return "****"


def _index(ledger: Dict[str, Any], signal_id: str) -> Dict[str, Any]:
    slot = ledger["by_signal"].setdefault(signal_id, {
        "signal_id": signal_id,
        "order": None,
        "deals": [],
        "position": None,
        "close_deal": None,
    })
    return slot


def record_signal(ledger: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
    errors = validate_signal(signal)
    if errors:
        raise ValueError("ledger signal invalid: " + "; ".join(errors))
    ev = {"type": "SIGNAL", **signal}
    ledger["events"].append(ev)
    _index(ledger, signal["signal_id"])["signal"] = signal
    return ev


def record_order(
    ledger: Dict[str, Any],
    signal_id: str,
    requested_fill: Optional[float],
    actual_fill: Optional[float],
    bid: Optional[float],
    ask: Optional[float],
    spread: Optional[float],
    volume: Optional[float],
    order_ticket: Optional[str] = None,
    status: str = "PAPER",
) -> Dict[str, Any]:
    slip = None
    if requested_fill is not None and actual_fill is not None:
        slip = float(actual_fill) - float(requested_fill)
    ev = {
        "type": "ORDER",
        "signal_id": signal_id,
        "requested_fill": requested_fill,
        "actual_fill": actual_fill,
        "slippage": slip,
        "bid": bid,
        "ask": ask,
        "spread": spread,
        "volume": volume,
        "order_ticket": order_ticket,
        "status": status,
    }
    ledger["events"].append(ev)
    _index(ledger, signal_id)["order"] = ev
    return ev


def record_deal(
    ledger: Dict[str, Any],
    signal_id: str,
    deal_ticket: Optional[str],
    price: Optional[float],
    volume: Optional[float],
    commission: Optional[float],
    swap: Optional[float],
    profit: Optional[float],
    entry: str = "IN",
) -> Dict[str, Any]:
    ev = {
        "type": "DEAL",
        "signal_id": signal_id,
        "deal_ticket": deal_ticket,
        "price": price,
        "volume": volume,
        "commission": commission,
        "swap": swap,
        "profit": profit,
        "entry": entry,
    }
    ledger["events"].append(ev)
    slot = _index(ledger, signal_id)
    slot["deals"].append(ev)
    if entry == "OUT":
        slot["close_deal"] = ev
    return ev


def record_position(
    ledger: Dict[str, Any],
    signal_id: str,
    side: str,
    volume: Optional[float],
    price_open: Optional[float],
    unrealized: Optional[float],
    position_ticket: Optional[str] = None,
) -> Dict[str, Any]:
    ev = {
        "type": "POSITION",
        "signal_id": signal_id,
        "side": side,
        "volume": volume,
        "price_open": price_open,
        "unrealized": unrealized,
        "position_ticket": position_ticket,
    }
    ledger["events"].append(ev)
    _index(ledger, signal_id)["position"] = ev
    if position_ticket:
        ledger["open_positions"][str(position_ticket)] = ev
    return ev


def record_account(
    ledger: Dict[str, Any],
    signal_id: str,
    balance: Optional[float],
    equity: Optional[float],
    margin: Optional[float],
    free_margin: Optional[float],
    margin_level: Optional[float],
    drawdown: Optional[float],
    login_masked: str = "****",
) -> Dict[str, Any]:
    ev = {
        "type": "ACCOUNT",
        "signal_id": signal_id,
        "balance": balance,
        "equity": equity,
        "margin": margin,
        "free_margin": free_margin,
        "margin_level": margin_level,
        "drawdown": drawdown,
        "login_masked": login_masked,
    }
    ledger["events"].append(ev)
    return ev


def lifecycle_ok(ledger: Dict[str, Any], signal_id: str) -> bool:
    slot = ledger.get("by_signal", {}).get(signal_id) or {}
    return bool(slot.get("signal") and slot.get("order") and slot.get("deals"))
