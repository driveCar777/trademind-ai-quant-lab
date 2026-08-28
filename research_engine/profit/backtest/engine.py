"""One-position backtest. Signal at t, fill at t+1 open. No close fills."""
from __future__ import print_function

from research_engine.profit import START_EQUITY
from research_engine.profit.backtest.metrics import summarize_equity
from research_engine.profit.cost.model import commission, fill_price
from research_engine.profit.risk.sizing import position_qty, stop_distance
from research_engine.profit.strategy_family.signals import signal_at
from research_engine.strategy.contract import assert_no_final_oos
from research_protocol.windows import window_guard


def _stop_hit(bar, side, stop_px):
    if bar is None or stop_px is None:
        return None
    op = bar.get("open")
    hi = bar.get("high")
    lo = bar.get("low")
    if op is None or hi is None or lo is None:
        return None
    if side > 0:
        if lo <= stop_px:
            return op if op < stop_px else stop_px
        return None
    if hi >= stop_px:
        return op if op > stop_px else stop_px
    return None


def _mark(pos, bar):
    if pos is None or bar is None or bar.get("close") is None:
        return 0.0
    return pos["qty"] * (float(bar["close"]) - pos["entry_px"]) * pos["side"]


def run_backtest(bars, window, role, states, strategy, timeframe, start_equity=START_EQUITY):
    assert_no_final_oos(role)
    family = strategy.get("family")
    holding = int(strategy.get("holding") or 0)
    risk_frac = float((strategy.get("risk") or {}).get("risk_frac") or 0.0)
    cash = float(start_equity)
    pos = None
    pending = None
    trades = []
    curve = []
    cost_paid = 0.0
    t = 0
    n = len(bars)
    while t < n:
        bar = bars[t]
        if pending is not None and pos is None and t == pending["entry_index"]:
            side = pending["side"]
            entry_px = fill_price(bar, side, False)
            dist = pending["stop_dist"]
            qty = position_qty(cash, risk_frac, entry_px, dist)
            if entry_px is not None and qty > 0:
                notional = qty * entry_px
                fee = commission(notional)
                cash -= fee
                cost_paid += fee
                stop_px = entry_px - dist if side > 0 else entry_px + dist
                pos = {
                    "side": side,
                    "qty": qty,
                    "entry_px": entry_px,
                    "stop_px": stop_px,
                    "entry_index": t,
                    "exit_index": t + holding,
                    "notional": notional,
                    "signal_t": pending["signal_t"],
                }
            pending = None
        if pos is not None and t == pos["exit_index"] and t != pos["entry_index"]:
            px = fill_price(bar, pos["side"], True)
            if px is not None:
                pnl = pos["qty"] * (px - pos["entry_px"]) * pos["side"]
                fee = commission(pos["qty"] * px)
                cash = cash + pnl - fee
                cost_paid += fee
                trades.append(
                    {
                        "signal_t": pos["signal_t"],
                        "entry_index": pos["entry_index"],
                        "exit_index": t,
                        "side": pos["side"],
                        "pnl": pnl - fee,
                        "notional": pos["notional"],
                        "reason": "TIME",
                    }
                )
                pos = None
        elif pos is not None:
            hit = _stop_hit(bar, pos["side"], pos["stop_px"])
            if hit is not None:
                pnl = pos["qty"] * (hit - pos["entry_px"]) * pos["side"]
                fee = commission(pos["qty"] * hit)
                cash = cash + pnl - fee
                cost_paid += fee
                trades.append(
                    {
                        "signal_t": pos["signal_t"],
                        "entry_index": pos["entry_index"],
                        "exit_index": t,
                        "side": pos["side"],
                        "pnl": pnl - fee,
                        "notional": pos["notional"],
                        "reason": "STOP",
                    }
                )
                pos = None
        if pos is None and pending is None and family != "DEF" and holding > 0:
            exit_i = t + 1 + holding
            ok, _reason = window_guard(t, exit_i, window, role)
            if ok and exit_i < n and (t + 1) < n:
                st = states[t] if t < len(states) else None
                sig = signal_at(bars, t, st, family)
                if sig != 0:
                    dist = stop_distance(bars, t, bars[t + 1].get("open") if t + 1 < n else None)
                    if dist is not None:
                        pending = {"entry_index": t + 1, "side": sig, "signal_t": t, "stop_dist": dist}
        equity = cash + _mark(pos, bar)
        if equity < 0:
            equity = 0.0
        curve.append(equity)
        t += 1
    metrics = summarize_equity(curve, timeframe, start_equity, trades)
    metrics["cost_paid"] = cost_paid
    metrics["role"] = role
    return {
        "metrics": metrics,
        "trades": trades,
        "equity_curve": curve,
        "equity_end": curve[-1] if curve else start_equity,
        "n_equity": len(curve),
    }
