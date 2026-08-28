"""Evaluate one locked hypothesis on the aligned pack. No OOS reads."""
from __future__ import print_function

import math

from research_engine.cross_asset import CROSS_BLOCK, CROSS_BOOT, CROSS_PERM, CROSS_SEED
from research_engine.cross_asset.align import iter_role
from research_engine.cross_asset.contract import deny_final_oos
from research_engine.profit import START_EQUITY
from research_engine.profit.backtest.metrics import summarize_equity
from research_engine.profit.cost.model import commission, fill_price
from research_engine.profit.risk.sizing import position_qty, stop_distance
from research_engine.regime.state import friction_raw_at
from research_engine.statistics import (
    bootstrap_delta_ci,
    effect_size_cohens_d,
    mean,
    moving_block_bootstrap_delta_ci,
    permutation_delta_p,
)


def _target_series(rows, target):
    bars = []
    for row in rows:
        bar = dict(row[target])
        bar["date"] = row["date"]
        bar["role"] = row["role"]
        bars.append(bar)
    return bars


def _ret(rows, symbol, i):
    if i < 1:
        return None
    a = rows[i - 1][symbol].get("close")
    b = rows[i][symbol].get("close")
    if a is None or b is None or a == 0:
        return None
    return float(b) / float(a) - 1.0


def _wide(target_bars, t):
    raw = friction_raw_at(target_bars, t)
    return raw is not None and raw >= 0.5


def freeze_gate(rows, spec):
    deny_final_oos("research")
    kind = spec.get("kind")
    if kind == "DOLLAR_UP":
        return {"kind": "DOLLAR_UP", "gate": 0.0}
    symbol = spec["input_assets"][0]
    vals = []
    i = 0
    while i < len(rows):
        if rows[i].get("role") != "research":
            i += 1
            continue
        ret = _ret(rows, symbol, i)
        if ret is not None:
            vals.append(ret)
        i += 1
    if not vals:
        return {"kind": "Q3", "gate": None}
    ordered = sorted(vals)
    idx = int(math.floor(0.67 * (len(ordered) - 1)))
    return {"kind": "Q3", "gate": ordered[idx], "n_freeze": len(ordered)}


def signal_at(rows, i, spec, gate_info):
    kind = spec.get("kind")
    if kind == "DOLLAR_UP":
        jpy = _ret(rows, "USDJPY", i)
        eur = _ret(rows, "EURUSD", i)
        if jpy is None or eur is None:
            return 0
        if jpy > 0.0 and eur < 0.0:
            return int(spec["side"])
        return 0
    symbol = spec["input_assets"][0]
    ret = _ret(rows, symbol, i)
    gate = (gate_info or {}).get("gate")
    if ret is None or gate is None:
        return 0
    if ret >= gate:
        return int(spec["side"])
    return 0


def _pearson(xs, ys):
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    mx = mean(xs)
    my = mean(ys)
    if mx is None or my is None:
        return None
    num = 0.0
    dx = 0.0
    dy = 0.0
    i = 0
    while i < len(xs):
        a = xs[i] - mx
        b = ys[i] - my
        num += a * b
        dx += a * a
        dy += b * b
        i += 1
    den = math.sqrt(dx * dy)
    if den == 0:
        return None
    return num / den


def _one_step(entry_bar, exit_bar, side, stop_px):
    entry = fill_price(entry_bar, side, False)
    if entry is None:
        return None
    hit = None
    if stop_px is not None:
        op = entry_bar.get("open")
        hi = entry_bar.get("high")
        lo = entry_bar.get("low")
        if side > 0 and lo is not None and lo <= stop_px:
            hit = op if op is not None and op < stop_px else stop_px
        elif side < 0 and hi is not None and hi >= stop_px:
            hit = op if op is not None and op > stop_px else stop_px
    if hit is not None:
        exit_px = hit
    else:
        exit_px = fill_price(exit_bar, side, True)
    if exit_px is None:
        return None
    gross = (float(exit_px) - float(entry)) * float(side) / float(entry)
    fees = 2.0 * 0.0005
    return {
        "entry": entry,
        "exit": exit_px,
        "step_return": gross - fees,
        "stopped": hit is not None,
    }


