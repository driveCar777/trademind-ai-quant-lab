"""A_SHARE_TRANSACTION_COST_MODEL_V1. Not MT5 5bp+10bp."""
from __future__ import print_function

from research_engine.cn_a_share_alpha import STAMP_CUT

COMMISSION = 0.00025
TRANSFER = 0.00001
SLIPPAGE = 0.0010
STAMP_OLD = 0.0010
STAMP_NEW = 0.0005


def stamp_duty_sell(trade_date):
    if trade_date >= STAMP_CUT:
        return STAMP_NEW
    return STAMP_OLD


def buy_cost(trade_date):
    return COMMISSION + TRANSFER + SLIPPAGE


def sell_cost(trade_date):
    return COMMISSION + TRANSFER + SLIPPAGE + stamp_duty_sell(trade_date)


def round_trip_cost(entry_date, exit_date):
    return buy_cost(entry_date) + sell_cost(exit_date)


def stress_mult(cost, slip, cost_k, slip_k):
    base_fees = cost - SLIPPAGE * (2.0 if cost >= 2.0 * SLIPPAGE else 1.0)
    # Explicit: scale commission/stamp/transfer by cost_k and slippage by slip_k.
    return {
        "commission": COMMISSION * cost_k,
        "transfer": TRANSFER * cost_k,
        "stamp_scale": cost_k,
        "slippage": SLIPPAGE * slip_k,
        "note": "stress cost x%s slip x%s" % (cost_k, slip_k),
    }
