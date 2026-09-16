"""A-Short cost model = thin wrapper over the CANONICAL A-share cost model. Not reinvented.

Canonical source (single source of truth):
  research_engine/cn_a_share_alpha/cost.py        COMMISSION/TRANSFER/SLIPPAGE/STAMP, stamp_duty_sell()
  research_engine/cn_a_share_ml_v25/top_n_book.py MIN_FEE=5.0, LOT=100, _fee(notional)

This module ONLY adds: per-order-notional round-trip decomposition (fee-only vs fee+slippage),
honoring the ¥5 minimum commission, so cost is computed per ACTUAL order size, not as a single flat %.
"""
from __future__ import print_function

from research_engine.cn_a_share_alpha.cost import COMMISSION, SLIPPAGE, TRANSFER, stamp_duty_sell
from research_engine.cn_a_share_ml_v25.top_n_book import LOT, MIN_FEE, _fee

# Default modelled stamp cut date is handled by stamp_duty_sell(day). Post-2023-08-28 = 0.0005.
DEFAULT_DAY = "2026-01-01"   # >= STAMP_CUT, so stamp = 0.0005 (current regime) unless a day is passed.


def commission_yuan(notional):
    """max(MIN_FEE, notional*COMMISSION). The ¥5 floor is what kills small orders."""
    return max(MIN_FEE, notional * COMMISSION)


def buy_cost_yuan(notional, slip_side=SLIPPAGE):
    """Buy-side cost in yuan on a given order notional: commission(floored)+transfer+slippage."""
    return commission_yuan(notional) + notional * TRANSFER + notional * slip_side


def sell_cost_yuan(notional, day=DEFAULT_DAY, slip_side=SLIPPAGE):
    """Sell-side cost in yuan: commission(floored)+transfer+stamp(sell only)+slippage."""
    return commission_yuan(notional) + notional * TRANSFER + notional * stamp_duty_sell(day) + notional * slip_side


def round_trip(notional, day=DEFAULT_DAY, slip_side=SLIPPAGE):
    """Full round-trip cost for one entry+exit at the SAME per-name notional.

    Returns yuan and pct-of-notional, split fee-only vs total (fee+slippage), so callers can
    report both. `slip_side` is a MODEL ASSUMPTION (per side); pass 0.0 for the fee-only floor.
    """
    fee_buy = commission_yuan(notional) + notional * TRANSFER
    fee_sell = commission_yuan(notional) + notional * TRANSFER + notional * stamp_duty_sell(day)
    slip = 2.0 * notional * slip_side
    fee_only = fee_buy + fee_sell
    total = fee_only + slip
    return {
        "notional": notional,
        "min_fee_binding": (notional * COMMISSION) < MIN_FEE,
        "fee_only_yuan": fee_only,
        "fee_only_pct": fee_only / notional if notional else None,
        "slippage_yuan": slip,
        "slip_side_assumed": slip_side,
        "total_yuan": total,
        "total_pct": total / notional if notional else None,
    }


def min_fee_breakeven_notional():
    """Notional at which per-side commission stops being floored by ¥5 (= MIN_FEE/COMMISSION)."""
    return MIN_FEE / COMMISSION


# Re-export canonical constants so downstream reads one place.
__all__ = [
    "COMMISSION", "TRANSFER", "SLIPPAGE", "stamp_duty_sell", "LOT", "MIN_FEE", "_fee",
    "commission_yuan", "buy_cost_yuan", "sell_cost_yuan", "round_trip", "min_fee_breakeven_notional",
]
