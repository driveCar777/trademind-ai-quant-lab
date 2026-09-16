"""Economic feasibility: horizon x turnover x slippage -> cost envelope and gross-alpha requirement.

This is a COST ENVELOPE, not a claim about whether alpha exists (§11). It answers: given a hold
length, a turnover scenario, a slippage assumption and a per-name notional band, how much friction
does a strategy pay, and how much gross per-rebalance return it must beat to be net positive.

Turnover convention (explicit, §10): `turnover` = ONE-WAY fraction of the book traded per rebalance
period (0.20 = 20% replaced). 100% one-way turnover per period = one full round trip on that capital.
"""
from __future__ import print_function

from research_engine.cn_a_short.cost import round_trip

YEAR_DAYS = 242.0


def periods_per_year(hold_days):
    """Non-overlapping rebalances per year for a given hold length."""
    return YEAR_DAYS / float(hold_days)


def cost_envelope(hold_days, turnover, notional, slip_side=0.001, day="2026-01-01"):
    """Friction for one (hold, turnover, notional, slippage) cell.

    Returns round-trip cost %, per-period friction, annualized friction, and the gross per-period
    return needed to (a) break even and (b) net +10%/yr.
    """
    rt = round_trip(notional, day=day, slip_side=slip_side)
    rt_pct = rt["total_pct"]
    ppy = periods_per_year(hold_days)
    per_period_friction = turnover * rt_pct
    annual_friction = ppy * per_period_friction
    gross_breakeven_per_period = per_period_friction
    gross_for_net10_per_period = per_period_friction + 0.10 / ppy
    return {
        "hold_days": hold_days,
        "turnover_one_way": turnover,
        "notional": notional,
        "slip_side": slip_side,
        "round_trip_pct_total": rt_pct,
        "round_trip_pct_fee_only": rt["fee_only_pct"],
        "min_fee_binding": rt["min_fee_binding"],
        "periods_per_year": ppy,
        "per_period_friction": per_period_friction,
        "annual_friction": annual_friction,
        "gross_breakeven_per_period": gross_breakeven_per_period,
        "gross_for_net10pct_per_period": gross_for_net10_per_period,
    }


def net_from_gross(gross_per_period, hold_days, turnover, notional, slip_side=0.001, day="2026-01-01"):
    """Given an assumed gross per-rebalance return, return net per-period and annualized net."""
    env = cost_envelope(hold_days, turnover, notional, slip_side, day)
    net_period = gross_per_period - env["per_period_friction"]
    net_annual = env["periods_per_year"] * net_period
    return {"net_per_period": net_period, "net_annual_approx": net_annual, "envelope": env}


def grid(horizons, turnovers, notionals, slippages, day="2026-01-01"):
    """Full cross product -> list of cost_envelope rows for reporting."""
    rows = []
    for h in horizons:
        for tn in turnovers:
            for P in notionals:
                for s in slippages:
                    rows.append(cost_envelope(h, tn, P, s, day))
    return rows


__all__ = ["periods_per_year", "cost_envelope", "net_from_gross", "grid", "YEAR_DAYS"]
