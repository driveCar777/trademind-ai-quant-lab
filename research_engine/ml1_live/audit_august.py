"""Calendar August 2026 of the V26.8 live book. Diagnostic only. Does not retune.

August 2026 is the first month after the V28 last signal (2026-07-30).
Holding = that 20-session book (entry next open, exit open t+21) plus 2026-08-31 new entry.
"""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_ml_v25.scale_book import daily_curve
from research_engine.cn_a_share_ml_v25.top_n_book import FEE_RESERVE_FULL, HOLD, UNIT_YUAN, board_mask, eq_money_open_mark, eq_money_period
from research_engine.ml1_live import FEATURES, LEDGER_DIR, MARGIN_NORM, HOLDERS_NORM, HOLDERS_RAW, CALENDAR_CSV
from research_engine.ml1_live.audit_open import _set_live_env

TAG = "AUDIT_AUG2026"
CAPITAL = 20_000.0
ASOF = "2026-09-04"
SIGNAL_JUL = "2026-07-30"
SIGNAL_AUG = "2026-08-28"


def _score(pack, feats, elig, xok, d):
    from research_engine.ml1_live.score import score_session
    t = pack["dates"].index(d)
    _, sc = score_session(pack, feats, elig, xok, t, 5_000_000.0, tag="SHADOW")
    return t, sc


def _ew_curve(pack, elig, start, end, boards="MAIN", max_price=100.0):
    dates, close = pack["dates"], pack["close"]
    i0, i1 = dates.index(start), dates.index(end)
    m0 = elig[i0] & board_mask(pack["symbols"], boards)
    c0 = np.asarray(close[i0], dtype=float)
    m0 = m0 & np.isfinite(c0) & (c0 > 0) & (c0 <= max_price)
    eq, curve = 1.0, [{"date": dates[i0], "ew": 1.0, "n": int(m0.sum())}]
    for i in range(i0 + 1, i1 + 1):
        c1 = np.asarray(close[i], dtype=float)
        ok = m0 & np.isfinite(c1) & (c1 > 0)
        if int(ok.sum()) < 50:
            r = 0.0
        else:
            r = float(np.nanmean(c1[ok] / c0[ok] - 1.0))
        eq *= 1.0 + r
        c0 = np.where(ok, c1, c0)
        curve.append({"date": dates[i], "ew": round(eq, 6), "n": int(ok.sum())})
        m0 = ok
    return curve


