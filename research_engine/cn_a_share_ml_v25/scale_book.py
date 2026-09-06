"""V26.8 — scaled unit (N_target cap) on the owner shell + multi-horizon analysis from a daily mark-to-market equity curve.
Contract: docs/research_engine/V26_8_ML1_SCALED_UNIT_CONTRACT.md. Grid selected on RESEARCH by per-period Sharpe; winner read once on VALIDATION."""
from __future__ import print_function

import datetime as dt
import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.cn_a_share_alpha_v2.books import ew_overlapping
from research_engine.cn_a_share_ml_v25 import FIRST_PRED, OUT, RESEARCH, VALIDATION
from research_engine.cn_a_share_ml_v25.top_n_book import HOLD, LOT, board_mask, summarize, top_n_book
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix

TAG = "V26_8_SCALE"
GRID = (10, 20, 40)
SHELL = dict(capital=20_000.0, boards="MAIN", max_price=100.0, eq_money=True, exposure=1.0, topup=True, monthly_contrib=2_000.0)


def daily_curve(pack, trades, capital):
    """Daily mark-to-market equity: cash + sum(shares x close) over open positions; deposits added on signal day."""
    dates, symbols = pack["dates"], pack["symbols"]
    sidx = dict((s, i) for i, s in enumerate(symbols))
    close = pack["close"]
    curve_d, curve_v, cash, prev_dep = [], [], float(capital), 0.0
    for k, tr in enumerate(trades):
        dep = tr.get("deposits_to_date", 0.0) - prev_dep
        prev_dep = tr.get("deposits_to_date", 0.0)
        cash += dep
        i_entry = dates.index(tr["entry"])
        i_next = dates.index(trades[k + 1]["entry"]) if k + 1 < len(trades) else min(dates.index(tr["exit"]) + 1, len(dates))
        pos = []
        for nm in tr["names"]:
            if nm.get("status", "").startswith("FILL") or nm.get("status") == "STUCK":
                j = sidx[nm["symbol"]]
                pos.append((j, nm["lots"] * LOT, nm["yuan"], nm["net"], dates.index(nm["exit"]) if nm.get("exit") else i_next))
                cash -= nm["yuan"]
        for d in range(i_entry, i_next):
            v = cash
            for j, sh, yuan, net, i_exit in pos:
                if d < i_exit:
                    c = float(close[d, j])
                    v += sh * c if np.isfinite(c) and c > 0 else yuan
                else:
                    v += yuan + net
            curve_d.append(dates[d]); curve_v.append(v)
        for j, sh, yuan, net, i_exit in pos:
            cash += yuan + net
    return curve_d, np.array(curve_v)


def _period_returns(cd, cv, key):
    """Return per calendar bucket = value at last day of bucket / value at last day of previous bucket - 1 (first bucket from its first day)."""
    groups, last_key, v_start, v_prev = [], None, None, None
    for d, v in zip(cd, cv):
        k = key(d)
        if k != last_key:
            if last_key is not None:
                groups.append((last_key, v_prev / v_start - 1.0))
            v_start = v_prev if v_prev is not None else v
            last_key = k
        v_prev = v
    groups.append((last_key, v_prev / v_start - 1.0))
    return groups


def _iso_week(d):
    y, w, _ = dt.date.fromisoformat(d).isocalendar()
    return "%d-W%02d" % (y, w)


def _stats(rs, label):
    rs = np.array([r for _, r in rs], dtype=float)
    if rs.size == 0:
        return None
    return {"horizon": label, "n": int(rs.size), "mean": float(rs.mean()), "median": float(np.median(rs)), "std": float(rs.std(ddof=1)) if rs.size > 1 else None,
            "worst": float(rs.min()), "best": float(rs.max()), "frac_positive": float((rs > 0).mean()),
            "p05": float(np.percentile(rs, 5)), "p95": float(np.percentile(rs, 95))}


