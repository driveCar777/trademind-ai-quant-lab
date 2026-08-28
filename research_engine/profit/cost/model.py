"""NEXT_BAR_OPEN fills with spread, commission, slippage. Close fills forbidden."""
from __future__ import print_function

from research_engine.profit import COMMISSION_BP, SLIPPAGE_BP


def spread_price(bar):
    close = bar.get("close")
    spr = bar.get("spread")
    if close is None or close <= 0 or spr is None:
        return 0.0
    close = float(close)
    spr = float(spr)
    if close >= 10.0:
        return spr * 0.01
    return spr * 0.00001


def slip_price(open_px):
    if open_px is None:
        return 0.0
    return (SLIPPAGE_BP / 10000.0) * float(open_px)


def fill_price(bar, side, is_exit):
    """side +1 long, -1 short. is_exit True uses the opposite adverse adjustment."""
    open_px = bar.get("open")
    if open_px is None:
        return None
    open_px = float(open_px)
    half = spread_price(bar) / 2.0
    slip = slip_price(open_px)
    adverse = half + slip
    if side > 0:
        return open_px + adverse if not is_exit else open_px - adverse
    return open_px - adverse if not is_exit else open_px + adverse


def commission(notional):
    if notional is None:
        return 0.0
    return abs(float(notional)) * (COMMISSION_BP / 10000.0)
