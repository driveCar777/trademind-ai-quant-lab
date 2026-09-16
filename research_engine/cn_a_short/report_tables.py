"""Generate the Phase 2A cost / account / feasibility tables. Runs WITHOUT any price panel.

These are deterministic arithmetic derived from the canonical cost model; they are the empirical
core of Phase 2A that IS runnable in this environment. Emits JSON to data/.../cn_a_short/ and prints
a compact summary used to fill A_SHORT_COST_FEASIBILITY_V2 / A_SHORT_ACCOUNT_FEASIBILITY.
"""
from __future__ import print_function

import json
import os

from research_engine.cn_a_short import (ACCOUNT_SIZES, HORIZONS, SLIPPAGE_SIDE_GRID, TOP_KS,
                                        TURNOVER_SCENARIOS)
from research_engine.cn_a_short.account import feasible_portfolio, min_capital_for_k, practical_min_capital_for_k
from research_engine.cn_a_short.cost import min_fee_breakeven_notional, round_trip
from research_engine.cn_a_short.feasibility import cost_envelope

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "market", "research_engine", "cn_a_short")

NOTIONAL_BANDS = (500, 1_000, 2_000, 5_000, 10_000, 20_000, 50_000, 100_000, 500_000)
PRICE_LEVELS = (5, 10, 20, 50, 100)


def cost_table():
    rows = []
    for P in NOTIONAL_BANDS:
        fee = round_trip(P, slip_side=0.0)
        slip = round_trip(P, slip_side=0.001)
        rows.append({"notional": P, "min_fee_binding": fee["min_fee_binding"],
                     "rt_fee_only_pct": fee["fee_only_pct"], "rt_with_0p1_slip_pct": slip["total_pct"]})
    return {"min_fee_breakeven_notional": min_fee_breakeven_notional(), "rows": rows}


def slippage_sensitivity():
    out = {}
    for P in (2_000, 20_000, 100_000):
        out[P] = [{"slip_side": s, "rt_pct": round_trip(P, slip_side=s)["total_pct"]} for s in SLIPPAGE_SIDE_GRID]
    return out


def feasibility_grid():
    rows = []
    for hold in HORIZONS:
        for name, tn in TURNOVER_SCENARIOS.items():
            for P in (2_000, 20_000, 100_000):
                for s in (0.0, 0.001, 0.003):
                    env = cost_envelope(hold, tn, P, slip_side=s)
                    rows.append({"hold": hold, "turnover": name, "turnover_val": tn, "notional": P,
                                 "slip_side": s, "rt_pct": env["round_trip_pct_total"],
                                 "annual_friction": env["annual_friction"],
                                 "gross_breakeven_per_period": env["gross_breakeven_per_period"],
                                 "gross_for_net10pct_per_period": env["gross_for_net10pct_per_period"]})
    return rows


def account_grid():
    rows = []
    for equity in ACCOUNT_SIZES:
        for price in PRICE_LEVELS:
            for k in TOP_KS:
                fp = feasible_portfolio(equity, price, k, exposure=1.0, slip_side=0.001)
                rows.append({"equity": equity, "price": price, "k": k,
                             "feasible": fp["feasible"], "n_names": fp["n_names"],
                             "cash_idle_frac": round(fp["cash_idle_frac"], 4),
                             "per_name_notional": fp.get("per_name_notional", 0.0),
                             "rt_cost_pct_total": fp.get("rt_cost_pct_total")})
    return rows


def min_capital_table():
    rows = []
    for k in TOP_KS:
        for price in PRICE_LEVELS:
            rows.append({"k": k, "price": price,
                         "theoretical_min_capital": min_capital_for_k(k, price, 1.0, 0.001),
                         "practical_min_capital": practical_min_capital_for_k(k, price, 1.0, 0.001)})
    return rows


def build():
    data = {
        "cost_table": cost_table(),
        "slippage_sensitivity": slippage_sensitivity(),
        "feasibility_grid": feasibility_grid(),
        "account_grid": account_grid(),
        "min_capital_table": min_capital_table(),
    }
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    path = os.path.join(OUT, "PHASE2A_TABLES.json")
    json.dump(data, open(path, "w"), indent=2, default=float)
    return data, path


if __name__ == "__main__":
    data, path = build()
    ct = data["cost_table"]
    print("MIN_FEE_BREAKEVEN_NOTIONAL:", ct["min_fee_breakeven_notional"])
    print("\nROUND-TRIP COST BY NOTIONAL:")
    for r in ct["rows"]:
        print("  P=%-8d fee_only=%.3f%%  +0.1%%slip=%.3f%%  min_fee_binding=%s"
              % (r["notional"], r["rt_fee_only_pct"] * 100, r["rt_with_0p1_slip_pct"] * 100, r["min_fee_binding"]))
    print("\nANNUAL FRICTION (turnover=100%, +0.1% slip):")
    for r in data["feasibility_grid"]:
        if r["turnover"] == "HIGH" and r["slip_side"] == 0.001 and r["notional"] == 20_000:
            print("  T+%d  annual_friction=%.1f%%  breakeven/period=%.3f%%"
                  % (r["hold"], r["annual_friction"] * 100, r["gross_breakeven_per_period"] * 100))
    print("\nWROTE", path)
