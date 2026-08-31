"""Candidate-to-strategy bridge. Diagnostic series A/B/C. Not a selector."""
from __future__ import print_function

import numpy as np


def build_bridge(overlap_rows, trades):
    by_date = dict((r["date"], r) for r in overlap_rows)
    rows = []
    for tr in trades:
        cand = by_date.get(tr["signal_date"])
        cand_net = None if cand is None else float(cand["net"])
        cap = float(tr["capital_ret"])
        v13 = float(tr["v13_style_net"])
        tags = []
        if cand_net is None:
            tags.append("NO_CANDIDATE_ROW")
        else:
            if abs(cand_net - v13) > 1e-6:
                tags.append("PICK_OR_FILL_MISMATCH")
            else:
                tags.append("SAME_SIGNAL_DATE")
        if abs(v13 - cap) > 1e-4:
            tags.append("COST_OR_CASH_FORMULA")
        if cand_net is not None and (cand_net > 0) != (cap > 0):
            tags.append("SIGN_FLIP")
        if tr.get("cash_frac", 0) > 0.005:
            tags.append("UNFILLED_CASH")
        rows.append(
            {
                "date": tr["signal_date"],
                "entry": tr["entry"],
                "exit": tr["exit"],
                "candidate_forward_return": cand_net,
                "strategy_realized_return": cap,
                "v13_style_net": v13,
                "difference": None if cand_net is None else cap - cand_net,
                "formula_gap": cap - v13,
                "n_elig": tr["n_elig"],
                "n_sel": tr["n_sel"],
                "n_fill": tr["n_fill"],
                "cash_frac": tr["cash_frac"],
                "cause": "|".join(tags) if tags else "ALIGNED",
            }
        )
    return rows


def series_abc(overlap_rows, trades, grids):
    """A=overlapping candidate. B=20-day nonoverlap. C=mean of 20 offset capital-style grids. Diagnostic only."""
    a_nets = [float(r["net"]) for r in overlap_rows]
    b_v13 = [float(tr["v13_style_net"]) for tr in trades]
    b_cap = [float(tr["capital_ret"]) for tr in trades]
    eq_v13 = 1.0
    eq_cap = 1.0
    for x in b_v13:
        eq_v13 *= 1.0 + x
    for x in b_cap:
        eq_cap *= 1.0 + x
    return {
        "A_overlapping_mean_net": float(np.mean(a_nets)) if a_nets else None,
        "A_n": len(a_nets),
        "B_nonoverlap_v13_mean": float(np.mean(b_v13)) if b_v13 else None,
        "B_nonoverlap_v13_compound": eq_v13 - 1.0,
        "B_nonoverlap_capital_mean": float(np.mean(b_cap)) if b_cap else None,
        "B_nonoverlap_capital_compound": eq_cap - 1.0,
        "C_offset_grids": {
            "n_negative": grids.get("n_negative_grids"),
            "mean_end": grids.get("mean_grid_end"),
            "min_end": grids.get("min_grid_end"),
            "max_end": grids.get("max_grid_end"),
            "offset0_end": grids.get("offset0_end"),
        },
        "not_a_selector": True,
        "note": "B/C are diagnostics. Official strategy remains the single non-overlapping capital account.",
    }
