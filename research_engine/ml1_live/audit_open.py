"""Numbers, not narration: reproduce V26.8 validation, then mark the live 2026-08-28 book to last close.

Does not retune ML1 or V26.8. Writes live/ledger/AUDIT_OPEN.json.
"""
from __future__ import print_function

import json
import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.cost import SLIPPAGE
from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.cn_a_share_ml_v25 import OUT, VALIDATION
from research_engine.cn_a_share_ml_v25.scale_book import SHELL
from research_engine.cn_a_share_ml_v25.top_n_book import FEE_RESERVE_FULL, HOLD, LOT, UNIT_YUAN, eq_money_open_mark, eq_money_select, top_n_book
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix
from research_engine.ml1_live import FEATURES, LEDGER_DIR, MARGIN_NORM, HOLDERS_NORM, HOLDERS_RAW, CALENDAR_CSV
from research_engine.ml1_live.shortlist import write_shortlist_eq_money

TAG = "AUDIT_OPEN"
READ = os.path.join(OUT, "ML1_SCALED_UNIT_FULL_CONTRIB2K_MAIN_READ.json")
SCORES = os.path.join(OUT, "SCORES_ML1_LGBM.npy")


def _set_live_env(asof):
    os.environ["TRADEMIND_MARGIN_END"] = asof
    os.environ["TRADEMIND_MARGIN_NORM"] = MARGIN_NORM
    os.environ["TRADEMIND_MARGIN_CALENDAR"] = CALENDAR_CSV
    os.environ["TRADEMIND_HOLDERS_RAW"] = HOLDERS_RAW
    os.environ["TRADEMIND_HOLDERS_NORM"] = HOLDERS_NORM
    os.environ["TRADEMIND_HOLDERS_NOTICE_CUTOFF"] = asof
    os.environ["TRADEMIND_V25_FEAT_CACHE"] = FEATURES


