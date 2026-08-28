"""Fetch frozen-engine ledgers for the manual review set. No engine change."""
from __future__ import print_function

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "master", "api"))
os.environ["TRADEMIND_MT5_SEND"] = "0"

import requests
from app.service.mt5_service import fetch_history
from app.service.walkforward_service import COMMISSION_BPS, IS_RATIO, SLIPPAGE_BPS, judge, score_is

OUT = os.path.join(ROOT, "data", "mine", "longrun", "review_ledgers.json")
ROWS = os.path.join(ROOT, "data", "mine", "longrun", "rows.jsonl")
CANDS = (
    ("XAUUSD", "M15", "RSI", {"period": 14, "oversold": 30, "overbought": 80}, "rsi-14-30-80"),
    ("XAUUSD", "H1", "RSI", {"period": 14, "oversold": 35, "overbought": 85}, "rsi-14-35-85"),
    ("EURUSD", "H4", "RSI", {"period": 28, "oversold": 32, "overbought": 72}, "rsi-28-32-72"),
)


def neighbor_ids(cid):
    parts = cid.split("-")
    if parts[0] != "rsi" or len(parts) != 4:
        return []
    period, osold, obuy = int(parts[1]), int(parts[2]), int(parts[3])
    out = [cid]
    for dp, dos, dob in ((0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1)):
        p, a, b = period + dp, osold + dos, obuy + dob
        if a < b and p >= 2:
            out.append("rsi-%s-%s-%s" % (p, a, b))
    return out


def main():
    need = set()
    for logical, tf, _strat, _params, cid in CANDS:
        sym = "GOLD" if logical == "XAUUSD" else "EURUSD"
        for nid in neighbor_ids(cid):
            need.add((sym, tf, nid))
    neigh = {}
    with open(ROWS, "r", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("win_start") != 0 or row.get("win_len") != 2000:
                continue
            if "|c" in str(row.get("key") or ""):
                continue
            key = (row.get("symbol"), row.get("timeframe"), row.get("id"))
            if key in need:
                neigh[key] = row
    ledgers = []
    for logical, tf, strat, params, cid in CANDS:
        pulled = fetch_history(logical, bars=2000, timeframe=tf)
        closes = [float(x) for x in (pulled.get("close") or [])]
        cut = int(len(closes) * IS_RATIO)
        payload = {
            "strategy": strat,
            "symbol": pulled.get("symbol") or logical,
            "start": "review-%s" % cid,
            "close": closes,
            "cut": cut,
            "slippage_bps": SLIPPAGE_BPS,
            "commission_bps": COMMISSION_BPS,
            "params": params,
        }
        body = requests.post("http://192.168.1.202:8002/backtest", json=payload, timeout=90).json()
        trades = body.get("trades") or []
        is_row = body.get("is") or {}
        oos_row = body.get("oos") or {}
        fills = []
        for item in trades:
            fills.append({"idx": item.get("idx"), "type": item.get("type"), "price": item.get("price")})
        ledgers.append({
            "id": cid,
            "symbol": pulled.get("symbol"),
            "timeframe": pulled.get("timeframe") or tf,
            "bars": len(closes),
            "cut": cut,
            "verdict": judge(is_row, oos_row),
            "is": {"profit": is_row.get("profit"), "max_drawdown": is_row.get("max_drawdown"), "total_trades": is_row.get("total_trades")},
            "oos": {"profit": oos_row.get("profit"), "max_drawdown": oos_row.get("max_drawdown"), "total_trades": oos_row.get("total_trades")},
            "is_score": score_is(is_row),
            "fills": fills,
            "fill_n": len(trades),
        })
        print(
            "LEDGER",
            cid,
            pulled.get("symbol"),
            tf,
            judge(is_row, oos_row),
            "IS",
            is_row.get("profit"),
            "OOS",
            oos_row.get("profit"),
            flush=True,
        )
    compact = {}
    for key, row in neigh.items():
        compact[str(key)] = {
            "verdict": row.get("verdict"),
            "is": row.get("is_profit"),
            "oos": row.get("oos_profit"),
            "is_n": row.get("is_trades"),
            "oos_n": row.get("oos_trades"),
            "is_dd": row.get("is_drawdown"),
            "oos_dd": row.get("oos_drawdown"),
        }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"ledgers": ledgers, "neighbors": compact}, fh, ensure_ascii=False, indent=2)
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
