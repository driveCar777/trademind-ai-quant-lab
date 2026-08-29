"""Cross-section book. Hold=5 NEXT_BAR_OPEN. Overlap skip. No Final OOS."""
from __future__ import print_function

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
from research_engine.idx_async import HOLD_BARS, OCCUPANCY_FAIL, IA_BLOCK, IA_BOOT, IA_PERM, IA_SEED
from research_engine.idx_async.contract import deny_final_oos
from research_engine.idx_async.event_detector import fired_at
from research_engine.idx_async.windows import same_role_hold


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


def _legs(_aligned, _row, mode):
    if mode == "US500_LONG":
        return [("US500", 1)]
    if mode == "US500_SHORT":
        return [("US500", -1)]
    if mode == "GER40_LONG":
        return [("GER40", 1)]
    return []


def evaluate_hypothesis(
    packed,
    spec,
    seed=IA_SEED,
    iters_boot=IA_BOOT,
    iters_perm=IA_PERM,
    block_length=IA_BLOCK,
    hold_bars=HOLD_BARS,
):
    event = spec["event"]
    mode = spec.get("side_mode") or "REV"
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
                fired = fired_at(book[i], event)
                if fired:
                    n_signal += 1
                if _eligible(book, i, role, hold_bars):
                    n_eligible += 1
                    legs = _legs(aligned, book[i], mode)
                    steps = []
                    ok = True
                    for name, side in legs:
                        step = costed_hold(aligned[name], i, side, hold_bars)
                        if step is None:
                            ok = False
                            break
                        steps.append((name, side, step))
                    if ok and steps:
                        rets = [s[2]["step_return"] for s in steps]
                        book_ret = mean(rets)
                        all_rets.append(book_ret)
                        if fired:
                            if steps[0][2]["entry_index"] < next_free:
                                n_skip_overlap += 1
                            else:
                                signal_rets.append(book_ret)
                                pnl = 0.0
                                notion = 0.0
                                for _name, side, step in steps:
                                    dist = step.get("stop_dist")
                                    entry_px = step["entry"]
                                    qty = position_qty(
                                        cash / float(len(steps)),
                                        0.005,
                                        entry_px,
                                        dist if dist else entry_px * 0.01,
                                    )
                                    if qty > 0:
                                        fee_in = commission(qty * entry_px)
                                        fee_out = commission(qty * step["exit"])
                                        pnl += qty * (step["exit"] - entry_px) * side - fee_in - fee_out
                                        cost_paid += fee_in + fee_out
                                        notion += qty * entry_px
                                cash = cash + pnl
                                trades.append(
                                    {
                                        "date": book[i].get("date"),
                                        "signal_t": i,
                                        "pnl": pnl,
                                        "notional": notion,
                                        "step_return": book_ret,
                                        "n_legs": len(steps),
                                    }
                                )
                                next_free = steps[0][2]["scheduled_exit"]
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
        "target_asset": "BOOK",
        "event": event,
        "side_mode": mode,
        "predicted_sign": spec.get("predicted_sign"),
        "hold_bars": 5,
        "research": arms["research"],
        "validation": arms["validation"],
    }
