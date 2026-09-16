"""A-Short D1 baseline evaluation engine (T+1/T+2/T+3/T+5).

Separates the PREDICTION layer (forward open-to-open returns, ranks) from the STRATEGY/CAPITAL layer
(next-open fills, T+1 sellability, limit-lock/suspension, ¥5 min-fee, slippage, stamp). Reuses the
canonical execution rule `exec_reason` and lot/min-fee constants; nothing here mutates frozen data.

A `pack` is a dict of aligned arrays (same schema as cn_a_share_alpha pack.load_pack):
  dates:[T] symbols:[N] open/high/low/close/preclose/volume/amount/turn:[T,N] float
  tradestatus/isST/listed:[T,N] int
This engine is data-source agnostic: give it any conforming pack (real frozen pack, or synthetic).
"""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_alpha.cost import SLIPPAGE, stamp_duty_sell
from research_engine.cn_a_share_ml_v25.top_n_book import LOT, _fee, board_mask
from research_engine.cn_a_share_strategy_v14_1.capital_ref import exec_reason


# ----------------------------------------------------------------- prediction layer
def forward_label(pack, t, j, hold):
    """Open-to-open forward return for name j: enter open(t+1), exit open(t+1+hold). PREDICTION target.

    Returns raw return (float) or None if out of range / bad opens. No cost, no fill feasibility here
    — this is MEAN_FORWARD_RETURN space, never call it CAGR. T+1 is enforced structurally: the
    earliest exit index is t+2 (t0=t+1, t1=t0+hold, hold>=1).
    """
    t0, t1 = t + 1, t + 1 + hold
    if t1 >= len(pack["dates"]) or hold < 1:
        return None
    o0 = float(pack["open"][t0, j])
    o1 = float(pack["open"][t1, j])
    if not (np.isfinite(o0) and o0 > 0 and np.isfinite(o1) and o1 > 0):
        return None
    return o1 / o0 - 1.0


def _open(pack, t, j):
    return float(pack["open"][t, j])


def simple_eligible(pack, min_hist=20, exclude_st=False):
    """Baseline eligibility matrix [T,N]: listed, trading, finite close, >= min_hist sessions listed,
    optionally exclude ST. Deliberately simple + transparent (contract §eligibility)."""
    T, N = pack["close"].shape
    listed = np.asarray(pack["listed"])
    status = np.asarray(pack["tradestatus"])
    close = np.asarray(pack["close"], dtype=float)
    st = np.asarray(pack["isST"])
    elig = (listed == 1) & (status == 1) & np.isfinite(close) & (close > 0)
    if exclude_st:
        elig = elig & (st != 1)
    if min_hist > 0:
        listed_cum = np.cumsum((listed == 1).astype(np.int32), axis=0)
        elig = elig & (listed_cum >= min_hist)
    return elig


def momentum_scores(pack, t, lookback=20):
    """Simple price momentum baseline score at day t: close(t)/close(t-lookback)-1. For comparison only."""
    if t - lookback < 0:
        return None
    c0 = np.asarray(pack["close"][t], dtype=float)
    cb = np.asarray(pack["close"][t - lookback], dtype=float)
    with np.errstate(all="ignore"):
        return c0 / cb - 1.0


# ----------------------------------------------------------------- strategy / capital layer
EXIT_CARRY_MAX = 10   # forced-hold recovery cap (trading days) when planned exit is not sellable


def _entry_ok(pack, t0, j):
    """Entry executable? (listed/trading/limit/volume). If not FILL, the position is NEVER opened."""
    return exec_reason(pack, t0, j) == "FILL"


def _find_exit(pack, t1, j, max_carry=EXIT_CARRY_MAX):
    """CAPITAL_PATH exit recovery (§B Option 2). Given an already-open position whose PLANNED exit is
    day t1, find the first executable sell day at or after t1 (carry forward up to max_carry). If none
    is sellable within the cap, the position is STUCK (marked at last close, flagged).

    Returns (exit_idx, exit_kind, block_reason, forced_hold_days):
      exit_kind = "FILL" (sold at open) | "STUCK" (could not sell; marked at last close)
    """
    dates = pack["dates"]
    for c in range(max_carry + 1):
        tk = t1 + c
        if tk >= len(dates):
            tk_last = min(t1 + max_carry, len(dates) - 1)
            return tk_last, "STUCK", "END_OF_DATA", (tk_last - t1)
        if exec_reason(pack, tk, j) == "FILL":
            block = None if c == 0 else exec_reason(pack, t1, j)
            return tk, "FILL", block, c
    tk_last = min(t1 + max_carry, len(dates) - 1)
    return tk_last, "STUCK", exec_reason(pack, t1, j), (tk_last - t1)


