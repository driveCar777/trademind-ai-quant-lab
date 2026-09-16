"""Account / executability feasibility. Pure arithmetic (no price panel needed).

Answers §7-§9: for a given account equity, stock price, target name count K and exposure,
how many names can actually be filled (>=1 lot of 100 shares), how much cash is stranded by lot
rounding + the ¥5 min-commission, and what per-name notional (hence round-trip cost %) results.

Account Capital (equity) and Strategy Capital (exposure*equity) are kept explicitly separate (§8):
alpha is unchanged; only executability changes.
"""
from __future__ import print_function

from research_engine.cn_a_short.cost import LOT, round_trip, buy_cost_yuan, sell_cost_yuan


def lot_cost_yuan(price, slip_side=0.0):
    """Cash to buy ONE lot (100 shares) at `price`, optionally including buy-side slippage."""
    return LOT * price * (1.0 + slip_side)


def lots_for(alloc_yuan, price, slip_side=0.0):
    """Whole lots buyable with `alloc_yuan` at `price`. Never negative; floor to lot."""
    lc = lot_cost_yuan(price, slip_side)
    if lc <= 0:
        return 0
    return int(alloc_yuan // lc)


def feasible_portfolio(equity, price, k, exposure=1.0, slip_side=0.0):
    """Try to build an equal-money K-name portfolio at a single price level.

    Returns realized name count, invested, cash-idle fraction, per-name notional and round-trip
    cost %. Guarantees cash never goes negative: invested <= exposure*equity <= equity.
    """
    assert equity > 0 and price > 0 and k >= 1 and 0 < exposure <= 1.0
    budget = exposure * equity
    unit = budget / k
    lots = lots_for(unit, price, slip_side)
    if lots == 0:
        # Cannot even hold 1 lot per name at this K → shrink K to what fits.
        max_names = lots_for(budget, price, slip_side)
        return {
            "equity": equity, "price": price, "k_target": k, "exposure": exposure,
            "feasible": False, "reason": "LOT_TOO_BIG_FOR_UNIT",
            "n_names": min(k, max_names), "max_names_at_1lot": max_names,
            "invested": 0.0, "cash_idle_frac": 1.0, "per_name_notional": 0.0,
        }
    per_name_notional = lots * LOT * price
    invested = k * per_name_notional
    # If rounding pushed invested over budget (can't happen since lots=floor(unit/lotcost)), clamp names.
    n_names = k
    if invested > budget + 1e-9:
        n_names = int(budget // per_name_notional)
        invested = n_names * per_name_notional
    rt = round_trip(per_name_notional)
    idle = 1.0 - invested / equity
    assert invested <= equity + 1e-6, "invariant: invested must not exceed equity"
    return {
        "equity": equity, "price": price, "k_target": k, "exposure": exposure,
        "feasible": n_names >= 1, "reason": "OK" if n_names == k else "K_REDUCED",
        "n_names": n_names, "lots_per_name": lots, "per_name_notional": per_name_notional,
        "invested": invested, "cash_idle_frac": idle,
        "rt_cost_pct_fee_only": rt["fee_only_pct"], "rt_cost_pct_total": rt["total_pct"],
        "min_fee_binding": rt["min_fee_binding"],
    }


def min_capital_for_k(k, price, exposure=1.0, slip_side=0.0):
    """Theoretical minimum equity to hold 1 lot each of K names at `price` within exposure budget.

    equity >= K * lot_cost / exposure. This is a FLOOR; real threshold is higher once you add a
    fee/limit-lock/unfilled buffer (see `practical_min_capital_for_k`).
    """
    return k * lot_cost_yuan(price, slip_side) / exposure


def practical_min_capital_for_k(k, price, exposure=1.0, slip_side=0.0, max_idle_frac=0.15, buffer_lots=1):
    """A padded threshold: enough that (a) cash idle from lot rounding <= max_idle_frac and
    (b) there is `buffer_lots` of extra headroom per name for fees/limit-lock re-tries.

    Returns yuan. Transparent, not fitted.
    """
    theo = min_capital_for_k(k + buffer_lots, price, exposure, slip_side)
    # Also require idle bound: invested/equity >= (1-max_idle_frac)*exposure is easier at higher equity;
    # the buffer_lots term already dominates for small K, so take the max of both notions.
    idle_floor = min_capital_for_k(k, price, exposure, slip_side) / max(1e-9, (1.0 - max_idle_frac))
    return max(theo, idle_floor)


def round_trip_notional_only(notional, day="2026-01-01", slip_side=0.001):
    """Convenience for reporting: cost in yuan and % for a single per-name notional."""
    rt = round_trip(notional, day=day, slip_side=slip_side)
    return rt


__all__ = [
    "lot_cost_yuan", "lots_for", "feasible_portfolio", "min_capital_for_k",
    "practical_min_capital_for_k", "round_trip_notional_only",
]
