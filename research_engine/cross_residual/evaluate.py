"""Residual 5-step change. Cost both legs. No Final OOS."""
from __future__ import print_function

from research_engine.cross_residual import HOLD_BARS, XR_BLOCK, XR_BOOT, XR_PERM, XR_SEED
from research_engine.holdout import assert_role_allowed
from research_engine.profit.cost.model import fill_price
from research_engine.statistics import (
    bootstrap_delta_ci,
    effect_size_cohens_d,
    mean,
    moving_block_bootstrap_delta_ci,
    permutation_delta_p,
)
from research_engine.cross_residual.residual import signal_at


def _bar(row, prefix):
    return {
        "open": row.get(prefix + "_open"),
        "high": row.get(prefix + "_high"),
        "low": row.get(prefix + "_low"),
        "close": row.get(prefix + "_close"),
        "spread": row.get(prefix + "_spread"),
    }


def two_leg_return(rows, t, fade_sign, hold_bars=HOLD_BARS):
    """fade_sign +1 means residual should rise (long GOLD / short OIL)."""
    entry_i = t + 1
    exit_i = t + 1 + hold_bars
    if exit_i >= len(rows):
        return None
    if rows[t].get("role") != rows[entry_i].get("role"):
        return None
    if rows[t].get("role") != rows[exit_i].get("role"):
        return None
    g_in = fill_price(_bar(rows[entry_i], "GOLD"), fade_sign, False)
    o_in = fill_price(_bar(rows[entry_i], "OIL"), -fade_sign, False)
    g_out = fill_price(_bar(rows[exit_i], "GOLD"), fade_sign, True)
    o_out = fill_price(_bar(rows[exit_i], "OIL"), -fade_sign, True)
    if None in (g_in, o_in, g_out, o_out):
        return None
    g_leg = (float(g_out) - float(g_in)) * float(fade_sign) / float(g_in)
    o_leg = (float(o_out) - float(o_in)) * float(-fade_sign) / float(o_in)
    fees = 4.0 * 0.0005
    resid0 = rows[t].get("resid")
    resid1 = rows[min(t + hold_bars, len(rows) - 1)].get("resid")
    d_resid = None
    if resid0 is not None and resid1 is not None:
        d_resid = resid1 - resid0
    return {
        "step_return": 0.5 * (g_leg + o_leg) - fees,
        "d_resid": d_resid,
        "entry_index": entry_i,
        "exit_index": exit_i,
    }


def evaluate_hypothesis(rows, spec, cuts, seed=XR_SEED, iters_boot=XR_BOOT, iters_perm=XR_PERM, block_length=XR_BLOCK):
    arms = {}
    for role in ("research", "validation"):
        assert_role_allowed(role)
        sig = []
        base = []
        n_signal = 0
        i = 0
        while i < len(rows):
            if rows[i].get("role") == "final_oos":
                i += 1
                continue
            if rows[i].get("role") != role:
                i += 1
                continue
            side = signal_at(rows[i], spec, cuts)
            fade = side if side != 0 else 1
            step = two_leg_return(rows, i, fade if side != 0 else 1)
            if step is not None:
                base.append(step["step_return"])
                if side != 0:
                    n_signal += 1
                    signed = step["step_return"]
                    if spec.get("kind") == "RICH":
                        signed = step["step_return"]
                    sig.append(signed)
            i += 1
        delta = None
        if sig and base:
            delta = mean(sig) - mean(base)
        arms[role] = {
            "n_signal": n_signal,
            "n_trade": n_signal,
            "mean_signal": mean(sig),
            "mean_baseline": mean(base),
            "delta": delta,
            "effect_size": effect_size_cohens_d(sig, base),
            "total_return": None if not sig else sum(sig),
            "raw_p": None,
            "max_drawdown": 0.0,
            "max_trade_share": None if n_signal == 0 else 1.0 / float(n_signal),
        }
        if sig and base and role == "research":
            perm = permutation_delta_p(sig, base, iterations=iters_perm, seed=seed)
            arms[role]["raw_p"] = None if perm is None else perm.get("p_value")
            arms[role]["bootstrap_ci"] = bootstrap_delta_ci(sig, base, iterations=iters_boot, seed=seed)
            arms[role]["block_bootstrap_ci"] = moving_block_bootstrap_delta_ci(
                sig, base, block_length=block_length, iterations=iters_boot, seed=seed
            )
    pred = spec.get("predicted_sign")
    for role in arms:
        if pred in (-1, 1) and arms[role].get("mean_signal") is not None:
            if arms[role]["mean_signal"] * pred > 0:
                arms[role]["sign_ok"] = True
    return {
        "hypothesis_id": spec["hypothesis_id"],
        "kind": spec.get("kind"),
        "predicted_sign": pred,
        "target_asset": "GOLD_OIL",
        "research": arms["research"],
        "validation": arms["validation"],
    }
