"""Cost arithmetic + minimum commission tests (§32). Values are exact per cost.py constants."""
from __future__ import print_function

from research_engine.cn_a_short.cost import (COMMISSION, MIN_FEE, round_trip, buy_cost_yuan,
                                             sell_cost_yuan, min_fee_breakeven_notional, stamp_duty_sell)

DAY = "2026-01-01"  # current stamp regime (0.0005)


def test_min_fee_breakeven_notional():
    assert abs(min_fee_breakeven_notional() - MIN_FEE / COMMISSION) < 1e-9
    assert abs(min_fee_breakeven_notional() - 20_000.0) < 1e-6


def test_small_order_round_trip_fee_only():
    # P=2000: buy_comm=5, sell_comm=5, transfer=2*0.02=0.04, stamp=2000*0.0005=1.0 -> 11.04
    rt = round_trip(2_000, day=DAY, slip_side=0.0)
    assert abs(rt["fee_only_yuan"] - 11.04) < 1e-6
    assert abs(rt["fee_only_pct"] - 0.00552) < 1e-9
    assert rt["min_fee_binding"] is True
    assert rt["slippage_yuan"] == 0.0


def test_large_order_round_trip_fee_only():
    # P=20000: comm 5+5, transfer 0.4, stamp 10 -> 20.4 ; min fee NOT binding at exactly 20000
    rt = round_trip(20_000, day=DAY, slip_side=0.0)
    assert abs(rt["fee_only_yuan"] - 20.4) < 1e-6
    assert abs(rt["fee_only_pct"] - 0.00102) < 1e-9
    assert rt["min_fee_binding"] is False


def test_slippage_adds_two_sides():
    P = 20_000
    rt0 = round_trip(P, day=DAY, slip_side=0.0)
    rt1 = round_trip(P, day=DAY, slip_side=0.001)
    assert abs((rt1["total_yuan"] - rt0["total_yuan"]) - 2 * P * 0.001) < 1e-6
    assert abs(rt1["total_pct"] - (rt0["fee_only_pct"] + 0.002)) < 1e-9


def test_stamp_is_sell_side_only():
    P = 50_000
    buy = buy_cost_yuan(P, slip_side=0.0)
    sell = sell_cost_yuan(P, day=DAY, slip_side=0.0)
    assert abs((sell - buy) - P * stamp_duty_sell(DAY)) < 1e-6


def test_cost_pct_monotone_decreasing_until_breakeven():
    pcts = [round_trip(P, day=DAY, slip_side=0.0)["fee_only_pct"] for P in (2_000, 5_000, 10_000, 20_000)]
    assert pcts[0] > pcts[1] > pcts[2] > pcts[3]
    # beyond breakeven cost% is flat (min fee no longer binds)
    assert abs(round_trip(20_000, day=DAY, slip_side=0.0)["fee_only_pct"]
               - round_trip(100_000, day=DAY, slip_side=0.0)["fee_only_pct"]) < 1e-12
