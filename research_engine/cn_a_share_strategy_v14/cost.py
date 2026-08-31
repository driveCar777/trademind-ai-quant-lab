"""A_SHARE_STRATEGY_COST_MODEL_V1. Locked rates from the V13 contract. Not MT5."""
from __future__ import print_function

from research_engine.cn_a_share_strategy_v14 import STAMP_CUT

COST_ID = "A_SHARE_STRATEGY_COST_MODEL_V1"
COMMISSION = 0.00025
TRANSFER = 0.00001
SLIPPAGE = 0.0010
STAMP_OLD = 0.0010
STAMP_NEW = 0.0005

UNKNOWN = (
    "minimum_commission_5cny_per_side",
    "lot_size_100_roundlot",
    "sz_transfer_fee_applicability",
    "bid_ask_spread_observed",
    "stamp_duty_on_non_equity",
)

EXECUTION_APPROXIMATION = "No bid/ask. Slippage is the locked 10bp contract approximation."


def stamp_duty_sell(trade_date):
    if trade_date >= STAMP_CUT:
        return STAMP_NEW
    return STAMP_OLD


def buy_rate(cost_k=1.0, slip_k=1.0):
    return (COMMISSION + TRANSFER) * cost_k + SLIPPAGE * slip_k


def sell_rate(trade_date, cost_k=1.0, slip_k=1.0):
    return (COMMISSION + TRANSFER) * cost_k + SLIPPAGE * slip_k + stamp_duty_sell(trade_date) * cost_k


def cost_model_record():
    return {
        "id": COST_ID,
        "parent": "A_SHARE_TRANSACTION_COST_MODEL_V1",
        "commission": COMMISSION,
        "transfer": TRANSFER,
        "slippage": SLIPPAGE,
        "stamp_before_20230828": STAMP_OLD,
        "stamp_from_20230828": STAMP_NEW,
        "stamp_side": "SELL_ONLY",
        "not": "MT5_5BP_10BP",
        "unknown": list(UNKNOWN),
        "execution_approximation": EXECUTION_APPROXIMATION,
        "note": "Rates locked. Do not search a cheaper model.",
    }
