"""Hold=5 NEXT_BAR_OPEN book. Overlap skip. No close fill. No Final OOS PnL."""
from __future__ import print_function

from research_engine.profit import START_EQUITY
from research_engine.profit.backtest.metrics import summarize_equity
from research_engine.profit.cost.model import commission, fill_price
from research_engine.profit.risk.sizing import position_qty, stop_distance
from research_engine.regime_transition import HOLD_BARS, OCCUPANCY_FAIL, RT_BLOCK, RT_BOOT, RT_PERM, RT_SEED
from research_engine.regime_transition.contract import deny_final_oos
from research_engine.regime_transition.transition_detector import feature_at, is_wide, level_still
from research_engine.regime_transition.windows import same_role_hold
from research_engine.statistics import (
    bootstrap_delta_ci,
    effect_size_cohens_d,
    mean,
    moving_block_bootstrap_delta_ci,
    permutation_delta_p,
)


def _stop_hit(bar, side, stop_px):
    if bar is None or stop_px is None:
        return None
    op = bar.get("open")
    hi = bar.get("high")
    lo = bar.get("low")
    if op is None or hi is None or lo is None:
        return None
    if side > 0:
        if lo <= stop_px:
            return op if op < stop_px else stop_px
        return None
    if hi >= stop_px:
        return op if op > stop_px else stop_px
    return None


def costed_hold(bars, signal_t, side, hold_bars=HOLD_BARS):
    entry_i = signal_t + 1
    sched_exit = signal_t + 1 + hold_bars
    if sched_exit >= len(bars) or entry_i >= len(bars):
        return None
    entry_bar = bars[entry_i]
    entry = fill_price(entry_bar, side, False)
    if entry is None:
        return None
    dist = stop_distance(bars, signal_t, entry)
    stop_px = None
    if dist is not None:
        stop_px = entry - dist if side > 0 else entry + dist
    hit = None
    hit_i = None
    t = entry_i
    while t < sched_exit:
        hit = _stop_hit(bars[t], side, stop_px)
        if hit is not None:
            hit_i = t
            break
        t += 1
    if hit is not None:
        exit_px = hit
        exit_i = hit_i
    else:
        exit_px = fill_price(bars[sched_exit], side, True)
        exit_i = sched_exit
    if exit_px is None:
        return None
    gross = (float(exit_px) - float(entry)) * float(side) / float(entry)
    fees = 2.0 * 0.0005
    return {
        "entry": entry,
        "exit": exit_px,
        "entry_index": entry_i,
        "exit_index": exit_i,
        "scheduled_exit": sched_exit,
        "step_return": gross - fees,
        "stopped": hit is not None,
        "stop_dist": dist,
    }


def _eligible(bars, states, signal_t, role, hold_bars=HOLD_BARS):
    if signal_t < 1:
        return False
    if bars[signal_t].get("role") == "final_oos":
        return False
    if bars[signal_t].get("role") != role:
        return False
    if states[signal_t] is None:
        return False
    if is_wide(states[signal_t]):
        return False
    if not same_role_hold(bars, signal_t, hold_bars, role):
        return False
    return True


def evaluate_hypothesis(
    bars,
    states,
    spec,
    seed=RT_SEED,
    iters_boot=RT_BOOT,
    iters_perm=RT_PERM,
    block_length=RT_BLOCK,
    hold_bars=HOLD_BARS,
    n_warmup_drop=0,
    cuts=None,
):
    feature = spec["feature"]
    side = int(spec["side"])
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
        n_level = 0
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
                if states[i] is not None:
                    n_feature += 1
                    if level_still(states[i], feature):
                        n_level += 1
                fired = False
                if i >= 1 and states[i] is not None:
                    fired = feature_at(states[i - 1], states[i], feature)
                if fired:
                    n_signal += 1
                if _eligible(bars, states, i, role, hold_bars):
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
                if role_i == role:
                    curve.append(cash)
            i += 1
        metrics = summarize_equity(curve if curve else [START_EQUITY], "D1", START_EQUITY, trades)
        occupancy = None if n_feature == 0 else n_signal / float(n_feature)
        level_share = None if n_feature == 0 else n_level / float(n_feature)
        delta = None
        if signal_rets and all_rets:
            delta = mean(signal_rets) - mean(all_rets)
        leak = occupancy is not None and occupancy >= OCCUPANCY_FAIL
        arms[role] = {
            "n_bars": n_feature,
            "n_feature": n_feature,
            "n_eligible": n_eligible,
            "n_signal": n_signal,
            "n_warmup_drop": n_warmup_drop,
            "n_skip_overlap": n_skip_overlap,
            "occupancy": occupancy,
            "level_share": level_share,
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
        "feature": feature,
        "predicted_sign": spec.get("predicted_sign"),
        "side": side,
        "hold_bars": 5,
        "vol_cuts": cuts,
        "research": arms["research"],
        "validation": arms["validation"],
    }


def path_benchmark(bars, states, side=1, hold_bars=HOLD_BARS):
    """Unconditional same-side hold=5. Diagnostic. Not a hypothesis."""
    deny_final_oos("research")
    deny_final_oos("validation")
    out = {}
    for role in ("research", "validation"):
        rets = []
        cash = float(START_EQUITY)
        trades = []
        curve = []
        i = 0
        while i < len(bars):
            if bars[i].get("role") == "final_oos":
                i += 1
                continue
            if bars[i].get("role") == role and _eligible(bars, states, i, role, hold_bars):
                step = costed_hold(bars, i, side, hold_bars)
                if step is not None:
                    rets.append(step["step_return"])
                    dist = step.get("stop_dist")
                    qty = position_qty(cash, 0.005, step["entry"], dist if dist else step["entry"] * 0.01)
                    if qty > 0:
                        fee_in = commission(qty * step["entry"])
                        fee_out = commission(qty * step["exit"])
                        pnl = qty * (step["exit"] - step["entry"]) * side - fee_in - fee_out
                        cash = cash + pnl
                        trades.append({"pnl": pnl, "notional": qty * step["entry"]})
            if bars[i].get("role") == role:
                curve.append(cash)
            i += 1
        metrics = summarize_equity(curve if curve else [START_EQUITY], "D1", START_EQUITY, trades)
        out[role] = {
            "n_trade": len(trades),
            "mean_return": mean(rets),
            "total_return": metrics.get("total_return"),
            "cagr": metrics.get("cagr"),
            "max_drawdown": metrics.get("max_drawdown"),
        }
    return out
