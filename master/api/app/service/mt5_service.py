"""V9: MT5 quotes + demo order_send on Windows Master. Xavier never runs MT5."""

from __future__ import print_function

import os
from typing import Any, Dict, List, Optional

from app.service.exceptions import TaskFailedError

ALLOWED = {
    "XAUUSD": ("GOLD", "XAUUSD", "XAUUSDm", "XAUUSD.a", "XAUUSD."),
    "EURUSD": ("EURUSD", "EURUSDm", "EURUSD.a"),
    "USDJPY": ("USDJPY", "USDJPYm", "USDJPY.a"),
    "GBPUSD": ("GBPUSD", "GBPUSDm", "GBPUSD.a"),
    "USDCAD": ("USDCAD", "USDCADm", "USDCAD.a"),
    "USDCHF": ("USDCHF", "USDCHFm", "USDCHF.a"),
    "CRUDE": (
        "CrudeOIL",
        "WTICrude",
        "XTIUSD",
        "USOIL",
        "CRUDE",
        "WTICOUSD",
        "BRENT_OIL",
        "USOIL.cash",
        "XTIUSD.cash",
    ),
}
BARS = 30
VOLUME = 0.01
MAGIC = 240824


def send_allowed() -> bool:
    return os.environ.get("TRADEMIND_MT5_SEND", "1") != "0"


def normalize_symbol(symbol: str) -> str:
    text = (symbol or "").strip().upper()
    aliases = {
        "GOLD": "XAUUSD",
        "XAU": "XAUUSD",
        "XAUUSD": "XAUUSD",
        "EURUSD": "EURUSD",
        "USDJPY": "USDJPY",
        "OIL": "CRUDE",
        "CRUDE": "CRUDE",
        "WTI": "CRUDE",
        "XTIUSD": "CRUDE",
        "USOIL": "CRUDE",
        "CRUDEOIL": "CRUDE",
        "WTICRUDE": "CRUDE",
        "BRENTOIL": "CRUDE",
        "BRENT_OIL": "CRUDE",
        "GBPUSD": "GBPUSD",
        "CABLE": "GBPUSD",
        "USDCAD": "USDCAD",
        "USDCHF": "USDCHF",
    }
    if text not in aliases and text not in ALLOWED:
        raise TaskFailedError("只支持黄金/原油/欧美/美日/美英/美加/美瑞")
    return aliases.get(text, text)


def _reject_scan_name(name: str) -> bool:
    n = (name or "").upper().replace(" ", "").replace("_", "")
    if not n or n.startswith("#"):
        return True
    for bad in ("FUTURE", "TEST", "HEATING", "SHARE", "BARRICK"):
        if bad in n:
            return True
    return False


def _scan_match(logical: str, name: str) -> bool:
    if _reject_scan_name(name):
        return False
    n = name.upper().replace(" ", "").replace("_", "")
    if logical == "XAUUSD":
        return n == "GOLD" or n.startswith("XAUUSD")
    if logical == "EURUSD":
        return n == "EURUSD" or n.startswith("EURUSD")
    if logical == "USDJPY":
        return n == "USDJPY" or n.startswith("USDJPY")
    if logical == "GBPUSD":
        return n == "GBPUSD" or n.startswith("GBPUSD")
    if logical == "USDCAD":
        return n == "USDCAD" or n.startswith("USDCAD")
    if logical == "USDCHF":
        return n == "USDCHF" or n.startswith("USDCHF")
    if logical == "CRUDE":
        return n in ("CRUDEOIL", "WTICRUDE", "XTIUSD", "USOIL", "CRUDE", "WTICOUSD", "BRENTOIL") or n.startswith(
            "XTIUSD"
        ) or n.startswith("USOIL")
    return False


def _import_mt5():
    try:
        import MetaTrader5 as mt5
        return mt5
    except Exception:
        return None


def _account_mode(account: Any) -> str:
    trade_mode = int(getattr(account, "trade_mode", -1))
    if trade_mode == 2:
        return "live"
    if trade_mode in (0, 1):
        return "demo"
    return "unknown"


