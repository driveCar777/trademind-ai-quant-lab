"""Stability: V9 fake MT5 — same bars, live always refuse, SEND=0 never sends."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


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
    TRADE_RETCODE_DONE = 10009

    def __init__(self):
        self.trade_mode = 1
        self.send_count = 0
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
        return [{"time": 1700000000 + i * 3600, "close": 1.08 + i * 0.001} for i in range(count)]

    def symbol_info_tick(self, name):
        bid, ask = self.known[name]
        return _Tick(bid, ask)

    def order_send(self, request):
        self.send_count += 1
        return _Result(self.TRADE_RETCODE_DONE, 990002)


def main():
    os.environ["TRADEMIND_MT5_SEND"] = "0"
    failed = 0
    fake = FakeMT5()
    sys.modules["MetaTrader5"] = fake
    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from app.service.exceptions import TaskFailedError, WorkerNotFoundError
    from app.service import mt5_service
    from app.service import research_service

    first = mt5_service.fetch_closes("EURUSD")
    same = True
    for _ in range(19):
        again = mt5_service.fetch_closes("EURUSD")
        if again.get("close") != first.get("close") or again.get("symbol") != first.get("symbol"):
            same = False
            break
    if same and len(first.get("close") or []) == 30:
        print("[PASS] 20x fetch_closes identical")
    else:
        print("[FAIL] fetch_closes drifted")
        failed += 1

    fake.trade_mode = 2
    os.environ["TRADEMIND_MT5_SEND"] = "1"
    blocked = 0
    for _ in range(10):
        try:
            mt5_service.send_demo_order("EURUSD", "BUY", 0.01)
        except TaskFailedError:
            blocked += 1
    if blocked == 10 and fake.send_count == 0:
        print("[PASS] live blocked 10x and never sent")
    else:
        print("[FAIL] live blocked=%s send_count=%s" % (blocked, fake.send_count))
        failed += 1
    fake.trade_mode = 1

    os.environ["TRADEMIND_MT5_SEND"] = "0"
    for _ in range(10):
        mt5_service.send_demo_order("XAUUSD", "SELL", 0.01)
    if fake.send_count == 0:
        print("[PASS] SEND=0 never increments order_send")
    else:
        print("[FAIL] SEND=0 still sent %s" % fake.send_count)
        failed += 1

    refused = 0
    for name in ("factor", "backtest", "monitor"):
        try:
            research_service.run_research(name, source="mt5", symbol="EURUSD")
        except WorkerNotFoundError:
            refused += 1
    if refused == 3:
        print("[PASS] non-indicator source=mt5 stays TM-1001")
    else:
        print("[FAIL] source refusals %s" % refused)
        failed += 1

    if failed:
        print("STABILITY_07_FAIL")
        return 1
    print("STABILITY_07_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
