"""Account feasibility + lot size + no-negative-cash tests (§32)."""
from __future__ import print_function

import pytest

from research_engine.cn_a_short.account import (feasible_portfolio, lots_for, lot_cost_yuan,
                                                min_capital_for_k, practical_min_capital_for_k)


def test_lot_size_floor():
    assert lots_for(10_000, 20) == 5          # 100*20=2000 per lot; 10000//2000=5
    assert lots_for(1_999, 20) == 0           # cannot afford one lot
    assert lot_cost_yuan(20) == 2_000.0


def test_min_capital_matches_example():
    # 10 names, ¥100 stock, 1 lot each, no slip, full exposure -> ¥100,000 (user §9 example)
    assert abs(min_capital_for_k(10, 100, 1.0, 0.0) - 100_000.0) < 1e-6


def test_practical_min_exceeds_theoretical():
    for k in (3, 5, 10):
        for price in (10, 50, 100):
            theo = min_capital_for_k(k, price, 1.0, 0.001)
            prac = practical_min_capital_for_k(k, price, 1.0, 0.001)
            assert prac > theo


def test_feasible_portfolio_never_negative_cash():
    # Small account, expensive stock, many names -> infeasible, but never invests over equity.
    fp = feasible_portfolio(2_000, 100, 10, exposure=1.0, slip_side=0.001)
    assert fp["feasible"] is False
    assert fp["invested"] <= 2_000 + 1e-6
    assert 0.0 <= fp["cash_idle_frac"] <= 1.0


def test_feasible_portfolio_ok_case():
    fp = feasible_portfolio(100_000, 20, 10, exposure=1.0, slip_side=0.0)
    assert fp["feasible"] is True
    assert fp["n_names"] == 10
    assert fp["invested"] <= 100_000 + 1e-6
    assert fp["per_name_notional"] > 0


def test_small_account_forced_into_worst_cost_band():
    # ¥2,000 single name ¥20 stock -> per-name notional ¥2,000 -> min fee binds (>0.5% round trip)
    fp = feasible_portfolio(2_000, 20, 1, exposure=1.0, slip_side=0.0)
    assert fp["feasible"] is True
    assert fp["per_name_notional"] == 2_000
    assert fp["min_fee_binding"] is True
    assert fp["rt_cost_pct_total"] > 0.005


@pytest.mark.parametrize("equity", [2_000, 5_000, 20_000, 100_000, 1_000_000])
def test_invariants_across_account_sizes(equity):
    fp = feasible_portfolio(equity, 20, 5, exposure=0.8, slip_side=0.001)
    assert fp["invested"] <= equity * 0.8 + 1e-6      # respects exposure budget
    assert fp["invested"] <= equity                    # never exceeds equity (no negative cash)