def main():
    from research_engine.ml1_live import panel
    from research_engine.ml1_live.score import eligibility, features_for

    _set_live_env(ASOF)
    equities = panel.load_live_equities()
    cal = panel.load_live_calendar()
    days = panel.trading_days(cal)
    asof_session = max(d for d in days if d <= ASOF)
    live_sessions = [d for d in days if d > panel.FROZEN_END]
    pack = panel.build_live_pack(equities, live_sessions, asof_session)
    feats, _ = features_for(pack, force=False)
    elig, xok = eligibility(pack)
    dates = pack["dates"]

    t_jul, sc_jul = _score(pack, feats, elig, xok, SIGNAL_JUL)
    unit = max(UNIT_YUAN, CAPITAL / 10)
    per = eq_money_period(pack, sc_jul, elig[t_jul], xok, t_jul, CAPITAL, 1.0, unit, "MAIN", 100.0, HOLD, True, FEE_RESERVE_FULL)
    if per is None:
        raise SystemExit("JUL_PERIOD_INCOMPLETE")
    per["equity"] = round(CAPITAL + per["pnl"], 2)
    per["deposits_to_date"] = 0.0
    cd, cv, cm = daily_curve(pack, [per], CAPITAL)
    aug_mask = [(d, v, m) for d, v, m in zip(cd, cv, cm) if d.startswith("2026-08")]

    t_aug, sc_aug = _score(pack, feats, elig, xok, SIGNAL_AUG)
    equity2 = per["equity"] + 2000.0
    last_aug = dates.index("2026-08-31")
    snap = eq_money_open_mark(pack, sc_aug, elig[t_aug], xok, t_aug, equity2, 1.0, max(UNIT_YUAN, equity2 / 10),
                             "MAIN", 100.0, True, FEE_RESERVE_FULL, last_aug)

    # August session closes: 08-03..08-28 from first book; 08-31 from second book
    first_aug_eq = None
    last_jul_hold = None
    for d, v, _ in zip(cd, cv, cm):
        if d < "2026-08-01":
            last_jul_hold = v
        if d.startswith("2026-08") and first_aug_eq is None:
            first_aug_eq = v
    eq_0831 = snap["curve"][0]["equity"] if snap and snap["curve"] else None
    # calendar August: start = close 08-03 (first session) vs start-of-month capital
    # money August = last August mark / first August mark - 1, plus 08-31
    eq_0828 = aug_mask[-1][1] if aug_mask else None
    # After 08-28 sale, cash = per["equity"] until 08-31 buy. 08-31 MTM is snap.
    month_start = last_jul_hold if last_jul_hold is not None else CAPITAL
    month_end = eq_0831 if eq_0831 is not None else eq_0828
    # 08-28 deposit is a cash flow on signal day (not a return). TWR: strip +2000 before 08-31 buy.
    twr_to_0828 = (eq_0828 / month_start - 1.0) if month_start and eq_0828 else None
    twr_0831 = (eq_0831 / (per["equity"] + 2000.0) - 1.0) if eq_0831 else None
    money_aug = month_end - month_start
    # include the 2k deposit in money end but not in TWR
    money_end_with_dep = (snap["mtm_equity"] if snap else eq_0828)

    ew = _ew_curve(pack, elig, per["entry"], per["exit"])
    ew_aug = [r for r in ew if r["date"].startswith("2026-08")]
    ew_month = None
    if ew_aug:
        # EW from last July hold session to 08-28
        pre = [r for r in ew if r["date"] < "2026-08-01"]
        ew0 = pre[-1]["ew"] if pre else ew[0]["ew"]
        ew_month = ew_aug[-1]["ew"] / ew0 - 1.0

    names = []
    for nm in per["names"]:
        names.append({k: nm[k] for k in nm if k != "names"})

    out = {
        "month": "2026-08",
        "contract": "ML1_SCALED_UNIT_N10_FULL_CONTRIB2K_MAIN",
        "capital_start_jul30": CAPITAL,
        "jul30_period": {
            "signal": SIGNAL_JUL, "entry": per["entry"], "exit": per["exit"],
            "n_sel": per["n_sel"], "n_fill": per["n_fill"], "n_exit_carry": per.get("n_exit_carry"),
            "n_stuck": per.get("n_stuck"), "invested": per["invested"], "pnl": per["pnl"],
            "ret": per["ret"], "equity_end": per["equity"], "cash_idle_frac": per.get("cash_idle_frac"),
            "names": names,
        },
        "aug28_new_book": {
            "signal": SIGNAL_AUG, "entry": snap["entry"] if snap else None,
            "capital_after_deposit": equity2, "n_fill": snap["n_fill"] if snap else None,
            "invested": snap["invested"] if snap else None, "mtm_0831": snap["mtm_equity"] if snap else None,
            "unrealized_one_day": snap["unrealized"] if snap else None,
            "names": (snap["names"] if snap else None),
        },
        "august_calendar": {
            "sessions": [d for d in dates if d.startswith("2026-08")],
            "n_sessions": sum(1 for d in dates if d.startswith("2026-08")),
            "equity_0731_close": last_jul_hold,
            "equity_first_aug_session": first_aug_eq,
            "equity_0828_after_sale": eq_0828,
            "equity_0831_mtm": eq_0831,
            "equity_0831_with_2k_deposit": money_end_with_dep,
            "twr_0731_to_0828": twr_to_0828,
            "twr_0831_vs_post_deposit": twr_0831,
            "money_0731_to_0831_ex_deposit": (eq_0831 - 2000.0 - month_start) if eq_0831 and month_start else None,
            "curve_jul_book_in_august": [{"date": d, "equity": v} for d, v, _ in aug_mask],
            "main_ew_hold_window": ew_month,
            "main_ew_hold_entry_to_exit": (ew[-1]["ew"] / ew[0]["ew"] - 1.0) if ew else None,
        },
    }
    path = os.path.join(LEDGER_DIR, "AUDIT_2026_08.json")
    dump_json(path, out)
    print(TAG, "JUL", per["entry"], "->", per["exit"], "pnl", per["pnl"], "ret", round(per["ret"] * 100, 2), "%",
          "fill", per["n_fill"], flush=True)
    print(TAG, "AUG TWR 0731->0828", None if twr_to_0828 is None else round(twr_to_0828 * 100, 2),
          "%  0831 mtm", eq_0831, "EW hold", None if ew_month is None else round(ew_month * 100, 2), "%", flush=True)
    print(TAG, "wrote", path, flush=True)
    return out


if __name__ == "__main__":
    os.environ.setdefault("TRADEMIND_V25_FEAT_CACHE", FEATURES)
    main()
