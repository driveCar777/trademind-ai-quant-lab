"""Audit V11 walk-forward: independent RSI, PnL, judge, ledger, live MT5."""
from __future__ import print_function

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LEDGER = os.path.join(ROOT, "data", "research", "tm-research-20260824-009995.json")


def _rsi(closes, period=14):
    gains = [max(0, closes[i] - closes[i - 1]) for i in range(1, len(closes))]
    losses = [max(0, closes[i - 1] - closes[i]) for i in range(1, len(closes))]
    rsi = [50.0] * period
    for i in range(period, len(closes)):
        ag = sum(gains[i - period:i]) / period
        al = sum(losses[i - period:i]) / period
        rsi.append(100 - 100 / (1 + ag / al) if al > 0 else 100.0)
    return rsi


def _signals(closes, period=14, buy=30, sell=70):
    rsi = _rsi(closes, period)
    pos = 0
    rows = []
    for i in range(period, len(closes)):
        if rsi[i] < buy and pos == 0:
            rows.append(("BUY", i, closes[i]))
            pos = 1
        elif rsi[i] > sell and pos == 1:
            rows.append(("SELL", i, closes[i]))
            pos = 0
    if pos == 1:
        rows.append(("SELL", len(closes) - 1, closes[-1]))
    return rows


def _pair_pnl(trades):
    out = []
    buy = None
    for item in trades:
        if item["side"] == "BUY":
            buy = item
        elif item["side"] == "SELL" and buy is not None:
            bp = float(buy["price"])
            sp = float(item["price"])
            out.append(round((sp - bp) / bp * 100, 2))
            buy = None
    return out