def _eligible_index(rows, i):
    if i < 1 or i + 2 >= len(rows):
        return False
    role = rows[i].get("role")
    if role not in ("research", "validation"):
        return False
    if rows[i + 1].get("role") != role:
        return False
    if rows[i + 2].get("role") != role:
        return False
    return True


def evaluate_hypothesis(pack, spec, seed=CROSS_SEED, iters_boot=CROSS_BOOT, iters_perm=CROSS_PERM, block_length=CROSS_BLOCK):
    rows = pack.get("rows") or []
    target = spec["target_asset"]
    target_bars = _target_series(rows, target)
    gate_info = freeze_gate(rows, spec)
    arms = {}
    for role in ("research", "validation"):
        deny_final_oos(role)
        signal_rets = []
        all_rets = []
        trades = []
        cash = float(START_EQUITY)
        cost_paid = 0.0
        curve = []
        xs = []
        ys = []
        n_feature = 0
        n_signal = 0
        i = 0
        while i < len(rows):
            role_i = rows[i].get("role")
            if role_i == "final_oos":
                i += 1
                continue
            if role_i == role:
                if _ret(rows, spec["input_assets"][0], i) is not None:
                    n_feature += 1
                sig = signal_at(rows, i, spec, gate_info)
                if sig != 0:
                    n_signal += 1
                if _eligible_index(rows, i) and not _wide(target_bars, i):
                    dist = stop_distance(target_bars, i, rows[i + 1][target].get("open"))
                    entry_fill = fill_price(rows[i + 1][target], spec["side"], False)
                    stop_px = None
                    if dist is not None and entry_fill is not None:
                        if spec["side"] > 0:
                            stop_px = entry_fill - dist
                        else:
                            stop_px = entry_fill + dist
                    step = _one_step(rows[i + 1][target], rows[i + 2][target], spec["side"], stop_px)
                    if step is not None:
                        all_rets.append(step["step_return"])
                        in_ret = _ret(rows, spec["input_assets"][0], i)
                        tgt_ret = _ret(rows, target, i)
                        if in_ret is not None and tgt_ret is not None:
                            xs.append(in_ret)
                            ys.append(tgt_ret)
                        if sig != 0:
                            signal_rets.append(step["step_return"])
                            entry_px = step["entry"]
                            qty = position_qty(cash, 0.005, entry_px, dist if dist else entry_px * 0.01)
                            if qty > 0:
                                fee_in = commission(qty * entry_px)
                                fee_out = commission(qty * step["exit"])
                                pnl = qty * (step["exit"] - entry_px) * spec["side"] - fee_in - fee_out
                                cash = cash + pnl
                                cost_paid += fee_in + fee_out
                                trades.append(
                                    {
                                        "date": rows[i]["date"],
                                        "pnl": pnl,
                                        "notional": qty * entry_px,
                                        "step_return": step["step_return"],
                                    }
                                )
            equity = cash
            if rows[i].get("role") == role:
                curve.append(equity)
            i += 1
        metrics = summarize_equity(curve if curve else [START_EQUITY], "D1", START_EQUITY, trades)
        metrics["cost_paid"] = cost_paid
        delta = None
        if signal_rets and all_rets:
            delta = mean(signal_rets) - mean(all_rets)
        arms[role] = {
            "n_aligned": len(iter_role(pack, role)),
            "n_feature": n_feature,
            "n_signal": n_signal,
            "occupancy": None if n_feature == 0 else n_signal / float(n_feature),
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
            "contemporaneous_corr": _pearson(xs, ys),
            "end_equity": metrics.get("end_equity"),
            "trade_count": len(trades),
            "win_count": metrics.get("win_count"),
        }
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
        "target_asset": target,
        "input_assets": list(spec.get("input_assets") or []),
        "predicted_sign": spec.get("predicted_sign"),
        "feature_gate": gate_info,
        "research": arms["research"],
        "validation": arms["validation"],
    }
