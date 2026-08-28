"""qty = risk_frac * equity / stop_distance, then cap notional at equity * LEVERAGE_CAP."""
from __future__ import print_function

from research_engine.profit import LEVERAGE_CAP, STOP_ATR_MULT
from research_protocol.causal import CausalView
from research_protocol.features import atr_at


def stop_distance(bars, signal_t, entry_px):
    view = CausalView(bars, signal_t)
    atr = atr_at(view, 14)
    if atr is None or atr <= 0 or entry_px is None:
        return None
    return STOP_ATR_MULT * float(atr)


def position_qty(equity, risk_frac, entry_px, stop_dist):
    if equity is None or equity <= 0 or risk_frac is None or risk_frac <= 0:
        return 0.0
    if entry_px is None or entry_px <= 0 or stop_dist is None or stop_dist <= 0:
        return 0.0
    raw = (float(equity) * float(risk_frac)) / float(stop_dist)
    max_qty = (float(equity) * LEVERAGE_CAP) / float(entry_px)
    if raw > max_qty:
        return max_qty
    return raw
