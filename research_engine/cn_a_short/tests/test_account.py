"""Account feasibility + lot size + no-negative-cash tests (§32)."""
from __future__ import print_function

import pytest

from research_engine.cn_a_short.account import (buy_cash_out, feasible_portfolio, lots_affordable,
                                                lots_for, lot_cost_yuan, min_capital_for_k,
                                                practical_min_capital_for_k)


def test_lot_size_floor_notional_only():
    # lots_for is notional/share-cost only (documented: NOT an affordability test).
    assert lots_for(10_000, 20) == 5          # 100*20=2000 per lot; 10000//2000=5
    assert lots_for(1_999, 20) == 0           # cannot afford one lot's shares
    assert lot_cost_yuan(20) == 2_000.0


def test_lots_affordable_is_fee_aware():
    # §A / §D.1: ¥2,000 cannot afford a ¥2,000 lot once the ¥5 min commission is included.
    assert lots_affordable(2_000, 20, slip_side=0.0) == 0
    # Just enough to cover shares + ¥5 commission + transfer -> 1 lot.
    assert buy_cash_out(2_000) == pytest.approx(2_005.02, abs=1e-6)
    assert lots_affordable(2_006, 20, slip_side=0.0) == 1
    # Contrast with the (fee-blind) notional floor which wrongly says affordable:
    assert lots_for(2_000, 20, slip_side=0.0) == 1


def test_actual_cash_out_never_exceeds_alloc():
    # §D.3: high price + small allocation; whatever lots_affordable returns, cash out fits alloc.
    for alloc, price in [(2_000, 20), (10_000, 100), (20_000, 20), (9_999, 100)]:
        L = lots_affordable(alloc, price, slip_side=0.001)
        notional = L * 100 * price * 1.001
        assert buy_cash_out(notional) <= alloc + 1e-9


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


def test_small_account_fee_aware_threshold_and_worst_cost_band():
    # §A fix: ¥2,000 can NOT afford one ¥2,000 lot once the ¥5 commission is included.
    infeasible = feasible_portfolio(2_000, 20, 1, exposure=1.0, slip_side=0.0)
    assert infeasible["feasible"] is False
    assert infeasible["invested"] == 0.0
    assert infeasible["cash_after_fees"] == 2_000        # nothing bought -> full cash
    # ¥2,010 (covers shares + ¥5 fee + transfer) -> feasible, worst cost band (min fee binds, >0.5% RT)
    fp = feasible_portfolio(2_010, 20, 1, exposure=1.0, slip_side=0.0)
    assert fp["feasible"] is True
    assert fp["per_name_notional"] == 2_000
    assert fp["min_fee_binding"] is True
    assert fp["rt_cost_pct_total"] > 0.005
    assert fp["cash_out_incl_fees"] <= 2_010 + 1e-6       # true cash out fits equity


def test_feasible_portfolio_true_cash_non_negative():
    # §D.2: multi-name; true cash out (incl fees) must fit strategy budget, cash never negative.
    for equity, price, k in [(50_000, 20, 10), (100_000, 50, 5), (20_000, 10, 3)]:
        fp = feasible_portfolio(equity, price, k, exposure=1.0, slip_side=0.001)
        if fp["feasible"]:
            assert fp["cash_out_incl_fees"] <= equity + 1e-6
            assert fp["cash_after_fees"] >= -1e-6


@pytest.mark.parametrize("equity", [2_000, 5_000, 20_000, 100_000, 1_000_000])
def test_invariants_across_account_sizes(equity):
    fp = feasible_portfolio(equity, 20, 5, exposure=0.8, slip_side=0.001)
    assert fp["invested"] <= equity * 0.8 + 1e-6      # respects exposure budget
    assert fp["invested"] <= equity                    # never exceeds equity (no negative cash)