class Mt5Session(object):
    def __init__(self):
        self.mt5 = _import_mt5()
        self.ok = False

    def __enter__(self):
        if self.mt5 is None:
            raise TaskFailedError("本机未装 MetaTrader5 包")
        if not self.mt5.initialize():
            raise TaskFailedError("MT5 终端连不上")
        self.ok = True
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.mt5 is not None and self.ok:
            try:
                self.mt5.shutdown()
            except Exception:
                pass
        return False

    def probe(self) -> Dict[str, Any]:
        account = self.mt5.account_info()
        if account is None:
            return {
                "available": True,
                "connected": True,
                "account_mode": "unknown",
                "login_masked": "",
                "reason": "no_account",
            }
        login = str(getattr(account, "login", "") or "")
        masked = ("****" + login[-4:]) if len(login) >= 4 else "****"
        mode = _account_mode(account)
        return {
            "available": True,
            "connected": True,
            "account_mode": mode,
            "login_masked": masked,
            "reason": "live_blocked" if mode == "live" else "probe_ok",
        }

    def _try_name(self, name: str) -> Optional[str]:
        try:
            self.mt5.symbol_select(name, True)
        except Exception:
            return None
        info = self.mt5.symbol_info(name)
        if info is None:
            return None
        return name

    def _scan_broker_symbol(self, logical: str) -> Optional[str]:
        getter = getattr(self.mt5, "symbols_get", None)
        if getter is None:
            return None
        try:
            rows = getter()
        except Exception:
            return None
        if not rows:
            return None
        ranked = []
        for item in rows:
            name = getattr(item, "name", "") or ""
            if not _scan_match(logical, name):
                continue
            visible = bool(getattr(item, "visible", False))
            exact = name.upper().replace(" ", "") in (
                "GOLD",
                "XAUUSD",
                "EURUSD",
                "USDJPY",
                "CRUDEOIL",
                "WTICRUDE",
            )
            ranked.append((0 if exact else 1, 0 if visible else 1, name))
        ranked.sort()
        for _exact, _vis, name in ranked:
            found = self._try_name(name)
            if found:
                return found
        return None

    def resolve_broker_symbol(self, logical: str) -> str:
        logical = normalize_symbol(logical)
        for name in ALLOWED[logical]:
            found = self._try_name(name)
            if found:
                return found
        scanned = self._scan_broker_symbol(logical)
        if scanned:
            return scanned
        labels = {"XAUUSD": "黄金", "EURUSD": "欧美", "USDJPY": "美日", "GBPUSD": "美英",
                  "USDCAD": "美加", "USDCHF": "美瑞", "CRUDE": "原油"}
        raise TaskFailedError("终端里没有%s（已试 %s）" % (labels.get(logical, logical), "/".join(ALLOWED[logical][:4])))

    def copy_closes(self, logical: str, bars: int = BARS, timeframe: str = "M15") -> Dict[str, Any]:
        broker = self.resolve_broker_symbol(logical)
        tf_name = "TIMEFRAME_%s" % timeframe
        tf = getattr(self.mt5, tf_name, None)
        if tf is None:
            raise TaskFailedError("不支持的周期：%s" % timeframe)
        rates = self.mt5.copy_rates_from_pos(broker, tf, 0, bars)
        if rates is None or len(rates) < 15:
            raise TaskFailedError("MT5 没有足够的 K 线：%s %s" % (broker, timeframe))
        closes = [float(row["close"]) for row in rates]
        times = []
        for row in rates:
            try:
                times.append(int(row["time"]))
            except (KeyError, TypeError, ValueError, IndexError):
                times.append(0)
        if not any(times):
            times = []
        return {
            "symbol": broker,
            "close": closes,
            "time": times,
            "logical": logical,
            "timeframe": timeframe,
        }

    def positions(self) -> List[Dict[str, Any]]:
        getter = getattr(self.mt5, "positions_get", None)
        if getter is None:
            return []
        try:
            rows = getter() or []
        except Exception:
            return []
        out: List[Dict[str, Any]] = []
        for pos in rows:
            side = "BUY" if int(getattr(pos, "type", 0) or 0) == 0 else "SELL"
            out.append({
                "ticket": str(getattr(pos, "ticket", "") or ""),
                "symbol": getattr(pos, "symbol", "") or "",
                "side": side,
                "volume": float(getattr(pos, "volume", 0) or 0),
                "price_open": float(getattr(pos, "price_open", 0) or 0),
                "profit": float(getattr(pos, "profit", 0) or 0),
                "magic": int(getattr(pos, "magic", 0) or 0),
            })
        return out

    def list_share_symbols(self, limit: int = 12) -> List[str]:
        getter = getattr(self.mt5, "symbols_get", None)
        if getter is None:
            return []
        try:
            rows = getter() or []
        except Exception:
            return []
        names: List[str] = []
        for item in rows:
            path = (getattr(item, "path", "") or "").lower()
            name = getattr(item, "name", "") or ""
            if not name or name.startswith("#"):
                continue
            if "share" not in path and "cfd-shares" not in path and "usa" not in path:
                continue
            if any(bad in name.upper() for bad in ("TEST", "FUTURE")):
                continue
            if name not in names:
                names.append(name)
            if len(names) >= limit:
                break
        return names

    def last_price(self, logical: str) -> Dict[str, Any]:
        broker = self.resolve_broker_symbol(logical)
        tick = self.mt5.symbol_info_tick(broker)
        if tick is None:
            raise TaskFailedError("没有报价：%s" % broker)
        return {
            "logical": logical,
            "symbol": broker,
            "bid": float(tick.bid),
            "ask": float(tick.ask),
        }

    def order_send_demo(self, logical: str, side: str, volume: float = VOLUME) -> Dict[str, Any]:
        if not send_allowed():
            return {"sent": False, "ticket": "", "reason": "send_disabled"}
        probe = self.probe()
        if probe.get("account_mode") == "live":
            raise TaskFailedError("当前是实盘账户，拒绝发单")
        if probe.get("account_mode") != "demo":
            raise TaskFailedError("不是模拟盘，拒绝发单")
        if side not in ("BUY", "SELL"):
            raise TaskFailedError("方向只能是 BUY/SELL")
        broker = self.resolve_broker_symbol(logical)
        tick = self.mt5.symbol_info_tick(broker)
        if tick is None:
            raise TaskFailedError("没有报价，不能发单")
        order_type = self.mt5.ORDER_TYPE_BUY if side == "BUY" else self.mt5.ORDER_TYPE_SELL
        price = float(tick.ask if side == "BUY" else tick.bid)
        filling_modes = []
        for name in ("ORDER_FILLING_IOC", "ORDER_FILLING_FOK", "ORDER_FILLING_RETURN"):
            if hasattr(self.mt5, name):
                filling_modes.append(getattr(self.mt5, name))
        last_err = "send_failed"
        for filling in filling_modes or [None]:
            request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "symbol": broker,
                "volume": float(volume),
                "type": order_type,
                "price": price,
                "deviation": 30,
                "magic": MAGIC,
                "comment": "TM V9 demo",
            }
            if filling is not None:
                request["type_filling"] = filling
            result = self.mt5.order_send(request)
            if result is not None and int(getattr(result, "retcode", 0)) == int(getattr(self.mt5, "TRADE_RETCODE_DONE", 10009)):
                return {
                    "sent": True,
                    "ticket": str(getattr(result, "order", "") or getattr(result, "deal", "") or ""),
                    "symbol": broker,
                    "reason": "mt5_demo",
                    "side": side,
                    "volume": float(volume),
                    "price": price,
                    "bid": float(tick.bid),
                    "ask": float(tick.ask),
                }
            if result is not None:
                last_err = "retcode=%s" % getattr(result, "retcode", "?")
        raise TaskFailedError("模拟盘发单失败：%s" % last_err)