def multi_horizon(cd, cv, deposits_by_date=None):
    v = np.asarray(cv, dtype=float)
    dr = v[1:] / v[:-1] - 1.0
    out = {"n_days": int(v.size), "first": cd[0], "last": cd[-1]}
    out["daily"] = _stats(list(zip(cd[1:], dr)), "day")
    dd = v / np.maximum.accumulate(v) - 1.0
    i_tr = int(np.argmin(dd)); i_pk = int(np.argmax(v[:i_tr + 1]))
    rec = next((cd[i] for i in range(i_tr, v.size) if v[i] >= v[i_pk]), None)
    out["daily_maxdd"] = {"maxdd": float(dd.min()), "peak": cd[i_pk], "trough": cd[i_tr], "recovered": rec,
                          "days_peak_to_trough": i_tr - i_pk, "days_to_recover": (cd.index(rec) - i_tr) if rec else None}
    out["weekly"] = _stats(_period_returns(cd, v, _iso_week), "week")
    out["monthly"] = _stats(_period_returns(cd, v, lambda d: d[:7]), "month")
    out["quarterly"] = _stats(_period_returns(cd, v, lambda d: "%s-Q%d" % (d[:4], (int(d[5:7]) - 1) // 3 + 1)), "quarter")
    yr = _period_returns(cd, v, lambda d: d[:4])
    out["yearly"] = _stats(yr, "year")
    out["calendar_years"] = dict((k, round(r, 4)) for k, r in yr)
    out["calendar_months_mean"] = {}
    mon = _period_returns(cd, v, lambda d: d[:7])
    for m in range(1, 13):
        rs = [r for k, r in mon if int(k[5:7]) == m]
        if rs:
            out["calendar_months_mean"]["%02d" % m] = {"mean": round(float(np.mean(rs)), 4), "n": len(rs), "frac_pos": round(float(np.mean([r > 0 for r in rs])), 2)}
    # rolling multi-year CAGR from any start day
    out["rolling"] = {}
    for yrs in (1, 3, 5):
        w = int(round(242 * yrs))
        if v.size > w + 5:
            cagr = (v[w:] / v[:-w]) ** (1.0 / yrs) - 1.0
            out["rolling"]["%dy" % yrs] = {"n_windows": int(cagr.size), "min": float(cagr.min()), "p10": float(np.percentile(cagr, 10)), "median": float(np.median(cagr)),
                                           "p90": float(np.percentile(cagr, 90)), "max": float(cagr.max()), "frac_negative": float((cagr < 0).mean())}
    out["twr_total"] = float(v[-1] / v[0] - 1.0)
    return out


def run_grid(pack, scores, elig, xok, a, b, ewm):
    res = {}
    for nt in GRID:
        bk = top_n_book(pack, scores, elig, xok, a, b, n_target=nt, **SHELL)
        s = summarize(bk, ewm)
        r = np.array([x["ret"] for x in bk["trades"]])
        s["sharpe_period"] = float(r.mean() / r.std(ddof=1)) if r.size > 2 else None
        s["mean_unit_yuan"] = float(np.mean([x["unit_yuan"] for x in bk["trades"]]))
        for k in ("equity_end", "deposits", "invested_total", "profit_yuan"):
            s[k] = bk.get(k)
        res[nt] = (s, bk)
        print(TAG, "N_target", nt, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items() if k in ("total", "cagr", "maxdd", "sharpe_period", "mean_excess_vs_ew", "t_excess", "mean_fill", "mean_unit_yuan", "profit_yuan")}, flush=True)
    return res


def irr_exact(trades, capital, contrib):
    d0 = dt.date.fromisoformat(trades[0]["signal_date"]); end = dt.date.fromisoformat(trades[-1]["exit"])
    flows, prev = [(0.0, capital)], 0.0
    for x in trades:
        d = x.get("deposits_to_date", 0.0)
        if d > prev:
            flows.append(((dt.date.fromisoformat(x["signal_date"]) - d0).days / 365.25, d - prev)); prev = d
    T = (end - d0).days / 365.25; E = trades[-1]["equity"]
    lo, hi = -0.9, 3.0
    for _ in range(200):
        m = (lo + hi) / 2; fv = sum(f * (1 + m) ** (T - t) for t, f in flows)
        lo, hi = (m, hi) if fv < E else (lo, m)
    return (lo + hi) / 2


def main():
    fn = os.path.join(OUT, "ML1_SCALED_UNIT_FULL_CONTRIB2K_MAIN_READ.json")
    if os.path.isfile(fn):
        raise SystemExit("V26.8 already read once; refusing")
    pack = load_pack(); dates = pack["dates"]
    scores = np.load(os.path.join(OUT, "SCORES_ML1_LGBM.npy"), mmap_mode="r")
    elig, xok = eligible(pack, 20), exec_ok_matrix(pack)
    c = np.asarray(pack["close"], dtype=float)
    elig_shell = elig & board_mask(pack["symbols"], "MAIN")[None, :] & np.isfinite(c) & (c <= 100.0)
    out = {"contract": "V26_8_ML1_SCALED_UNIT_CONTRACT.md", "grid": list(GRID), "selection": "research per-period Sharpe", "denied_window_read": False, "shell": SHELL}
    a, b = max(RESEARCH[0], FIRST_PRED), RESEARCH[1]
    ew = ew_overlapping(pack, elig_shell, xok, a, dates[dates.index(b) - HOLD - 1], HOLD)
    ewm_r = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
    grid = run_grid(pack, scores, elig, xok, a, b, ewm_r)
    out["research_grid"] = dict((str(k), v[0]) for k, v in grid.items())
    winner = max(GRID, key=lambda k: grid[k][0]["sharpe_period"])
    out["winner_n_target"] = winner
    print(TAG, "WINNER N_target", winner, flush=True)
    bk_r = grid[winner][1]
    cd, cv = daily_curve(pack, bk_r["trades"], SHELL["capital"])
    out["research"] = dict(grid[winner][0]); out["research"]["irr"] = irr_exact(bk_r["trades"], SHELL["capital"], SHELL["monthly_contrib"])
    out["research"]["multi_horizon"] = multi_horizon(cd, cv)
    # single validation read of the winner
    a2, b2 = VALIDATION
    ew = ew_overlapping(pack, elig_shell, xok, a2, dates[dates.index(b2) - HOLD - 1], HOLD)
    ewm_v = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
    bk_v = top_n_book(pack, scores, elig, xok, a2, b2, n_target=winner, **SHELL)
    s = summarize(bk_v, ewm_v)
    r = np.array([x["ret"] for x in bk_v["trades"]]); s["sharpe_period"] = float(r.mean() / r.std(ddof=1))
    for k in ("equity_end", "deposits", "invested_total", "profit_yuan"):
        s[k] = bk_v.get(k)
    s["irr"] = irr_exact(bk_v["trades"], SHELL["capital"], SHELL["monthly_contrib"])
    cd2, cv2 = daily_curve(pack, bk_v["trades"], SHELL["capital"])
    s["multi_horizon"] = multi_horizon(cd2, cv2)
    out["validation"] = s
    out["validation_trades"] = [dict((k, v) for k, v in tr.items() if k != "names") for tr in bk_v["trades"]]
    out["research_trades"] = [dict((k, v) for k, v in tr.items() if k != "names") for tr in bk_r["trades"]]
    viable = bool(s["total"] > 0 and (s["mean_excess_vs_ew"] or 0) > 0)
    out["label"] = "ML1_SCALED_UNIT_N%d_FULL_CONTRIB2K_MAIN_%s" % (winner, "VIABLE_HISTORICAL" if viable else "NOT_VIABLE")
    np.save(os.path.join(OUT, "V26_8_DAILY_CURVE_RESEARCH.npy"), np.array(list(zip(cd, cv)), dtype=object), allow_pickle=True)
    np.save(os.path.join(OUT, "V26_8_DAILY_CURVE_VALIDATION.npy"), np.array(list(zip(cd2, cv2)), dtype=object), allow_pickle=True)
    dump_json(fn, out)
    print(TAG, "validation", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items() if k in ("total", "cagr", "maxdd", "sharpe_period", "mean_excess_vs_ew", "t_excess", "beat_ew_periods", "mean_fill", "profit_yuan", "irr")}, flush=True)
    print(TAG, "DONE", out["label"], flush=True)


if __name__ == "__main__":
    main()
