"""Hold=5 NEXT_BAR_OPEN IV book. Overlap skip. No close fill. No Final OOS."""
from __future__ import print_function

from research_engine.positioning import HOLD_BARS, POS_BLOCK, POS_BOOT, POS_PERM, POS_SEED, OCCUPANCY_FAIL
from research_engine.positioning.contract import deny_final_oos
from research_engine.positioning.event_detector import fired_at
from research_engine.positioning.windows import same_role_hold
from research_engine.profit import START_EQUITY
from research_engine.profit.backtest.metrics import summarize_equity
from research_engine.profit.cost.model import commission
from research_engine.profit.risk.sizing import position_qty
from research_engine.regime_transition.evaluator import costed_hold
from research_engine.statistics import (
    bootstrap_delta_ci,
    effect_size_cohens_d,
    mean,
    moving_block_bootstrap_delta_ci,
    permutation_delta_p,
)


def _eligible(bars, signal_t, role, hold_bars=HOLD_BARS):
    if signal_t < 0:
        return False
    if bars[signal_t].get("role") == "final_oos":
        return False
    if bars[signal_t].get("role") != role:
        return False
    if not same_role_hold(bars, signal_t, hold_bars, role):
        return False
    return True


def evaluate_hypothesis(
    bars,
    spec,
    seed=POS_SEED,
    iters_boot=POS_BOOT,
    iters_perm=POS_PERM,
    block_length=POS_BLOCK,
    hold_bars=HOLD_BARS,
):
    event = spec["event"]
    side = int(spec.get("side") if spec.get("side") is not None else spec.get("predicted_sign") or 1)
    if int(spec.get("hold_bars") or hold_bars) != 5:
        raise RuntimeError("HOLD_MUST_BE_5")
    arms = {}
    for role in ("research", "validation"):
        deny_final_oos(role)
        signal_rets = []
        all_rets = []
        trades = []
        cash = float(START_EQUITY)
        cost_paid = 0.0
        curve = []
        n_feature = 0
        n_signal = 0
        n_skip_overlap = 0
        n_eligible = 0
        next_free = 0
        i = 0
        while i < len(bars):
            role_i = bars[i].get("role")
            if role_i == "final_oos":
                i += 1
                continue
            if role_i == role:
                n_feature += 1
                fired = fired_at(bars[i], event)
                if fired:
                    n_signal += 1
                if _eligible(bars, i, role, hold_bars):
                    n_eligible += 1
                    step = costed_hold(bars, i, side, hold_bars)
                    if step is not None:
                        all_rets.append(step["step_return"])
                        if fired:
                            if step["entry_index"] < next_free:
                                n_skip_overlap += 1
                            else:
                                signal_rets.append(step["step_return"])
                                dist = step.get("stop_dist")
                                entry_px = step["entry"]
                                qty = position_qty(cash, 0.005, entry_px, dist if dist else entry_px * 0.01)
                                if qty > 0:
                                    fee_in = commission(qty * entry_px)
                                    fee_out = commission(qty * step["exit"])
                                    pnl = qty * (step["exit"] - entry_px) * side - fee_in - fee_out
                                    cash = cash + pnl
                                    cost_paid += fee_in + fee_out
                                    trades.append(
                                        {
                                            "date": bars[i].get("date"),
                                            "signal_t": i,
                                            "pnl": pnl,
                                            "notional": qty * entry_px,
                                            "step_return": step["step_return"],
                                            "stopped": step["stopped"],
                                        }
                                    )
                                    next_free = step["scheduled_exit"]
                curve.append(cash)
            i += 1
        metrics = summarize_equity(curve if curve else [START_EQUITY], "D1", START_EQUITY, trades)
        occupancy = None if n_feature == 0 else n_signal / float(n_feature)
        delta = None
        if signal_rets and all_rets:
            delta = mean(signal_rets) - mean(all_rets)
        leak = occupancy is not None and occupancy >= OCCUPANCY_FAIL
        arms[role] = {
            "n_bars": n_feature,
            "n_feature": n_feature,
            "n_eligible": n_eligible,
            "n_signal": n_signal,
            "n_skip_overlap": n_skip_overlap,
            "occupancy": occupancy,
            "level_leak": leak,
            "n_trade": len(trades),
            "total_return": metrics.get("total_return"),
            "cagr": metrics.get("cagr"),
            "max_drawdown": metrics.get("max_drawdown"),
            "sharpe": metrics.get("sharpe"),
            "turnover": metrics.get("turnover"),
            "cost_paid": cost_paid,
            "max_trade_share": metrics.get("max_trade_share"),
            "mean_signal": mean(signal_rets),
            "mean_baseline": mean(all_rets),
            "delta": delta,
            "effect_size": effect_size_cohens_d(signal_rets, all_rets),
            "raw_p": None,
            "bootstrap_ci": None,
            "block_bootstrap_ci": None,
            "end_equity": metrics.get("end_equity"),
            "trade_count": len(trades),
            "win_count": metrics.get("win_count"),
        }
        if leak:
            arms[role]["fail_reason"] = "LEVEL_LEAK"
        if signal_rets and all_rets and role == "research":
            perm = permutation_delta_p(signal_rets, all_rets, iterations=iters_perm, seed=seed)
            arms[role]["raw_p"] = None if perm is None else perm.get("p_value")
            arms[role]["bootstrap_ci"] = bootstrap_delta_ci(signal_rets, all_rets, iterations=iters_boot, seed=seed)
            arms[role]["block_bootstrap_ci"] = moving_block_bootstrap_delta_ci(
                signal_rets, all_rets, block_length=block_length, iterations=iters_boot, seed=seed
            )
        elif signal_rets and all_rets:
            arms[role]["bootstrap_ci"] = bootstrap_delta_ci(signal_rets, all_rets, iterations=iters_boot, seed=seed)
            arms[role]["block_bootstrap_ci"] = moving_block_bootstrap_delta_ci(
                signal_rets, all_rets, block_length=block_length, iterations=iters_boot, seed=seed
            )
    return {
        "hypothesis_id": spec["hypothesis_id"],
        "target_asset": spec.get("target") or spec.get("target_asset"),
        "event": event,
        "predicted_sign": spec.get("predicted_sign"),
        "side": side,
        "hold_bars": 5,
        "research": arms["research"],
        "validation": arms["validation"],
    }