def probe_mt5() -> Dict[str, Any]:
    if _import_mt5() is None:
        return {
            "available": False,
            "connected": False,
            "account_mode": "offline",
            "login_masked": "",
            "reason": "package_missing",
            "symbols": [],
        }
    try:
        with Mt5Session() as session:
            data = session.probe()
            symbols = []
            for logical in ("XAUUSD", "EURUSD", "CRUDE", "USDJPY"):
                try:
                    quote = session.last_price(logical)
                    symbols.append(quote)
                except TaskFailedError:
                    symbols.append({"logical": logical, "symbol": "", "bid": None, "ask": None})
            data["symbols"] = symbols
            return data
    except TaskFailedError as exc:
        return {
            "available": True,
            "connected": False,
            "account_mode": "offline",
            "login_masked": "",
            "reason": str(exc),
            "symbols": [],
        }


def list_quotes() -> Dict[str, Any]:
    status = probe_mt5()
    return {"account_mode": status.get("account_mode"), "items": status.get("symbols") or []}


def fetch_closes(symbol: str, bars: int = BARS) -> Dict[str, Any]:
    with Mt5Session() as session:
        return session.copy_closes(symbol, bars=bars)


def fetch_history(symbol: str, bars: int = 500, timeframe: Optional[str] = None) -> Dict[str, Any]:
    order = (timeframe,) if timeframe else ("D1", "H4", "H1")
    with Mt5Session() as session:
        last_err = "no_bars"
        for name in order:
            try:
                pulled = session.copy_closes(symbol, bars=bars, timeframe=name)
            except TaskFailedError as exc:
                last_err = str(exc)
                continue
            if len(pulled.get("close") or []) >= 200:
                return pulled
            last_err = "bars=%s" % len(pulled.get("close") or [])
        raise TaskFailedError("MT5 历史不够做证伪回测：%s" % last_err)


def send_demo_order(symbol: str, side: str, volume: float = VOLUME) -> Dict[str, Any]:
    with Mt5Session() as session:
        return session.order_send_demo(symbol, side, volume=volume)