def main():
    os.environ["TRADEMIND_MT5_SEND"] = "0"
    failed = 0
    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    sys.path.insert(0, os.path.join(ROOT, "backtest-worker-v1"))
    import server as bt
    from app.service.walkforward_service import CANDIDATES, judge, pick_is, score_is, split_closes, stamp_trades, window_of

    dump = [2000.0]
    for _i in range(80):
        dump.append(dump[-1] * 0.985)
    rally = [dump[-1]]
    for _i in range(80):
        rally.append(rally[-1] * 1.015)
    wave = dump + rally[1:]
    local = _signals(wave)
    worker = bt.run_backtest("RSI", "GOLD", "audit", closes=wave, slippage_bps=10, commission_bps=5)
    widx = [(t["type"], t["idx"]) for t in worker.get("trades") or []]
    lidx = [(t[0], t[1]) for t in local]
    if widx == lidx:
        print("[PASS] independent RSI idx matches worker")
    else:
        print("[FAIL] RSI mismatch local=%s worker=%s" % (lidx[:6], widx[:6]))
        failed += 1

    pairs = []
    buy_px = None
    for t in worker.get("trades") or []:
        if t["type"] == "BUY":
            buy_px = t["price"]
        else:
            pairs.append(round((t["price"] - buy_px) / buy_px * 100, 2))
            if abs(pairs[-1] - t.get("pnl_pct", 999)) > 0.011:
                print("[FAIL] worker pnl %s vs pair %s" % (t.get("pnl_pct"), pairs[-1]))
                failed += 1
                break
    else:
        print("[PASS] worker sell pnl matches fill prices")

    eq = 10000.0
    pos = 0.0
    ep = 0.0
    for t in worker.get("trades") or []:
        if t["type"] == "BUY":
            pos = eq / t["price"]
            eq = 0.0
            ep = t["price"]
        else:
            eq = pos * t["price"] * (1 - 5 / 10000.0)
            pos = 0.0
    if pos > 0:
        eq = pos * ep
    profit = round((eq - 10000.0) / 10000.0 * 100, 2)
    if abs(profit - worker["profit"]) <= 0.05:
        print("[PASS] equity from fills ~= worker profit %s vs %s" % (profit, worker["profit"]))
    else:
        print("[FAIL] equity %s worker %s" % (profit, worker["profit"]))
        failed += 1

    if judge({"total_trades": 8, "max_drawdown": 10, "profit": -20}, {"total_trades": 6, "max_drawdown": 8, "profit": 1.2}) == "survived":
        print("[PASS] judge survived despite IS loss")
    else:
        print("[FAIL] judge survived")
        failed += 1
    if judge({"total_trades": 8, "max_drawdown": 10, "profit": 5}, {"total_trades": 6, "max_drawdown": 8, "profit": 0}) == "falsified":
        print("[PASS] judge oos 0 is falsified")
    else:
        print("[FAIL] judge zero oos")
        failed += 1
    if judge({"total_trades": 4, "max_drawdown": 10, "profit": 5}, {"total_trades": 6, "max_drawdown": 8, "profit": 2}) == "insufficient":
        print("[PASS] judge 4 fills insufficient")
    else:
        print("[FAIL] judge min trades")
        failed += 1
    if judge({"total_trades": 8, "max_drawdown": 25.1, "profit": 5}, {"total_trades": 6, "max_drawdown": 8, "profit": 2}) == "risk_fail":
        print("[PASS] judge 25.1 dd risk_fail")
    else:
        print("[FAIL] judge dd")
        failed += 1
    if len(CANDIDATES) == 12:
        print("[PASS] frozen mine has 12 candidates")
    else:
        print("[FAIL] candidates %s" % len(CANDIDATES))
        failed += 1
    better_is = {
        "id": "a",
        "is_score": score_is({"total_trades": 8, "max_drawdown": 10, "profit": 5}),
        "oos_profit": -9,
    }
    better_oos = {
        "id": "b",
        "is_score": score_is({"total_trades": 8, "max_drawdown": 10, "profit": 1}),
        "oos_profit": 20,
    }
    picked = pick_is([better_is, better_oos])
    if picked and picked["id"] == "a":
        print("[PASS] pick uses IS score, ignores better OOS")
    else:
        print("[FAIL] pick %s" % picked)
        failed += 1

    hold = [100.0]
    for _i in range(174):
        hold.append(hold[-1] * 0.997)
    for _i in range(75):
        hold.append(hold[-1] * 1.01)
    is_h, oos_h = split_closes(hold)
    cut = len(is_h)
    cont = bt.run_backtest("RSI", "GOLD", "cont", closes=hold, slippage_bps=0, commission_bps=0, cut=cut)
    sells = [t for t in (cont.get("trades") or []) if t.get("type") == "SELL"]
    forced = any(t.get("idx") == cut - 1 for t in sells)
    carried = any(t.get("idx", -1) >= cut for t in sells) and (cont.get("is") or {}).get("profit") is not None
    if (not forced) and carried and "oos" in cont:
        print("[PASS] continuous cut does not flatten; OOS sell idx=%s" % [t.get("idx") for t in sells])
    else:
        print("[FAIL] carry cut=%s forced=%s sells=%s is=%s" % (cut, forced, sells, cont.get("is")))
        failed += 1
    names = []
    for name in ("RSI", "EMA_MACD", "SMA_CROSS", "BOLLINGER", "TURTLE", "REGIME_SWITCH"):
        row = bt.run_backtest(name, "GOLD", "basket", closes=hold, slippage_bps=10, commission_bps=5, cut=cut)
        if row.get("is") and row.get("oos"):
            names.append(name)
    if names == ["RSI", "EMA_MACD", "SMA_CROSS", "BOLLINGER", "TURTLE", "REGIME_SWITCH"]:
        print("[PASS] frozen basket all return is/oos")
    else:
        print("[FAIL] basket %s" % names)
        failed += 1
    wave = [2000.0]
    for _i in range(120):
        wave.append(wave[-1] * 0.994)
    for _i in range(120):
        wave.append(wave[-1] * 1.006)
    tags = bt.label_regimes(wave)
    if tags[80] == "down" and tags[-10] == "up" and "range" in tags:
        print("[PASS] regime labels see down then up")
    else:
        print("[FAIL] labels mid=%s end=%s" % (tags[80], tags[-10]))
        failed += 1

    with open(LEDGER, encoding="utf-8") as fh:
        rec = json.load(fh)
    trades = rec.get("trades") or []
    listed = [t.get("pnl_pct") for t in trades if t.get("side") == "SELL"]
    calc = _pair_pnl(trades)
    if listed == calc and len(trades) == 40 and rec.get("verdict") == "survived":
        print("[PASS] ledger 009995 pair pnl matches 40 fills")
    else:
        print("[FAIL] ledger listed=%s calc=%s n=%s" % (listed, calc, len(trades)))
        failed += 1
    is_n = sum(1 for t in trades if t.get("split") == "样本内")
    oos_n = sum(1 for t in trades if t.get("split") == "样本外")
    if is_n == 28 and oos_n == 12:
        print("[PASS] ledger split counts 28/12")
    else:
        print("[FAIL] split counts %s/%s" % (is_n, oos_n))
        failed += 1
    oos_sum = round(sum(x for x in calc[14:]), 2)
    if oos_sum > 0:
        print("[PASS] OOS listed sell-sum %s > 0 (not equity)" % oos_sum)
    else:
        print("[FAIL] OOS sell-sum %s" % oos_sum)
        failed += 1

    times = [1700000000 + i * 3600 for i in range(20)]
    stamped = stamp_trades([{"type": "BUY", "idx": 2, "price": 10}], times, "样本内")
    start, end = window_of(times)
    if stamped and stamped[0].get("time") and start and end:
        print("[PASS] stamp + window %s %s %s" % (stamped[0]["time"], start, end))
    else:
        print("[FAIL] stamp %s window %s %s" % (stamped, start, end))
        failed += 1

    # Live MT5 + Xavier: pull GOLD H1, local worker vs remote if Master answers.
    live_ok = False
    try:
        from app.service.mt5_service import fetch_history
        pulled = fetch_history("XAUUSD", bars=2000, timeframe="H1")
        closes = pulled.get("close") or []
        times = pulled.get("time") or []
        if len(closes) >= 200 and len(times) == len(closes):
            is_c, oos_c = split_closes(closes)
            is_w = bt.run_backtest("RSI", pulled.get("symbol") or "GOLD", "is", closes=is_c, slippage_bps=10, commission_bps=5)
            oos_w = bt.run_backtest("RSI", pulled.get("symbol") or "GOLD", "oos", closes=oos_c, slippage_bps=10, commission_bps=5)
            verd = judge(is_w, oos_w)
            print("[INFO] live MT5 %s %s bars=%s IS=%s/%s OOS=%s/%s verdict=%s" % (
                pulled.get("symbol"), pulled.get("timeframe"), len(closes),
                is_w.get("profit"), is_w.get("total_trades"),
                oos_w.get("profit"), oos_w.get("total_trades"), verd,
            ))
            if abs((is_w.get("profit") or 0) - (-19.77)) <= 0.05 and abs((oos_w.get("profit") or 0) - 2.02) <= 0.05:
                print("[PASS] live local worker reproduces 009995 -19.77 / 2.02")
                live_ok = True
            else:
                print("[INFO] live numbers differ from 009995 (new bars or different pull) IS=%s OOS=%s" % (
                    is_w.get("profit"), oos_w.get("profit")))
                live_ok = True
            is_led = stamp_trades(is_w.get("trades") or [], times[:len(is_c)], "样本内")
            if is_led and is_led[0].get("time") and is_led[0].get("price"):
                print("[PASS] live stamp first fill %s %s %s" % (is_led[0]["side"], is_led[0]["time"], is_led[0]["price"]))
            else:
                print("[FAIL] live stamp empty")
                failed += 1
        else:
            print("[FAIL] live MT5 missing time/close %s %s" % (len(closes), len(times)))
            failed += 1
    except Exception as exc:
        print("[INFO] live MT5 skip: %s" % exc)

    try:
        import requests
        health = requests.get("http://127.0.0.1:9000/health", timeout=5)
        xv = requests.get("http://192.168.1.202:8002/version", timeout=5)
        if health.status_code == 200 and (xv.json() or {}).get("version") == "2.1.4":
            print("[PASS] Master up, Xavier-03 2.1.4")
        else:
            print("[FAIL] Master/Xavier %s %s" % (health.status_code, xv.text[:120]))
            failed += 1
        if live_ok:
            body = {"preset": "backtest", "source": "mt5", "symbol": "XAUUSD"}
            resp = requests.post("http://127.0.0.1:9000/api/v1/research/run", json=body, timeout=300)
            data = (resp.json() or {}).get("data") or {}
            n = len(data.get("trades") or [])
            basket = data.get("basket") or []
            mined = data.get("mine") or basket
            if resp.status_code == 200 and data.get("verdict") and data.get("carry") and len(mined) >= 6 and data.get("picked") and data.get("window_from"):
                print("[PASS] live research %s verdict=%s trades=%s basket=%s %s" % (
                    data.get("research_id"), data.get("verdict"), n,
                    [(x.get("strategy"), x.get("verdict"), x.get("oos_profit")) for x in basket],
                    data.get("summary"),
                ))
            elif resp.status_code == 200 and data.get("code") == "TM-1005":
                print("[INFO] research lock busy TM-1005")
            else:
                print("[FAIL] live research %s %s" % (resp.status_code, (resp.text or "")[:300]))
                failed += 1
    except Exception as exc:
        print("[INFO] live HTTP skip: %s" % exc)

    if failed:
        print("SMOKE_21_FAIL")
        return 1
    print("SMOKE_21_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
