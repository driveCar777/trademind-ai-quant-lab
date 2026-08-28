"""IS-only brute mine on the four Xavier :8002 sidecars. Does not change Master."""
from __future__ import print_function

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "master", "api"))
os.environ["TRADEMIND_MT5_SEND"] = "0"

from app.service.mt5_service import fetch_history
from app.service.walkforward_service import (
    COMMISSION_BPS,
    SLIPPAGE_BPS,
    judge,
    pick_is,
    score_is,
    split_closes,
)

NODES = (
    "http://192.168.1.200:8002",
    "http://192.168.1.201:8002",
    "http://192.168.1.202:8002",
    "http://192.168.1.203:8002",
)
OUT_DIR = os.path.join(ROOT, "data", "mine")


def candidates():
    rows = []
    for period in (8, 10, 14, 18, 21, 28):
        for osold in (20, 25, 30, 35):
            for obuy in (65, 70, 75, 80):
                if osold >= obuy:
                    continue
                rows.append({
                    "id": "rsi-%s-%s-%s" % (period, osold, obuy),
                    "strategy": "RSI",
                    "params": {"period": period, "oversold": osold, "overbought": obuy},
                })
    for fast in (8, 10, 15, 20):
        for slow in (30, 40, 50, 60, 80):
            if fast >= slow:
                continue
            rows.append({
                "id": "sma-%s-%s" % (fast, slow),
                "strategy": "SMA_CROSS",
                "params": {"fast": fast, "slow": slow},
            })
    for period in (12, 15, 20, 25):
        for num_std in (1.5, 2.0, 2.5):
            rows.append({
                "id": "boll-%s-%s" % (period, str(num_std).replace(".", "p")),
                "strategy": "BOLLINGER",
                "params": {"period": period, "num_std": num_std},
            })
    rows.append({"id": "macd-12-26-9", "strategy": "EMA_MACD", "params": {}})
    rows.append({"id": "turtle", "strategy": "TURTLE", "params": {}})
    rows.append({"id": "regime", "strategy": "REGIME_SWITCH", "params": {}})
    return rows


def live_nodes():
    ok = []
    for base in NODES:
        try:
            resp = requests.get(base + "/version", timeout=4)
            if resp.status_code == 200 and (resp.json() or {}).get("version") >= "2.1.4":
                ok.append(base)
        except requests.RequestException:
            continue
    return ok


def run_one(base, broker, closes, cut, cand):
    payload = {
        "strategy": cand["strategy"],
        "symbol": broker,
        "start": "mine-%s" % cand["id"],
        "close": closes,
        "cut": cut,
        "slippage_bps": SLIPPAGE_BPS,
        "commission_bps": COMMISSION_BPS,
        "params": cand.get("params") or {},
    }
    resp = requests.post(base + "/backtest", json=payload, timeout=90)
    body = resp.json()
    is_row = body.get("is") or {}
    oos_row = body.get("oos") or {}
    return {
        "id": cand["id"],
        "strategy": cand["strategy"],
        "params": cand.get("params") or {},
        "node": base,
        "verdict": judge(is_row, oos_row),
        "is_profit": is_row.get("profit"),
        "oos_profit": oos_row.get("profit"),
        "is_drawdown": is_row.get("max_drawdown"),
        "oos_drawdown": oos_row.get("max_drawdown"),
        "is_trades": is_row.get("total_trades"),
        "oos_trades": oos_row.get("total_trades"),
        "is_score": score_is(is_row),
    }


def main():
    logical = (sys.argv[1] if len(sys.argv) > 1 else "XAUUSD").upper()
    tf = sys.argv[2] if len(sys.argv) > 2 else "H1"
    nodes = live_nodes()
    if not nodes:
        print("NO_BACKTEST_NODES")
        return 1
    pulled = fetch_history(logical, bars=2000, timeframe=tf)
    closes = pulled.get("close") or []
    is_c, _oos = split_closes(closes)
    cut = len(is_c)
    cands = candidates()
    print("nodes=%s bars=%s cut=%s jobs=%s" % (len(nodes), len(closes), cut, len(cands)))
    rows = [None] * len(cands)

    def work(i):
        return i, run_one(nodes[i % len(nodes)], pulled.get("symbol") or "GOLD", closes, cut, cands[i])

    with ThreadPoolExecutor(max_workers=min(8, len(nodes) * 2)) as pool:
        futs = [pool.submit(work, i) for i in range(len(cands))]
        done = 0
        for fut in as_completed(futs):
            i, row = fut.result()
            rows[i] = row
            done += 1
            if done % 20 == 0 or done == len(cands):
                print("progress %s/%s" % (done, len(cands)))

    picked = pick_is(rows)
    if picked:
        picked = dict(picked)
        picked["picked"] = True
    survived = [r for r in rows if r and r.get("verdict") == "survived"]
    is_ok = [r for r in rows if r and r.get("is_score") is not None]
    is_ok.sort(key=lambda item: item.get("is_score") or -999, reverse=True)
    report = {
        "created_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "symbol": pulled.get("symbol"),
        "timeframe": pulled.get("timeframe"),
        "bars": len(closes),
        "cut": cut,
        "nodes": nodes,
        "jobs": len(cands),
        "is_eligible": len(is_ok),
        "oos_survived": len(survived),
        "picked_by_is": picked,
        "top_is": is_ok[:8],
        "rows": rows,
        "note": "picked_by_is uses IS only. OOS is published, not used to choose.",
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    tag = "%s_%s" % ((pulled.get("symbol") or logical).lower(), (pulled.get("timeframe") or tf).lower())
    path = os.path.join(OUT_DIR, "%s_%s.json" % (tag, stamp))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("WROTE", path)
    print("eligible_IS=%s survived_OOS=%s" % (len(is_ok), len(survived)))
    if picked:
        print("PICKED", picked.get("id"), "IS", picked.get("is_profit"), "OOS", picked.get("oos_profit"), picked.get("verdict"))
    print("TOP_IS")
    for row in is_ok[:8]:
        print(" ", row.get("id"), "is", row.get("is_profit"), "dd", row.get("is_drawdown"), "oos", row.get("oos_profit"), row.get("verdict"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