def top_k_period(pack, scores_t, elig_t, t, hold, k, equity, boards="ALL", slip_side=SLIPPAGE,
                 exit_carry_max=EXIT_CARRY_MAX):
    """One rebalance from signal day t. CAPITAL-PATH aware (§B fix): a position that ENTERS (open t+1
    executable) is ALWAYS booked as held; if its planned exit (t+1+hold) is not sellable, it is carried
    forward to the first executable day (STUCK if never sellable within `exit_carry_max`). Entry-blocked
    names are never opened. Fee-aware lot sizing (§A fix) so cash out (incl. ¥5 min fee) fits the unit.

    Keeps PREDICTION (planned open-to-open gross) distinct from STRATEGY (realized net on actual exit).
    """
    dates = pack["dates"]
    t0, t1 = t + 1, t + 1 + hold
    if t1 >= len(dates):
        return None
    mask = elig_t & board_mask(pack["symbols"], boards)
    idx = np.where(mask & np.isfinite(scores_t))[0]
    if idx.size < 1:
        return None
    order = idx[np.lexsort((idx, scores_t[idx]))][::-1]  # score desc, tie -> lower symbol index
    picks = [int(j) for j in order[:k]]
    alloc = equity / float(k)
    pnl, invested, cash_out_total = 0.0, 0.0, 0.0
    n_entry, n_entry_blocked, n_no_lot = 0, 0, 0
    n_round_trip_clean, n_exit_carry, n_stuck, forced_hold_sum = 0, 0, 0, 0
    gross_list, names = [], []
    for j in picks:
        o0, planned_o1 = _open(pack, t0, j), _open(pack, t1, j)
        gross = (planned_o1 / o0 - 1.0) if (np.isfinite(o0) and o0 > 0 and np.isfinite(planned_o1) and planned_o1 > 0) else float("nan")
        gross_list.append(gross)  # PREDICTION target: planned horizon, independent of fills
        entry_reason = exec_reason(pack, t0, j)
        if entry_reason != "FILL":
            n_entry_blocked += 1
            names.append({"symbol": pack["symbols"][j], "status": entry_reason, "entered": False,
                          "gross": gross, "net": 0.0})
            continue
        # fee-aware lot sizing: shares cash (incl slippage) + buy fee must fit alloc
        buy_px = o0 * (1.0 + slip_side)
        lots = int(alloc // (LOT * buy_px))
        while lots > 0 and (lots * LOT * buy_px + _fee(lots * LOT * buy_px)) > alloc + 1e-9:
            lots -= 1
        if lots == 0:
            n_no_lot += 1
            names.append({"symbol": pack["symbols"][j], "status": "NO_LOT", "entered": False,
                          "gross": gross, "net": 0.0})
            continue
        shares = lots * LOT
        cost_in = shares * buy_px
        buy_fee = _fee(cost_in)
        cash_out = cost_in + buy_fee
        invested += cost_in
        cash_out_total += cash_out
        n_entry += 1
        # capital-path exit recovery
        exit_idx, exit_kind, block_reason, carry = _find_exit(pack, t1, j, exit_carry_max)
        forced_hold_sum += carry
        if exit_kind == "FILL":
            px_exit = _open(pack, exit_idx, j)
            sell_px = px_exit * (1.0 - slip_side)
            status = "FILL" if carry == 0 else ("FILL_CARRY_%d" % carry)
            if carry == 0:
                n_round_trip_clean += 1
            else:
                n_exit_carry += 1
        else:  # STUCK: assume liquidation at last available close, flagged
            px_exit = float(pack["close"][exit_idx, j])
            sell_px = px_exit * (1.0 - slip_side) if (np.isfinite(px_exit) and px_exit > 0) else o0
            status = "STUCK"
            n_stuck += 1
        proceeds = shares * sell_px
        fees = buy_fee + _fee(proceeds) + proceeds * stamp_duty_sell(dates[exit_idx])
        net = proceeds - cost_in - fees
        pnl += net
        names.append({"symbol": pack["symbols"][j], "status": status, "entered": True, "gross": gross,
                      "planned_exit": dates[t1], "actual_exit": dates[exit_idx],
                      "forced_hold_days": carry, "exit_block_reason": block_reason,
                      "net": round(net, 4), "net_pct": net / cost_in if cost_in else None})
    gross_arr = np.array([g for g in gross_list if np.isfinite(g)], dtype=float)
    assert cash_out_total <= equity + 1e-6, "invariant: total buy cash out (incl fees) <= equity"
    return {
        "signal_date": dates[t], "entry": dates[t0], "planned_exit": dates[t1], "exit": dates[t1],
        "hold": hold, "k": k, "n_pick": len(picks), "n_fill": n_entry,
        "n_entry": n_entry, "n_entry_blocked": n_entry_blocked, "n_no_lot": n_no_lot,
        "n_round_trip_clean": n_round_trip_clean, "n_exit_carry": n_exit_carry, "n_stuck": n_stuck,
        "forced_hold_days_total": forced_hold_sum,
        "mean_gross_topk": float(gross_arr.mean()) if gross_arr.size else None,
        "median_gross_topk": float(np.median(gross_arr)) if gross_arr.size else None,
        "hit_rate_gross": float((gross_arr > 0).mean()) if gross_arr.size else None,
        "invested": round(invested, 2), "cash_out_incl_fees": round(cash_out_total, 2),
        "cash_idle_frac": round(1.0 - cash_out_total / equity, 4) if equity else None,
        "pnl": round(pnl, 2), "ret_net": pnl / equity if equity else None,
        "names": names,
    }


def ew_period(pack, elig_t, t, hold, boards="ALL"):
    """Equal-weight eligible open-to-open benchmark for the same (t, hold). Gross (no cost)."""
    dates = pack["dates"]
    t0, t1 = t + 1, t + 1 + hold
    if t1 >= len(dates):
        return None
    mask = elig_t & board_mask(pack["symbols"], boards)
    js = np.where(mask)[0]
    if js.size < 1:
        return None
    a = np.asarray(pack["open"][t0, js], dtype=float)
    b = np.asarray(pack["open"][t1, js], dtype=float)
    good = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
    if not good.any():
        return None
    r = b[good] / a[good] - 1.0
    return {"mean_ew": float(r.mean()), "n": int(good.sum())}


def evaluate(pack, scores, elig, signal_indices, hold, ks, equity, boards="ALL", slip_side=SLIPPAGE, min_eligible=1):
    """Aggregate Top-K vs EW over the given signal indices for one horizon.

    `scores` is [T,N] (or a callable t->[N]); overlapping signal_indices are fine for gross means; the
    chained STRATEGY total steps non-overlapping (hold+1). Returns per-K summary.
    """
    per_k = {}
    for k in ks:
        gross_topk, gross_ew, excess, hits, net_rets = [], [], [], [], []
        # gross means over ALL signal days (prediction layer)
        for t in signal_indices:
            scores_t = scores(t) if callable(scores) else scores[t]
            if scores_t is None:
                continue
            elig_t = elig[t]
            if int(elig_t.sum()) < min_eligible:
                continue
            per = top_k_period(pack, scores_t, elig_t, t, hold, k, equity, boards, slip_side)
            ew = ew_period(pack, elig_t, t, hold, boards)
            if per is None or ew is None or per["mean_gross_topk"] is None:
                continue
            gross_topk.append(per["mean_gross_topk"])
            gross_ew.append(ew["mean_ew"])
            excess.append(per["mean_gross_topk"] - ew["mean_ew"])
            hits.append(per["hit_rate_gross"])
        # chained non-overlapping strategy net (capital layer)
        strat_total, n_chain, eq = 1.0, 0, float(equity)
        idx_sorted = sorted(signal_indices)
        last_used = -10 ** 9
        for t in idx_sorted:
            if t - last_used < (hold + 1):
                continue
            scores_t = scores(t) if callable(scores) else scores[t]
            if scores_t is None or int(elig[t].sum()) < min_eligible:
                continue
            per = top_k_period(pack, scores_t, elig[t], t, hold, k, eq, boards, slip_side)
            if per is None or per["ret_net"] is None:
                continue
            strat_total *= (1.0 + per["ret_net"])
            eq *= (1.0 + per["ret_net"])
            net_rets.append(per["ret_net"])
            n_chain += 1
            last_used = t
        ga = np.array(excess, dtype=float)
        per_k[k] = {
            "k": k, "hold": hold, "n_signal": len(gross_topk),
            "mean_gross_topk": float(np.mean(gross_topk)) if gross_topk else None,
            "mean_gross_ew": float(np.mean(gross_ew)) if gross_ew else None,
            "mean_excess_vs_ew": float(ga.mean()) if ga.size else None,
            "t_excess": float(ga.mean() / (ga.std(ddof=1) / np.sqrt(ga.size))) if ga.size > 2 and ga.std(ddof=1) > 0 else None,
            "hit_rate_gross": float(np.mean(hits)) if hits else None,
            "strategy_total_net": strat_total - 1.0, "n_chain": n_chain,
            "mean_net_per_period": float(np.mean(net_rets)) if net_rets else None,
            "turnover_one_way_per_period": 1.0,  # baseline fully replaces each rebalance
        }
    return per_k


__all__ = ["forward_label", "simple_eligible", "momentum_scores", "top_k_period", "ew_period", "evaluate"]
