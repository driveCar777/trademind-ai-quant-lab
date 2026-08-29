"""Hold=5 next-session open after OI knowledge. 2 bp one-way. No close fill. No Final OOS."""
from __future__ import print_function

from research_engine.oi_cot import (
    HOLD_BARS,
    OCCUPANCY_FAIL,
    OICOT_BLOCK,
    OICOT_BOOT,
    OICOT_PERM,
    OICOT_SEED,
    ONE_WAY_BP,
    ROOTS,
)
from research_engine.oi_cot.contract import deny_final_oos
from research_engine.oi_cot.events import fired_at
from research_engine.profit import START_EQUITY
from research_engine.profit.backtest.metrics import summarize_equity
from research_engine.profit.risk.sizing import position_qty
from research_engine.regime_transition.windows import same_role_hold
from research_engine.statistics import (
    bootstrap_delta_ci,
    effect_size_cohens_d,
    mean,
    moving_block_bootstrap_delta_ci,
    permutation_delta_p,
)
from research_engine.v6_external.knowledge_time import (
    assert_feature_before_target,
    oi_knowledge_utc,
)


def _px(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def futures_hold(bars, signal_t, side, hold_bars=HOLD_BARS):
    entry_i = signal_t + 1
    sched_exit = signal_t + 1 + hold_bars
    if sched_exit >= len(bars) or entry_i >= len(bars):
        return None
    entry = _px(bars[entry_i].get("open"))
    exit_px = _px(bars[sched_exit].get("open"))
    if entry is None or exit_px is None or entry <= 0:
        return None
    gross = (exit_px - entry) * float(side) / entry
    fees = 2.0 * (ONE_WAY_BP / 10000.0)
    return {
        "entry": entry,
        "exit": exit_px,
        "entry_index": entry_i,
        "exit_index": sched_exit,
        "scheduled_exit": sched_exit,
        "step_return": gross - fees,
        "stopped": False,
        "stop_dist": entry * 0.01,
    }


def _eligible(book, signal_t, role, hold_bars=HOLD_BARS):
    if signal_t < 0:
        return False
    if book[signal_t].get("role") == "final_oos":
        return False
    if book[signal_t].get("role") != role:
        return False
    if not same_role_hold(book, signal_t, hold_bars, role):
        return False
    return True


def _assert_week_knowledge(book, signal_t, root, entry_date):
    feat = ((book[signal_t].get("roots") or {}).get(root)) or {}
    know = feat.get("week_knowledge_utc")
    if not know or not entry_date:
        raise RuntimeError("KNOWLEDGE_TIME_MISSING")
    assert_feature_before_target(know, entry_date + "T00:00:00Z")


def evaluate_hypothesis(
    packed,
    spec,
    seed=OICOT_SEED,
    iters_boot=OICOT_BOOT,
    iters_perm=OICOT_PERM,
    block_length=OICOT_BLOCK,
    hold_bars=HOLD_BARS,
):
    event = spec["event"]
    side = int(spec.get("predicted_sign") or 1)
    if int(spec.get("hold_bars") or hold_bars) != 5:
        raise RuntimeError("HOLD_MUST_BE_5")
    aligned = packed["_aligned"]
    book = packed["_book"]
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
        while i < len(book):
            role_i = book[i].get("role")
            if role_i == "final_oos":
                i += 1
                continue
            if role_i == role:
                n_feature += 1
                fired_roots = [root for root in ROOTS if fired_at(book[i], event, root)]
                if fired_roots:
                    n_signal += 1
                if _eligible(book, i, role, hold_bars):
                    n_eligible += 1
                    steps = []
                    for root in ROOTS:
                        step = futures_hold(aligned[root], i, side, hold_bars)
                        if step is not None:
                            steps.append((root, step))
                    if steps:
                        rets = [item[1]["step_return"] for item in steps]
                        all_rets.append(mean(rets))
                        if fired_roots:
                            if steps[0][1]["entry_index"] < next_free:
                                n_skip_overlap += 1
                            else:
                                used = [item for item in steps if item[0] in fired_roots]
                                if used:
                                    book_ret = mean([item[1]["step_return"] for item in used])
                                    signal_rets.append(book_ret)
                                    pnl = 0.0
                                    notion = 0.0
                                    for root, step in used:
                                        entry_date = aligned[root][step["entry_index"]].get("date")
                                        _assert_week_knowledge(book, i, root, entry_date)
                                        entry_px = step["entry"]
                                        qty = position_qty(
                                            cash / float(len(used)),
                                            0.005,
                                            entry_px,
                                            step.get("stop_dist") or entry_px * 0.01,
                                        )
                                        if qty > 0:
                                            fee = abs(qty * entry_px) * (ONE_WAY_BP / 10000.0)
                                            fee_out = abs(qty * step["exit"]) * (ONE_WAY_BP / 10000.0)
                                            pnl += qty * (step["exit"] - entry_px) * side - fee - fee_out
                                            cost_paid += fee + fee_out
                                            notion += qty * entry_px
                                    cash = cash + pnl
                                    trades.append(
                                        {
                                            "date": book[i].get("date"),
                                            "signal_t": i,
                                            "pnl": pnl,
                                            "notional": notion,
                                            "step_return": book_ret,
                                            "n_legs": len(used),
                                        }
                                    )
                                    next_free = used[0][1]["scheduled_exit"]
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
            arms[role]["bootstrap_ci"] = bootstrap_delta_ci(
                signal_rets, all_rets, iterations=iters_boot, seed=seed
            )
            arms[role]["block_bootstrap_ci"] = moving_block_bootstrap_delta_ci(
                signal_rets,
                all_rets,
                block_length=block_length,
                iterations=iters_boot,
                seed=seed,
            )
        elif signal_rets and all_rets:
            arms[role]["bootstrap_ci"] = bootstrap_delta_ci(
                signal_rets, all_rets, iterations=iters_boot, seed=seed
            )
    return {
        "hypothesis_id": spec["hypothesis_id"],
        "target_asset": spec.get("target_asset") or "FRONT",
        "event": event,
        "predicted_sign": spec.get("predicted_sign"),
        "hold_bars": 5,
        "one_way_bp": ONE_WAY_BP,
        "research": arms["research"],
        "validation": arms["validation"],
    }
