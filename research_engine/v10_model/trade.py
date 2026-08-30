"""Thresholded NEXT_BAR_OPEN conversion. Thresholds pre-registered."""
from __future__ import print_function

from research_engine.profit import START_EQUITY
from research_engine.profit.cost.model import commission, fill_price, slip_price, spread_price
from research_engine.profit.risk.sizing import position_qty, stop_distance
from research_engine.strategy.contract import assert_no_final_oos
from research_engine.v10_model import HOLD_BARS, PRIMARY_THRESHOLD
from research_engine.v9_master.metrics_v9 import extend_metrics


def proba_to_side(p, threshold=PRIMARY_THRESHOLD):
    if p is None:
        return 0
    if p > threshold:
        return 1
    if p < (1.0 - threshold):
        return -1
    return 0


def replay_sides(bars, sides, holding, risk_frac, role, start_equity=START_EQUITY):
    assert_no_final_oos(role)
    cash = float(start_equity)
    pos = None
    pending = None
    trades = []
    curve = []
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
                half = spread_price(bar) / 2.0
                slip = slip_price(bar.get("open"))
                cash -= fee
                stop_px = entry_px - dist if side > 0 else entry_px + dist
                pos = {
                    "side": side,
                    "qty": qty,
                    "entry_px": entry_px,
                    "entry_open": bar.get("open"),
                    "stop_px": stop_px,
                    "entry_index": t,
                    "exit_index": t + holding,
                    "notional": notional,
                    "entry_spread": half * qty,
                    "entry_slip": slip * qty,
                    "entry_fee": fee,
                    "signal_t": pending["signal_t"],
                }
            pending = None
        if pos is not None and t == pos["exit_index"] and t != pos["entry_index"]:
            px = fill_price(bar, pos["side"], True)
            if px is not None:
                pnl_gross = pos["qty"] * (px - pos["entry_px"]) * pos["side"]
                fee = commission(pos["qty"] * px)
                half = spread_price(bar) / 2.0
                slip = slip_price(bar.get("open"))
                cash = cash + pnl_gross - fee
                trades.append(
                    {
                        "signal_t": pos["signal_t"],
                        "entry_index": pos["entry_index"],
                        "exit_index": t,
                        "entry_time": (bars[pos["entry_index"]] or {}).get("timestamp_utc"),
                        "exit_time": bar.get("timestamp_utc"),
                        "entry_price": pos["entry_px"],
                        "exit_price": px,
                        "side": pos["side"],
                        "gross_pnl": pnl_gross,
                        "spread_cost": pos["entry_spread"] + half * pos["qty"],
                        "commission": pos["entry_fee"] + fee,
                        "slippage": pos["entry_slip"] + slip * pos["qty"],
                        "net_pnl": pnl_gross - fee,
                        "pnl": pnl_gross - fee,
                        "notional": pos["notional"],
                        "holding_bars": t - pos["entry_index"],
                        "reason": "TIME",
                    }
                )
                pos = None
        elif pos is not None:
            op = bar.get("open")
            hi = bar.get("high")
            lo = bar.get("low")
            hit = None
            if op is not None and hi is not None and lo is not None:
                if pos["side"] > 0 and lo <= pos["stop_px"]:
                    hit = op if op < pos["stop_px"] else pos["stop_px"]
                elif pos["side"] < 0 and hi >= pos["stop_px"]:
                    hit = op if op > pos["stop_px"] else pos["stop_px"]
            if hit is not None:
                pnl_gross = pos["qty"] * (hit - pos["entry_px"]) * pos["side"]
                fee = commission(pos["qty"] * hit)
                cash = cash + pnl_gross - fee
                trades.append(
                    {
                        "signal_t": pos["signal_t"],
                        "entry_index": pos["entry_index"],
                        "exit_index": t,
                        "entry_time": (bars[pos["entry_index"]] or {}).get("timestamp_utc"),
                        "exit_time": bar.get("timestamp_utc"),
                        "entry_price": pos["entry_px"],
                        "exit_price": hit,
                        "side": pos["side"],
                        "gross_pnl": pnl_gross,
                        "spread_cost": pos["entry_spread"],
                        "commission": pos["entry_fee"] + fee,
                        "slippage": pos["entry_slip"],
                        "net_pnl": pnl_gross - fee,
                        "pnl": pnl_gross - fee,
                        "notional": pos["notional"],
                        "holding_bars": t - pos["entry_index"],
                        "reason": "STOP",
                    }
                )
                pos = None
        if pos is None and pending is None and holding > 0 and t + 1 + holding < n:
            if bars[t].get("role") == role:
                side = sides[t] if t < len(sides) else 0
                if side:
                    dist = stop_distance(bars, t, bars[t + 1].get("open") if t + 1 < n else None)
                    if dist is not None:
                        pending = {"entry_index": t + 1, "side": side, "signal_t": t, "stop_dist": dist}
        mark = 0.0
        if pos is not None and bar.get("close") is not None:
            mark = pos["qty"] * (float(bar["close"]) - pos["entry_px"]) * pos["side"]
        equity = cash + mark
        if equity < 0:
            equity = 0.0
        curve.append(equity)
        t += 1
    metrics = extend_metrics(curve, "D1", start_equity, trades, bars)
    metrics["role"] = role
    metrics["trade_count"] = len(trades)
    return {"metrics": metrics, "trades": trades, "equity_curve": curve}


def sides_from_proba(proba, threshold, rows, role):
    sides = []
    i = 0
    while i < len(rows):
        if rows[i].get("role") != role:
            sides.append(0)
        else:
            sides.append(proba_to_side(proba[i], threshold))
        i += 1
    return sides


def momentum_sides(rows, role):
    sides = []
    i = 0
    while i < len(rows):
        if rows[i].get("role") != role:
            sides.append(0)
        else:
            r = rows[i].get("ret20")
            if r is None or r == 0:
                sides.append(0)
            elif r > 0:
                sides.append(1)
            else:
                sides.append(-1)
        i += 1
    return sides


def buyhold_sides(rows, role):
    sides = []
    i = 0
    while i < len(rows):
        sides.append(1 if rows[i].get("role") == role else 0)
        i += 1
    return sides


def hold_for(target_id):
    return int(HOLD_BARS[target_id])
