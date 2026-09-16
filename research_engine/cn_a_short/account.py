"""Account / executability feasibility. Pure arithmetic (no price panel needed).

Answers §7-§9: for a given account equity, stock price, target name count K and exposure,
how many names can actually be filled (>=1 lot of 100 shares), how much cash is stranded by lot
rounding + the ¥5 min-commission, and what per-name notional (hence round-trip cost %) results.

Account Capital (equity) and Strategy Capital (exposure*equity) are kept explicitly separate (§8):
alpha is unchanged; only executability changes.
"""
from __future__ import print_function

from research_engine.cn_a_short.cost import LOT, SLIPPAGE, _fee, round_trip, buy_cost_yuan, sell_cost_yuan


def lot_cost_yuan(price, slip_side=0.0):
    """Cash for the SHARES of ONE lot (100 shares) at `price`, incl. buy-side slippage. Excludes fees.

    NOTE (Phase 2A.1): this is the notional/share cost only. It is NOT the affordable-cash test; use
    `buy_cash_out` / `lots_affordable` when you need "can I actually pay for this incl. commission".
    """
    return LOT * price * (1.0 + slip_side)


def buy_cash_out(notional_at_fill):
    """TRUE cash that leaves the account to BUY `notional_at_fill` yuan of shares (slippage already in
    the fill price): shares cash + buy fee (commission floored at ¥5 + transfer). Matches the real
    outflow = buy notional + buy slippage + commission + transfer."""
    return notional_at_fill + _fee(notional_at_fill)


def lots_for(alloc_yuan, price, slip_side=0.0):
    """Whole lots by SHARE cost only (ignores fees). Kept for notional math; NOT an affordability test.
    For "can I actually pay incl. fees" use `lots_affordable`."""
    lc = lot_cost_yuan(price, slip_side)
    if lc <= 0:
        return 0
    return int(alloc_yuan // lc)


def lots_affordable(alloc_yuan, price, slip_side=SLIPPAGE):
    """Max whole lots whose TRUE cash out (shares incl. slippage + commission + transfer) fits
    `alloc_yuan`. Fee-aware: the ¥5 minimum commission can drop the last lot vs `lots_for` (§A fix)."""
    buy_px = price * (1.0 + slip_side)
    lc = LOT * buy_px
    if lc <= 0 or alloc_yuan <= 0:
        return 0
    L = int(alloc_yuan // lc)
    while L > 0:
        notional = L * lc
        if buy_cash_out(notional) <= alloc_yuan + 1e-9:
            return L
        L -= 1
    return 0


def feasible_portfolio(equity, price, k, exposure=1.0, slip_side=SLIPPAGE):
    """Try to build an equal-money K-name portfolio at a single price level. FEE-AWARE (§A fix).

    Sizes lots so TRUE cash out (shares + slippage + commission + transfer) fits each name's unit,
    hence sum(cash_out) <= exposure*equity <= equity. The no-negative-cash invariant now constrains
    TRUE cash after fees, not notional.
    """
    assert equity > 0 and price > 0 and k >= 1 and 0 < exposure <= 1.0
    budget = exposure * equity
    unit = budget / k
    lots = lots_affordable(unit, price, slip_side)
    if lots == 0:
        # Cannot even afford 1 lot (incl. fees) per name at this K → shrink K to what fits the budget.
        max_names = lots_affordable(budget, price, slip_side)
        return {
            "equity": equity, "price": price, "k_target": k, "exposure": exposure,
            "feasible": False, "reason": "LOT_PLUS_FEE_TOO_BIG_FOR_UNIT",
            "n_names": min(k, max_names), "max_names_at_1lot": max_names,
            "invested": 0.0, "cash_out_incl_fees": 0.0, "cash_after_fees": equity,
            "cash_idle_frac": 1.0, "per_name_notional": 0.0,
        }
    buy_px = price * (1.0 + slip_side)
    per_name_fill_notional = lots * LOT * buy_px          # shares cash incl. slippage
    per_name_cash_out = buy_cash_out(per_name_fill_notional)  # + commission(floored) + transfer
    per_name_notional = lots * LOT * price                # clean notional for cost-% reporting
    n_names = k
    total_cash_out = n_names * per_name_cash_out
    invested = n_names * per_name_notional
    cash_after_fees = equity - total_cash_out
    # Invariants (Phase 2A.1): TRUE cash out never exceeds budget or equity; cash never negative.
    assert total_cash_out <= budget + 1e-6, "invariant: true cash out must fit strategy budget"
    assert total_cash_out <= equity + 1e-6, "invariant: true cash out must not exceed equity"
    assert cash_after_fees >= -1e-6, "invariant: no negative cash after fees"
    rt = round_trip(per_name_notional)
    return {
        "equity": equity, "price": price, "k_target": k, "exposure": exposure,
        "feasible": n_names >= 1, "reason": "OK",
        "n_names": n_names, "lots_per_name": lots, "per_name_notional": per_name_notional,
        "invested": invested, "cash_out_incl_fees": round(total_cash_out, 4),
        "cash_after_fees": round(cash_after_fees, 4), "cash_idle_frac": cash_after_fees / equity,
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
    "lot_cost_yuan", "buy_cash_out", "lots_for", "lots_affordable", "feasible_portfolio",
    "min_capital_for_k", "practical_min_capital_for_k", "round_trip_notional_only",
]