def _close_est_lots(pack, scores_t, elig_t, t, equity, unit):
    from research_engine.cn_a_share_ml_v25.top_n_book import board_mask
    symbols = pack["symbols"]
    c = np.asarray(pack["close"][t], dtype=float)
    m = elig_t & board_mask(symbols, "MAIN") & np.isfinite(scores_t) & np.isfinite(c) & (c <= 100.0)
    idx = np.where(m)[0]
    order = idx[np.lexsort((idx, scores_t[idx]))][::-1]
    n = int(equity // unit)
    picks = []
    for j in order:
        j = int(j)
        px = float(c[j])
        lots = int(unit // (LOT * px)) if px > 0 else 0
        if lots == 0:
            continue
        picks.append([j, lots])
        if len(picks) >= n:
            break
    if picks:
        budget = equity - FEE_RESERVE_FULL - sum(l * LOT * float(c[j]) for j, l in picks)
        while True:
            added = False
            for p in picks:
                lc = LOT * float(c[p[0]])
                if lc <= budget:
                    p[1] += 1
                    budget -= lc
                    added = True
            if not added:
                break
    return dict((symbols[j], lots) for j, lots in picks)


def close_vs_open_lots(pack, scores, elig, trades, capital_path):
    """How often signal-day close lots differ from next-open lots (V26.8; diagnostic, not a retune)."""
    dates, symbols = pack["dates"], pack["symbols"]
    n_same, n_diff, n_name_diff, gaps = 0, 0, 0, []
    for tr, eq0 in zip(trades, capital_path):
        t = dates.index(tr["signal_date"])
        unit = max(UNIT_YUAN, eq0 / 10)
        sel = eq_money_select(pack, scores[t], elig[t], t, eq0, 1.0, unit, "MAIN", 100.0, True, FEE_RESERVE_FULL)
        if sel is None:
            continue
        open_map = dict((symbols[j], lots) for j, lots in sel["picks"])
        close_map = _close_est_lots(pack, scores[t], elig[t], t, eq0, unit)
        if set(close_map) != set(open_map):
            n_name_diff += 1
        if close_map == open_map:
            n_same += 1
        else:
            n_diff += 1
        for s in open_map:
            j = symbols.index(s)
            c0, o1 = float(pack["close"][t, j]), float(pack["open"][t + 1, j])
            if c0 > 0 and np.isfinite(o1):
                gaps.append(o1 / c0 - 1.0)
    g = np.array(gaps, dtype=float)
    return {"periods": len(trades), "lots_and_names_identical": n_same, "any_diff": n_diff, "name_set_diff": n_name_diff,
            "gap_mean": float(g.mean()) if g.size else None, "gap_p05": float(np.percentile(g, 5)) if g.size else None,
            "gap_p95": float(np.percentile(g, 95)) if g.size else None, "gap_abs_mean": float(np.abs(g).mean()) if g.size else None}


def reproduce_v26_8():
    frozen = json.load(open(READ, encoding="utf-8"))
    pack = load_pack()
    scores = np.load(SCORES, mmap_mode="r")
    elig, xok = eligible(pack, 20), exec_ok_matrix(pack)
    a, b = VALIDATION
    bk = top_n_book(pack, scores, elig, xok, a, b, n_target=10, **SHELL)
    want = frozen["validation"]
    got_total = float(bk["total"])
    got_eq = float(bk["equity_end"])
    got_n = len(bk["trades"])
    out = {
        "window": [a, b],
        "n_periods": got_n,
        "total": got_total,
        "equity_end": got_eq,
        "profit_yuan": bk.get("profit_yuan"),
        "read_total": want["total"],
        "read_equity_end": want["equity_end"],
        "read_n_periods": want["n_periods"],
        "delta_total": got_total - want["total"],
        "delta_equity": got_eq - want["equity_end"],
        "match": abs(got_total - want["total"]) < 1e-9 and abs(got_eq - want["equity_end"]) < 0.02 and got_n == want["n_periods"],
        "last3": [{"signal_date": tr["signal_date"], "ret": tr["ret"], "pnl": tr["pnl"], "invested": tr["invested"], "n_fill": tr["n_fill"]} for tr in bk["trades"][-3:]],
    }
    pre, last_m = [], None
    equity = float(SHELL["capital"])
    for tr in bk["trades"]:
        if last_m is not None and tr["signal_date"][:7] != last_m:
            equity += SHELL["monthly_contrib"]
        pre.append(equity)
        equity = float(tr["equity"])
        last_m = tr["signal_date"][:7]
    out["close_vs_open"] = close_vs_open_lots(pack, scores, elig, bk["trades"], pre)
    print(TAG, "V26.8 replay", "MATCH" if out["match"] else "MISMATCH", "n", got_n, "TWR", round(got_total, 6), "eq", round(got_eq, 2), flush=True)
    return out


def live_open_audit():
    from research_engine.ml1_live import panel
    from research_engine.ml1_live.score import eligibility, features_for, score_session

    asof = "2026-09-04"
    _set_live_env(asof)
    equities = panel.load_live_equities()
    cal = panel.load_live_calendar()
    days = panel.trading_days(cal)
    asof_session = max(d for d in days if d <= asof)
    live_sessions = [d for d in days if d > panel.FROZEN_END]
    pack = panel.build_live_pack(equities, live_sessions, asof_session)
    feats, _ = features_for(pack, force=False)
    elig, xok = eligibility(pack)
    dates = pack["dates"]
    t = dates.index("2026-08-28")
    _, sc = score_session(pack, feats, elig, xok, t, 5_000_000.0, tag="SHADOW")
    unit = max(UNIT_YUAN, 20000.0 / 10)
    snap = eq_money_open_mark(pack, sc, elig[t], xok, t, 20000.0, 1.0, unit, "MAIN", 100.0, True, FEE_RESERVE_FULL, len(dates) - 1)
    close_est = write_shortlist_eq_money(pack, sc, elig[t], t, capital=20000.0, exposure=1.0, boards="MAIN",
                                        max_price=100.0, tag="SHORTLIST_SHADOW", topup=True, n_target=10)
    by_close = dict((r["symbol"], r) for r in close_est["names"])
    lot_diffs = []
    for row in snap["names"]:
        est = by_close.get(row["symbol"])
        est_lots = est["lots_100_est"] if est else None
        lot_diffs.append({"symbol": row["symbol"], "open_lots": row["lots"], "close_est_lots": est_lots,
                          "lot_delta": (row["lots"] - est_lots) if est_lots is not None else None,
                          "open": row.get("open"), "status": row["status"], "unrealized": row.get("unrealized")})
    extra_close = [s for s in by_close if s not in set(r["symbol"] for r in snap["names"])]
    extra_open = [r["symbol"] for r in snap["names"] if r["symbol"] not in by_close]
    # same-name close vs next-open price move
    t0 = t + 1
    px_gap = []
    for row in snap["names"]:
        j = pack["symbols"].index(row["symbol"])
        c0 = float(pack["close"][t, j])
        o1 = float(pack["open"][t0, j])
        px_gap.append({"symbol": row["symbol"], "signal_close": round(c0, 4), "entry_open": round(o1, 4),
                       "gap": round(o1 / c0 - 1.0, 6) if c0 > 0 else None})
    out = {
        "signal_date": "2026-08-28",
        "entry": snap["entry"],
        "mark_date": snap["mark_date"],
        "sessions_held": len(snap["curve"]),
        "hold_target": HOLD,
        "n_fill": snap["n_fill"],
        "invested_open": snap["invested"],
        "close_est_invested": close_est["est_invested_yuan"],
        "invested_delta": round(snap["invested"] - close_est["est_invested_yuan"], 2),
        "buy_fees": snap["buy_fees"],
        "cash": snap["cash"],
        "mtm_equity": snap["mtm_equity"],
        "unrealized": snap["unrealized"],
        "ret_unrealized": snap["ret_unrealized"],
        "names_only_in_close_est": extra_close,
        "names_only_in_open": extra_open,
        "lot_diffs": lot_diffs,
        "overnight_gaps": px_gap,
        "curve": snap["curve"],
        "slippage": SLIPPAGE,
        "unit": unit,
    }
    print(TAG, "live OPEN", snap["entry"], "->", snap["mark_date"], "fills", snap["n_fill"],
          "invested", snap["invested"], "mtm", snap["mtm_equity"], "u", snap["unrealized"], flush=True)
    return out, pack, sc, elig, xok, t


def main():
    replay = reproduce_v26_8()
    live, pack, sc, elig, xok, t = live_open_audit()
    out = {"tag": TAG, "v26_8_replay": replay, "live_open": live}
    path = os.path.join(LEDGER_DIR, "AUDIT_OPEN.json")
    dump_json(path, out)
    print(TAG, "wrote", path, flush=True)
    return out


if __name__ == "__main__":
    main()
