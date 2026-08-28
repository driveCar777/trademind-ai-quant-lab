"""Smoke: V11 walk-forward judge + worker uses real close. No live order_send."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DASH = os.path.join(ROOT, "dashboard", "index.html")


def main():
    os.environ["TRADEMIND_MT5_SEND"] = "0"
    failed = 0
    with open(DASH, encoding="utf-8") as fh:
        html = fh.read()
    if "function startGoldWf(" in html and "黄金 MT5 证伪回测" in html and "黄金CSV样本" in html and "function renderLedger(" in html:
        print("[PASS] dashboard has walk-forward chip")
    else:
        print("[FAIL] dashboard missing walk-forward")
        failed += 1

    sys.path.insert(0, os.path.join(ROOT, "master", "api"))
    from app.service.walkforward_service import judge, split_closes, payload_for
    from app.service.exceptions import WorkerNotFoundError
    from app.service import research_service

    closes = [100.0 + i * 0.1 for i in range(250)]
    is_c, oos_c = split_closes(closes)
    if len(is_c) == 175 and len(oos_c) == 75:
        print("[PASS] split 70/30")
    else:
        print("[FAIL] split %s %s" % (len(is_c), len(oos_c)))
        failed += 1

    if judge({"total_trades": 8, "max_drawdown": 10, "profit": 5}, {"total_trades": 6, "max_drawdown": 12, "profit": -1}) == "falsified":
        print("[PASS] oos loss falsified")
    else:
        print("[FAIL] falsified")
        failed += 1
    if judge({"total_trades": 8, "max_drawdown": 30, "profit": 5}, {"total_trades": 6, "max_drawdown": 10, "profit": 2}) == "risk_fail":
        print("[PASS] drawdown risk_fail")
    else:
        print("[FAIL] risk_fail")
        failed += 1
    if judge({"total_trades": 2, "max_drawdown": 5, "profit": 5}, {"total_trades": 6, "max_drawdown": 5, "profit": 2}) == "insufficient":
        print("[PASS] few trades insufficient")
    else:
        print("[FAIL] insufficient")
        failed += 1
    if judge({"total_trades": 8, "max_drawdown": 10, "profit": 5}, {"total_trades": 6, "max_drawdown": 8, "profit": 1.2}) == "survived":
        print("[PASS] survived is not a promise")
    else:
        print("[FAIL] survived")
        failed += 1

    sys.path.insert(0, os.path.join(ROOT, "backtest-worker-v1"))
    import server as bt

    up = [10.0 + i * 0.2 for i in range(80)]
    down = [30.0 - i * 0.15 for i in range(80)]
    a = bt.run_backtest("RSI", "GOLD", "mt5-is", closes=up, slippage_bps=10, commission_bps=5)
    b = bt.run_backtest("RSI", "GOLD", "mt5-is", closes=down, slippage_bps=10, commission_bps=5)
    if "error" not in a and "error" not in b and a.get("profit") != b.get("profit"):
        print("[PASS] worker uses supplied close")
    else:
        print("[FAIL] worker close a=%s b=%s" % (a, b))
        failed += 1

    syn = bt.run_backtest("RSI", "GOLD", "2025-01-01", slippage_bps=0, commission_bps=0)
    if "error" not in syn and "profit" in syn:
        print("[PASS] worker synthetic path still works")
    else:
        print("[FAIL] synthetic %s" % syn)
        failed += 1

    body = payload_for("GOLD", up, "is", cut=40, strategy="RSI")
    if body.get("strategy") == "RSI" and body.get("close") == up and body.get("slippage_bps") == 10 and body.get("cut") == 40:
        print("[PASS] payload carries close + costs")
    else:
        print("[FAIL] payload %s" % body)
        failed += 1

    try:
        research_service.run_research("factor", source="mt5", symbol="XAUUSD")
        print("[FAIL] factor+mt5 allowed")
        failed += 1
    except WorkerNotFoundError:
        print("[PASS] mt5+factor still TM-1001")

    from app.service.research_service import context_for_ai
    from app.service.walkforward_service import describe

    wf_result = {
        "strategy": "RSI",
        "symbol": "GOLD",
        "profit": 2.02,
        "max_drawdown": 3.37,
        "win_rate": 66.7,
        "total_trades": 12,
        "sharpe_ratio": -0.46,
        "profit_factor": 2.34,
        "verdict": "survived",
        "is_profit": -19.77,
        "oos_profit": 2.02,
        "is_drawdown": 19.83,
        "oos_drawdown": 3.37,
        "is_trades": 28,
        "oos_trades": 12,
        "bars": 2000,
        "timeframe": "H1",
    }
    csv_ctx = context_for_ai("backtest", {
        "strategy": "RSI",
        "symbol": "XAUUSD",
        "profit": -12.3,
        "max_drawdown": 12.3,
        "win_rate": 40.0,
        "total_trades": 8,
        "sharpe_ratio": -0.2,
        "profit_factor": 0.8,
    })
    csv_inner = (csv_ctx or {}).get("result") or {}
    if csv_inner.get("total_trades") == 8 and csv_inner.get("profit") == -12.3:
        print("[PASS] white-box CSV backtest also nests result")
    else:
        print("[FAIL] CSV context %s" % csv_ctx)
        failed += 1

    ctx = context_for_ai("backtest", wf_result)
    nested = (ctx or {}).get("result") or {}
    if nested.get("total_trades") == 12 and nested.get("profit") == 2.02:
        print("[PASS] white-box AI context nests result trades")
    else:
        print("[FAIL] AI context %s" % ctx)
        failed += 1
    if ((ctx or {}).get("result") or {}).get("total_trades", 0) == 0:
        print("[FAIL] gateway would still see 0 trades")
        failed += 1
    text = describe(wf_result)
    if "28" in text and "12" in text and "没有任何交易" not in text and "-19.77" in text:
        print("[PASS] white-box describe uses real trade counts")
    else:
        print("[FAIL] describe %s" % text)
        failed += 1

    # Reproduce the old bug: gateway only reads context["result"].
    ghost = (wf_result.get("result") or {})
    if ghost.get("total_trades", 0) == 0:
        print("[PASS] white-box old flat payload would show 0 trades")
    else:
        print("[FAIL] expected empty nested result on flat payload")
        failed += 1

    sys.path.insert(0, os.path.join(ROOT, "ai-gateway"))
    from prompts import STRATEGY_DESCRIBE_TEMPLATE, dict_to_text

    prompt = STRATEGY_DESCRIBE_TEMPLATE.format(
        strategy=ctx.get("strategy", "unknown"),
        symbol=ctx.get("symbol", "unknown"),
        params=str(ctx.get("params", {})),
        profit=nested.get("profit", 0),
        max_drawdown=nested.get("max_drawdown", 0),
        win_rate=nested.get("win_rate", 0),
        total_trades=nested.get("total_trades", 0),
        sharpe_ratio=nested.get("sharpe_ratio", 0),
        profit_factor=nested.get("profit_factor", 0),
        benchmark_text=dict_to_text(ctx.get("benchmark", {})),
    )
    if "12" in prompt and "2.02" in prompt and "28" in prompt and "survived" in prompt:
        print("[PASS] white-box gateway prompt has 12/28 trades")
    else:
        print("[FAIL] gateway prompt %s" % prompt[:400])
        failed += 1
    research_src = open(
        os.path.join(ROOT, "master", "api", "app", "service", "research_service.py"),
        encoding="utf-8",
    ).read()
    if 'if last.get("verdict"):' in research_src and "wf_describe" in research_src:
        print("[PASS] white-box walk-forward skips LLM")
    else:
        print("[FAIL] research still asks LLM for verdict")
        failed += 1

    src = open(os.path.join(ROOT, "backtest-worker-v1", "server.py"), encoding="utf-8").read()
    if "closes=None" in src and 'VERSION = "2.1.4"' in src and "REGIME_SWITCH" in src:
        print("[PASS] worker 2.1.4 has regime switch")
    else:
        print("[FAIL] worker missing close/trades hook")
        failed += 1

    from app.service.walkforward_service import stamp_trades, window_of

    wave = [2000.0]
    for _i in range(40):
        wave.append(wave[-1] * 0.97)
    for _i in range(40):
        wave.append(wave[-1] * 1.03)
    led = bt.run_backtest("RSI", "GOLD", "mt5-is", closes=wave, slippage_bps=10, commission_bps=5)
    fills = led.get("trades") or []
    if fills and fills[0].get("idx") is not None and fills[0].get("price") and fills[0].get("type") in ("BUY", "SELL"):
        print("[PASS] white-box RSI returns idx/price fills")
    else:
        print("[FAIL] RSI trades %s" % fills[:3])
        failed += 1
    times = [1700000000 + i * 3600 for i in range(len(wave))]
    stamped = stamp_trades(fills, times, "样本内")
    if stamped and stamped[0].get("time") and stamped[0].get("price"):
        print("[PASS] white-box stamp_trades maps idx to time")
    else:
        print("[FAIL] stamped %s" % stamped[:2])
        failed += 1
    start, end = window_of(times)
    if start.startswith("2023-") and end:
        print("[PASS] white-box window_of %s %s" % (start, end))
    else:
        print("[FAIL] window %s %s" % (start, end))
        failed += 1
    mt5_src = open(os.path.join(ROOT, "master", "api", "app", "service", "mt5_service.py"), encoding="utf-8").read()
    if 'row["time"]' in mt5_src and '"time": times' in mt5_src:
        print("[PASS] MT5 copy keeps bar time")
    else:
        print("[FAIL] copy_closes still drops time")
        failed += 1

    if failed:
        print("SMOKE_20_FAIL")
        return 1
    print("SMOKE_20_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
