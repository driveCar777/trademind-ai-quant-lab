"""Read-only MT5 ground-truth collector. Never order_send.

Saves AUDIT/BROKER_GOLD_SPEC_<ts>.json and MT5_GROUND_TRUTH/*.
Masks login / account numbers. If the terminal is down, writes DATA_BLOCKED.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from research_engine.phase2_mt5.ledger import mask_login
from research_engine.phase2_mt5.paths import AUDIT, GROUND, LIVE_HIST, ensure

GOLD_ALIASES = ("GOLD", "XAUUSD", "XAUUSDm")
NO_SEND = True


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _dump(path: Path, obj: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def _safe_float(obj: Any, name: str, default=None):
    try:
        val = getattr(obj, name, default)
        if val is None:
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_int(obj: Any, name: str, default=None):
    try:
        val = getattr(obj, name, default)
        if val is None:
            return default
        return int(val)
    except (TypeError, ValueError):
        return default


def _account_payload(acc: Any) -> Dict[str, Any]:
    return {
        "login_masked": mask_login(getattr(acc, "login", "")),
        "ACCOUNT_LEVERAGE": _safe_int(acc, "leverage"),
        "ACCOUNT_MARGIN_MODE": _safe_int(acc, "margin_mode"),
        "ACCOUNT_CURRENCY": getattr(acc, "currency", None),
        "ACCOUNT_TRADE_MODE": _safe_int(acc, "trade_mode"),
        "balance": _safe_float(acc, "balance"),
        "equity": _safe_float(acc, "equity"),
        "margin": _safe_float(acc, "margin"),
        "margin_free": _safe_float(acc, "margin_free"),
        "margin_level": _safe_float(acc, "margin_level"),
        "profit": _safe_float(acc, "profit"),
        "server": getattr(acc, "server", None),
        "company": getattr(acc, "company", None),
        "name_present": bool(getattr(acc, "name", None)),
        "order_send": False,
    }


def _symbol_payload(info: Any, tick: Any) -> Dict[str, Any]:
    bid = _safe_float(tick, "bid") if tick is not None else _safe_float(info, "bid")
    ask = _safe_float(tick, "ask") if tick is not None else _safe_float(info, "ask")
    spread_pts = None
    if bid and ask and getattr(info, "point", None):
        spread_pts = (ask - bid) / float(info.point)
    return {
        "name": getattr(info, "name", None),
        "CONTRACT_SIZE": _safe_float(info, "trade_contract_size"),
        "TICK_SIZE": _safe_float(info, "trade_tick_size"),
        "TICK_VALUE": _safe_float(info, "trade_tick_value"),
        "VOLUME_MIN": _safe_float(info, "volume_min"),
        "VOLUME_MAX": _safe_float(info, "volume_max"),
        "VOLUME_STEP": _safe_float(info, "volume_step"),
        "MARGIN_INITIAL": _safe_float(info, "margin_initial"),
        "MARGIN_HEDGED": _safe_float(info, "margin_hedged"),
        "TRADE_MODE": _safe_int(info, "trade_mode"),
        "BID": bid,
        "ASK": ask,
        "SPREAD": _safe_int(info, "spread") if _safe_int(info, "spread") is not None else spread_pts,
        "SWAP_LONG": _safe_float(info, "swap_long"),
        "SWAP_SHORT": _safe_float(info, "swap_short"),
        "SWAP_MODE": _safe_int(info, "swap_mode"),
        "DIGITS": _safe_int(info, "digits"),
        "POINT": _safe_float(info, "point"),
        "swap_rollover3days": _safe_int(info, "swap_rollover3days"),
        "source": "live_terminal",
        "assumed": False,
        "order_send": False,
    }


def _row_list(items: Optional[Any], fields: List[str]) -> List[Dict[str, Any]]:
    out = []
    if not items:
        return out
    for item in items:
        rec = {}
        for name in fields:
            rec[name] = getattr(item, name, None)
        if "login" in rec:
            rec["login_masked"] = mask_login(rec.pop("login"))
        out.append(rec)
    return out


def _blocked(reason: str, detail: str = "") -> Dict[str, Any]:
    ensure()
    stamp = _utc_stamp()
    payload = {
        "status": "DATA_BLOCKED",
        "reason": reason,
        "detail": detail[:500],
        "timestamp_utc": stamp,
        "order_send": False,
        "candidate": False,
        "schema": "SPEC §30.4",
        "file_meta_not_live": None,
    }
    meta_path = LIVE_HIST / "GOLD_META.json"
    if meta_path.is_file():
        payload["file_meta_not_live"] = json.loads(meta_path.read_text(encoding="utf-8"))
        payload["file_meta_not_live"]["assumed"] = True
        payload["file_meta_not_live"]["source"] = "GOLD_META.json — NOT a live snapshot"
    _dump(GROUND / "STATUS.json", payload)
    _dump(AUDIT / ("BROKER_GOLD_SPEC_%s.json" % stamp), payload)
    return payload


def collect(pull_extra_frames: bool = False) -> Dict[str, Any]:
    """Read-only collect. pull_extra_frames may copy H4/M15 into phase2/history only."""
    del pull_extra_frames
    ensure()
    if not NO_SEND:
        raise RuntimeError("collector must stay read-only")
    try:
        import MetaTrader5 as mt5
    except Exception as exc:
        return _blocked("MT5_PACKAGE_MISSING", str(exc))
    if not mt5.initialize():
        err = mt5.last_error()
        return _blocked("MT5_INITIALIZE_FAILED", str(err))
    try:
        acc = mt5.account_info()
        if acc is None:
            return _blocked("NO_ACCOUNT", str(mt5.last_error()))
        broker = None
        info = None
        for name in GOLD_ALIASES:
            try:
                mt5.symbol_select(name, True)
            except Exception:
                pass
            info = mt5.symbol_info(name)
            if info is not None:
                broker = name
                break
        if info is None:
            return _blocked("GOLD_SYMBOL_MISSING", "tried %s" % (GOLD_ALIASES,))
        tick = mt5.symbol_info_tick(broker)
        from_dt = datetime(2018, 1, 1)
        to_dt = datetime.now()
        orders = mt5.orders_get()
        positions = mt5.positions_get()
        hist_orders = mt5.history_orders_get(from_dt, to_dt)
        deals = mt5.history_deals_get(from_dt, to_dt)
        account = _account_payload(acc)
        symbol = _symbol_payload(info, tick)
        stamp = _utc_stamp()
        spec = {
            "status": "AVAILABLE",
            "timestamp_utc": stamp,
            "broker_symbol": broker,
            "logical": "XAUUSD",
            "order_send": False,
            "candidate": False,
            "account": account,
            "GOLD": symbol,
            "note": "Live terminal snapshot. Not README assumptions.",
        }
        order_fields = ["ticket", "time_setup", "symbol", "type", "volume_current", "price_open", "sl", "tp", "magic"]
        deal_fields = ["ticket", "order", "time", "symbol", "type", "entry", "volume", "price", "commission", "swap", "profit", "magic", "position_id"]
        pos_fields = ["ticket", "time", "symbol", "type", "volume", "price_open", "sl", "tp", "swap", "profit", "magic"]
        ground = {
            "account": account,
            "symbol_gold": symbol,
            "orders": _row_list(orders, order_fields),
            "deals": _row_list(deals, deal_fields),
            "positions": _row_list(positions, pos_fields),
            "history_orders": _row_list(hist_orders, order_fields + ["time_done"]),
        }
        _dump(GROUND / "ACCOUNT_SNAPSHOT.json", account)
        _dump(GROUND / "SYMBOL_GOLD.json", symbol)
        _dump(GROUND / "ORDERS.json", {"n": len(ground["orders"]), "rows": ground["orders"]})
        _dump(GROUND / "DEALS.json", {"n": len(ground["deals"]), "rows": ground["deals"]})
        _dump(GROUND / "POSITIONS.json", {"n": len(ground["positions"]), "rows": ground["positions"]})
        _dump(GROUND / "HISTORY_ORDERS.json", {"n": len(ground["history_orders"]), "rows": ground["history_orders"]})
        _dump(GROUND / "STATUS.json", {"status": "AVAILABLE", "timestamp_utc": stamp, "broker_symbol": broker})
        _dump(GROUND / "INDEX.json", {
            "account": "ACCOUNT_SNAPSHOT.json",
            "symbol": "SYMBOL_GOLD.json",
            "orders": "ORDERS.json",
            "deals": "DEALS.json",
            "positions": "POSITIONS.json",
            "history_orders": "HISTORY_ORDERS.json",
            "goal": "reconstruct any trade from broker/terminal data",
        })
        spec_path = AUDIT / ("BROKER_GOLD_SPEC_%s.json" % stamp)
        _dump(spec_path, spec)
        spec["paths"] = {"spec": str(spec_path), "ground": str(GROUND)}
        return spec
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    out = collect()
    print(json.dumps({k: out.get(k) for k in ("status", "reason", "broker_symbol", "GOLD", "account") if k in out}, indent=2, default=str))
