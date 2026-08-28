"""Smoke: V9 MT5 demo path. Fake terminal only. Never send to a real account."""
from __future__ import print_function

import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DASH = os.path.join(ROOT, "dashboard", "index.html")
WORKERS = os.path.join(ROOT, "workers")


class _Account(object):
    def __init__(self, trade_mode, login=12345678):
        self.trade_mode = trade_mode
        self.login = login


class _Tick(object):
    def __init__(self, bid, ask):
        self.bid = bid
        self.ask = ask


class _Result(object):
    def __init__(self, retcode, order):
        self.retcode = retcode
        self.order = order
        self.deal = order


class FakeMT5(object):
    TIMEFRAME_M15 = 15
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_FOK = 2
    ORDER_FILLING_RETURN = 3
    TRADE_RETCODE_DONE = 10009

    def __init__(self):
        self.trade_mode = 1
        self.send_count = 0
        self.last_request = None
        self.known = {
            "XAUUSD": (2345.1, 2345.4),
            "EURUSD": (1.0851, 1.0853),
            "USDJPY": (149.21, 149.24),
            "XTIUSD": (78.12, 78.16),
        }

    def initialize(self):
        return True

    def shutdown(self):
        return True

    def account_info(self):
        return _Account(self.trade_mode)

    def symbol_select(self, name, enable):
        return name in self.known

    def symbol_info(self, name):
        return object() if name in self.known else None

    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        if symbol not in self.known:
            return None
        return [{"time": 1700000000 + i * 3600, "close": 1.08 + i * 0.001} for i in range(count)]

    def symbol_info_tick(self, name):
        if name not in self.known:
            return None
        bid, ask = self.known[name]
        return _Tick(bid, ask)

    def symbols_get(self):
        rows = []
        for name in self.known:
            row = types.SimpleNamespace(name=name, visible=True, path="")
            rows.append(row)
        return rows

    def order_send(self, request):
        self.send_count += 1
        self.last_request = request
        return _Result(self.TRADE_RETCODE_DONE, 990001)


def _install_fake():
    fake = FakeMT5()
    sys.modules["MetaTrader5"] = fake
    return fake


def _workers_mention_mt5():
    hits = []
    for dirpath, _dirnames, filenames in os.walk(WORKERS):
        for name in filenames:
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            text = open(path, encoding="utf-8").read()
            if "MetaTrader5" in text or "order_send" in text:
                hits.append(path)
    return hits


def main():
    os.environ["TRADEMIND_MT5_SEND"] = "0"
    failed = 0
    fake = _install_fake()

    with open(DASH, encoding="utf-8") as fh:
        html = fh.read()
    if "function applyMt5(" in html and "source: 'mt5'" in html and "确认挂模拟盘" in html:
        print("[PASS] dashboard MT5 chips + source + confirm")
    else:
        print("[FAIL] dashboard missing MT5 path")
        failed += 1
    init = html[html.find("async function init()"):html.find("init();")]
    if "/api/v1/orders/submit" not in init and "/api/v1/research/run" not in init:
        print("[PASS] init() does not research or submit")
    else:
        print("[FAIL] init() auto-runs")
        failed += 1

    hits = _workers_mention_mt5()
    if not hits:
        print("[PASS] Xavier workers do not import MT5")
    else:
        print("[FAIL] workers mention MT5 %s" % hits)
        failed += 1

    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from app.service.exceptions import TaskFailedError, WorkerNotFoundError
    from app.service import mt5_service
    from app.service import research_service

    probe = mt5_service.probe_mt5()
    if probe.get("account_mode") == "demo" and probe.get("connected") and len(probe.get("symbols") or []) == 4:
        print("[PASS] fake probe demo + 4 symbols")
    else:
        print("[FAIL] probe %s" % probe)
        failed += 1

    quotes = mt5_service.list_quotes()
    names = [item.get("logical") for item in quotes.get("items") or []]
    if quotes.get("account_mode") == "demo" and names == ["XAUUSD", "EURUSD", "CRUDE", "USDJPY"]:
        print("[PASS] quotes four logicals")
    else:
        print("[FAIL] quotes %s" % quotes)
        failed += 1

    pulled = mt5_service.fetch_closes("XAUUSD")
    if pulled.get("symbol") == "XAUUSD" and len(pulled.get("close") or []) == 30:
        print("[PASS] fetch XAUUSD 30 closes")
    else:
        print("[FAIL] fetch %s" % pulled)
        failed += 1

    saved = dict(fake.known)
    fake.known = {
        "GOLD": (2345.1, 2345.4),
        "EURUSD": (1.0851, 1.0853),
        "USDJPY": (149.21, 149.24),
        "CrudeOIL": (78.12, 78.16),
    }
    ava_gold = mt5_service.fetch_closes("XAUUSD")
    ava_oil = mt5_service.fetch_closes("CRUDE")
    if ava_gold.get("symbol") == "GOLD" and ava_oil.get("symbol") == "CrudeOIL":
        print("[PASS] Ava-style GOLD / CrudeOIL resolve")
    else:
        print("[FAIL] Ava resolve gold=%s oil=%s" % (ava_gold, ava_oil))
        failed += 1
    fake.known = saved

    os.environ["TRADEMIND_MT5_SEND"] = "1"
    sent = mt5_service.send_demo_order("EURUSD", "BUY", 0.01)
    if sent.get("sent") and sent.get("ticket") == "990001" and fake.send_count == 1:
        print("[PASS] fake demo order_send ticket")
    else:
        print("[FAIL] send %s count=%s" % (sent, fake.send_count))
        failed += 1

    os.environ["TRADEMIND_MT5_SEND"] = "0"
    before = fake.send_count
    disabled = mt5_service.send_demo_order("EURUSD", "SELL", 0.01)
    if disabled.get("sent") is False and disabled.get("reason") == "send_disabled" and fake.send_count == before:
        print("[PASS] TRADEMIND_MT5_SEND=0 does not send")
    else:
        print("[FAIL] send_disabled %s count=%s" % (disabled, fake.send_count))
        failed += 1

    fake.trade_mode = 2
    os.environ["TRADEMIND_MT5_SEND"] = "1"
    try:
        mt5_service.send_demo_order("EURUSD", "BUY", 0.01)
        print("[FAIL] live account did not raise")
        failed += 1
    except TaskFailedError:
        print("[PASS] live account blocked")
    fake.trade_mode = 1
    os.environ["TRADEMIND_MT5_SEND"] = "0"

    try:
        mt5_service.normalize_symbol("600519")
        print("[FAIL] A-share symbol accepted")
        failed += 1
    except TaskFailedError:
        print("[PASS] unsupported symbol TM-1003")

    try:
        research_service.run_research("factor", source="mt5", symbol="EURUSD")
        print("[FAIL] factor+mt5 did not raise")
        failed += 1
    except WorkerNotFoundError:
        print("[PASS] source=mt5 only indicator")

    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    body = client.get("/api/v1/mt5/quotes").json()
    data = body.get("data") or {}
    if body.get("success") and data.get("account_mode") == "demo" and data.get("items"):
        print("[PASS] GET /mt5/quotes")
    else:
        print("[FAIL] quotes route %s" % body)
        failed += 1

    if failed:
        print("SMOKE_18_FAIL")
        return 1
    print("SMOKE_18_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
