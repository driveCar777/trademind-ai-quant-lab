"""Rebuild trade ledger fields from bars + V0.6 fills. EXECUTION_APPROXIMATION."""
from __future__ import print_function

from research_engine.profit.cost.model import commission, fill_price, slip_price, spread_price


def bar_time(bar):
    if not bar:
        return ""
    return bar.get("timestamp_utc") or bar.get("date") or ""


def enrich_path_trade(bars, trade, side=None):
    entry_i = trade.get("entry_index")
    exit_i = trade.get("exit_index")
    side = side if side is not None else trade.get("side")
    entry_bar = bars[entry_i] if bars and entry_i is not None and entry_i < len(bars) else None
    exit_bar = bars[exit_i] if bars and exit_i is not None and exit_i < len(bars) else None
    entry_fill = trade.get("entry_px") or trade.get("entry")
    exit_fill = trade.get("exit_px") or trade.get("exit")
    if entry_fill is None and entry_bar is not None and side:
        entry_fill = fill_price(entry_bar, side, False)
    if exit_fill is None and exit_bar is not None and side:
        if trade.get("reason") == "STOP" or trade.get("stopped"):
            exit_fill = trade.get("exit") or (exit_bar.get("open") if exit_bar else None)
        else:
            exit_fill = fill_price(exit_bar, side, True)
    qty = trade.get("qty")
    notional = trade.get("notional")
    if qty is None and notional and entry_fill:
        qty = abs(float(notional)) / float(entry_fill)
    if qty is None:
        qty = 0.0
    entry_open = (entry_bar or {}).get("open")
    exit_open = (exit_bar or {}).get("open")
    half_in = spread_price(entry_bar) / 2.0 if entry_bar else 0.0
    half_out = spread_price(exit_bar) / 2.0 if exit_bar else 0.0
    slip_in = slip_price(entry_open) if entry_open is not None else 0.0
    slip_out = slip_price(exit_open) if exit_open is not None else 0.0
    comm_in = commission(qty * float(entry_fill)) if entry_fill else 0.0
    comm_out = commission(qty * float(exit_fill)) if exit_fill else 0.0
    gross = None
    if entry_open is not None and exit_open is not None and side:
        gross = qty * (float(exit_open) - float(entry_open)) * float(side)
    net = trade.get("pnl")
    if net is None and entry_fill is not None and exit_fill is not None and side:
        net = qty * (float(exit_fill) - float(entry_fill)) * float(side) - comm_in - comm_out
    out = dict(trade)
    out["entry_time"] = bar_time(entry_bar) or trade.get("date") or ""
    out["exit_time"] = bar_time(exit_bar) or ""
    out["entry_price"] = entry_fill
    out["exit_price"] = exit_fill
    out["side"] = side
    out["gross_pnl"] = gross
    out["spread_cost"] = qty * (half_in + half_out)
    out["slippage"] = qty * (slip_in + slip_out)
    out["commission"] = comm_in + comm_out
    out["net_pnl"] = net
    out["holding_bars"] = None if entry_i is None or exit_i is None else exit_i - entry_i
    return out


def enrich_family_trade(trade):
    out = dict(trade)
    out["entry_time"] = trade.get("date") or trade.get("entry_time") or ""
    out["exit_time"] = trade.get("exit_time") or ""
    out["entry_price"] = trade.get("entry") or trade.get("entry_price")
    out["exit_price"] = trade.get("exit") or trade.get("exit_price")
    out["side"] = trade.get("side")
    out["gross_pnl"] = trade.get("gross_pnl")
    out["spread_cost"] = trade.get("spread_cost")
    out["commission"] = trade.get("commission")
    out["slippage"] = trade.get("slippage")
    out["net_pnl"] = trade.get("net_pnl")
    if out["net_pnl"] is None:
        out["net_pnl"] = trade.get("pnl")
    return out
