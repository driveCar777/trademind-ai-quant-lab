"""Replay V26.8 research+validation books at a preview capital. Does not retune ML1. Does not write frozen READ. Does not read the denied window."""
from __future__ import print_function

import json
import os
import time

import numpy as np

from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.cn_a_share_ml_v25 import FIRST_PRED, OUT, RESEARCH, VALIDATION
from research_engine.cn_a_share_ml_v25.top_n_book import FEE_RESERVE_FULL, HOLD, UNIT_YUAN, eq_money_open_mark, eq_money_period, top_n_book
from research_engine.cn_a_share_ml_v25.scale_book import daily_curve
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix
from research_engine.ml1_live import SIGNALS

TAG = "V26_8_PREVIEW"
SCORES = os.path.join(OUT, "SCORES_ML1_LGBM.npy")
_ASSETS = None
_LIVE = None
SIGNAL_WEEK = "2026-08-28"
SIGNAL_MONTH = "2026-07-30"
ASOF_LIVE = "2026-09-04"


def _assets():
    global _ASSETS
    if _ASSETS is not None:
        return _ASSETS
    t0 = time.time()
    pack = load_pack()
    scores = np.load(SCORES, mmap_mode="r")
    elig, xok = eligible(pack, 20), exec_ok_matrix(pack)
    _ASSETS = (pack, scores, elig, xok)
    print(TAG, "assets", round(time.time() - t0, 1), "s", flush=True)
    return _ASSETS


def _live_assets():
    global _LIVE
    if _LIVE is not None:
        return _LIVE
    from research_engine.ml1_live.audit_open import _set_live_env
    from research_engine.ml1_live import panel
    t0 = time.time()
    _set_live_env(ASOF_LIVE)
    equities = panel.load_live_equities()
    cal = panel.load_live_calendar()
    days = panel.trading_days(cal)
    asof_session = max(d for d in days if d <= ASOF_LIVE)
    live_sessions = [d for d in days if d > panel.FROZEN_END]
    pack = panel.build_live_pack(equities, live_sessions, asof_session)
    elig, xok = eligible(pack, 20), exec_ok_matrix(pack)
    _LIVE = (pack, elig, xok)
    print(TAG, "live assets", round(time.time() - t0, 1), "s", flush=True)
    return _LIVE


def _scores_from_shadow(pack, day):
    """Reuse frozen SHADOW/SIGNAL scores. Does not import lightgbm. Does not rewrite signal files."""
    path = None
    for kind in ("SHADOW", "SIGNAL"):
        cand = os.path.join(SIGNALS, "%s_%s.json" % (kind, day))
        if os.path.isfile(cand):
            path = cand
            break
    if path is None:
        raise RuntimeError("NO_SHADOW %s" % day)
    names = json.load(open(path, encoding="utf-8")).get("names") or []
    mapped = dict((n["symbol"], float(n["score"])) for n in names if n.get("symbol") and n.get("score") is not None)
    sc = np.full(len(pack["symbols"]), np.nan, dtype=np.float64)
    for i, sym in enumerate(pack["symbols"]):
        if sym in mapped:
            sc[i] = mapped[sym]
    if int(np.isfinite(sc).sum()) < 200:
        raise RuntimeError("SCORES_TOO_THIN %s n=%d" % (day, int(np.isfinite(sc).sum())))
    return pack["dates"].index(day), sc


def _pts_pack(label, pts, extra=None):
    pts = [{"date": p.get("date"), "equity": p.get("equity")} for p in (pts or []) if p.get("date") is not None and p.get("equity") is not None]
    out = {"label": label, "start": pts[0]["date"] if pts else None, "end": pts[-1]["date"] if pts else None,
           "n": len(pts), "points": pts, "preview": True}
    if extra:
        out.update(extra)
    return out


def _holdings_from_snap(snap):
    rows = []
    for i, f in enumerate((snap or {}).get("names") or []):
        if f.get("status") != "FILL":
            continue
        rows.append({"rank": i + 1, "symbol": f.get("symbol"), "buy_price": f.get("open"),
                     "mark_price": f.get("mark_close"), "lots": f.get("lots"), "cost_in": f.get("cost_in"),
                     "buy_fee": f.get("buy_fee"), "unrealized": f.get("unrealized"), "status": f.get("status"),
                     "buy_date": (snap or {}).get("entry"), "mark_date": f.get("mark_date") or (snap or {}).get("mark_date")})
    return rows


def _closed_from_per(per, pack=None):
    rows = []
    if per is None:
        return rows
    dates = (pack or {}).get("dates") or []
    sidx = dict((s, i) for i, s in enumerate((pack or {}).get("symbols") or []))
    for i, n in enumerate(per.get("names") or []):
        if not n.get("yuan") and n.get("status") not in ("FILL", "FILL_CARRY", "STUCK"):
            continue
        buy_px = sell_px = None
        j = sidx.get(n.get("symbol"))
        if j is not None and dates:
            entry = per.get("entry")
            exit_d = n.get("exit") or per.get("exit")
            if entry in dates:
                o0 = float(pack["open"][dates.index(entry), j])
                if np.isfinite(o0) and o0 > 0:
                    buy_px = round(o0, 4)
            if exit_d in dates:
                o1 = float(pack["open"][dates.index(exit_d), j])
                if np.isfinite(o1) and o1 > 0:
                    sell_px = round(o1, 4)
        rows.append({"rank": i + 1, "symbol": n.get("symbol"), "lots": n.get("lots"),
                     "cost_in": n.get("yuan"), "pnl": n.get("net"), "status": n.get("status"),
                     "buy_date": per.get("entry"), "sell_date": n.get("exit") or per.get("exit"),
                     "buy_price": buy_px, "sell_price": sell_px})
    return rows


def _cannot_buy_note(capital):
    return "单位下限 ¥%s，这笔 ¥%s 买不进。本周/本月不会回落到官方 ¥20,000。" % (int(UNIT_YUAN), int(capital))


def replay_week_month(capital, n_target, monthly_contrib, boards, max_price, exposure):
    unit0 = max(UNIT_YUAN, float(capital) / float(n_target))
    pack, elig, xok = _live_assets()
    fee = FEE_RESERVE_FULL if float(exposure) >= 0.999 else 0.0
    t_w, sc_w = _scores_from_shadow(pack, SIGNAL_WEEK)
    snap = eq_money_open_mark(pack, sc_w, elig[t_w], xok, t_w, float(capital), float(exposure), unit0,
                              boards, float(max_price), True, fee, len(pack["dates"]) - 1)
    live_pts = (snap or {}).get("curve") or ([{"date": SIGNAL_WEEK, "equity": float(capital)}] if snap is None else [])
    live = _pts_pack("预览本周 ¥%s" % int(capital), live_pts, {
        "equity_end": float(capital) if snap is None else snap.get("mtm_equity"),
        "n_fill": 0 if snap is None else snap.get("n_fill"),
        "invested": 0.0 if snap is None else snap.get("invested"),
        "unrealized": 0.0 if snap is None else snap.get("unrealized"),
        "note": _cannot_buy_note(capital) if snap is None else None,
    })
    t_m, sc_m = _scores_from_shadow(pack, SIGNAL_MONTH)
    per = eq_money_period(pack, sc_m, elig[t_m], xok, t_m, float(capital), float(exposure), unit0,
                          boards, float(max_price), HOLD, True, fee)
    month_pts, month_end, hold_ret = [{"date": SIGNAL_MONTH, "equity": float(capital)}], float(capital), 0.0
    if per is not None:
        per["equity"] = round(float(capital) + per["pnl"], 2)
        per["deposits_to_date"] = 0.0
        cd, cv, _cm = daily_curve(pack, [per], float(capital))
        month_pts = [{"date": d, "equity": float(v)} for d, v in zip(cd, cv) if str(d) >= "2026-07-31"]
        month_end = per["equity"]
        hold_ret = per.get("ret")
    august = _pts_pack("预览本月 ¥%s" % int(capital), month_pts, {
        "equity_end": month_end,
        "total": hold_ret,
        "n_fill": 0 if per is None else per.get("n_fill"),
        "note": _cannot_buy_note(capital) if per is None else None,
    })
    return live, august, _holdings_from_snap(snap), _closed_from_per(per, pack)


def _curve(trades, capital):
    if not trades:
        return []
    pts = [{"date": trades[0]["entry"], "equity": float(capital)}]
    for tr in trades:
        pts.append({"date": tr.get("exit") or tr.get("entry"), "equity": tr.get("equity")})
    return pts


def _pack_book(book, capital, label):
    trades = book.get("trades") or []
    yrs = max(len(trades) * (HOLD + 1) / 242.0, 1e-9)
    total = float(book.get("total") or 0.0)
    pts = _curve(trades, capital)
    return {
        "label": label,
        "start": pts[0]["date"] if pts else None,
        "end": pts[-1]["date"] if pts else None,
        "n": len(pts),
        "n_periods": len(trades),
        "total": total,
        "cagr": float((1.0 + total) ** (1.0 / yrs) - 1.0) if trades else None,
        "equity_end": book.get("equity_end"),
        "deposits": book.get("deposits"),
        "invested_total": book.get("invested_total"),
        "profit_yuan": book.get("profit_yuan"),
        "points": pts,
        "periods": [{"signal_date": tr.get("signal_date"), "entry": tr.get("entry"), "exit": tr.get("exit"),
                     "n_fill": tr.get("n_fill"), "invested": tr.get("invested"), "pnl": tr.get("pnl"),
                     "ret": tr.get("ret"), "equity": tr.get("equity")} for tr in trades],
        "preview": True,
    }


def replay(capital, n_target=10, monthly_contrib=2000.0, boards="MAIN", max_price=100.0, exposure=1.0):
    capital = float(capital)
    n_target = int(n_target)
    monthly_contrib = float(monthly_contrib)
    max_price = float(max_price)
    if capital <= 0:
        raise ValueError("capital must be > 0")
    if n_target < 1:
        raise ValueError("n_target must be >= 1")
    pack, scores, elig, xok = _assets()
    dates = pack["dates"]
    a_r, b_r = max(RESEARCH[0], FIRST_PRED), RESEARCH[1]
    a_v, b_v = VALIDATION
    for d in (a_r, b_r, a_v, b_v):
        if d not in dates:
            raise RuntimeError("DATE_MISSING %s" % d)
    shell = dict(
        capital=capital,
        boards=boards,
        max_price=max_price,
        eq_money=True,
        exposure=float(exposure),
        topup=True,
        monthly_contrib=monthly_contrib,
        n_target=n_target,
    )
    t0 = time.time()
    bk_r = top_n_book(pack, scores, elig, xok, a_r, b_r, **shell)
    bk_v = top_n_book(pack, scores, elig, xok, a_v, b_v, **shell)
    out = {
        "preview": True,
        "official_capital": 20000.0,
        "capital": capital,
        "n_target": n_target,
        "monthly_contrib": monthly_contrib,
        "boards": boards,
        "max_price": max_price,
        "denied_window_read": False,
        "ticket_v": 2,
        "note": "按这笔钱重跑 V26.8 外壳；不是改 ML1，不是新合同，不覆盖官方 ¥20,000 账本。",
        "elapsed_s": round(time.time() - t0, 1),
        "research": _pack_book(bk_r, capital, "预览研究期 ¥%s" % int(capital)),
        "validation": _pack_book(bk_v, capital, "预览验证期 ¥%s" % int(capital)),
    }
    try:
        live, august, holds, aug_holds = replay_week_month(capital, n_target, monthly_contrib, boards, max_price, exposure)
        out["live"] = live
        out["august"] = august
        out["holdings"] = holds
        out["august_holdings"] = aug_holds
    except Exception as exc:
        out["live"] = {"label": "预览本周", "points": [], "preview": True, "error": str(exc)}
        out["august"] = {"label": "预览本月", "points": [], "preview": True, "error": str(exc)}
        out["holdings"] = []
        out["august_holdings"] = []
        out["note"] = out["note"] + " 本周/本月预览失败：%s" % exc
    print(TAG, "cap", int(capital), "val TWR", round(out["validation"]["total"], 4),
          "end", out["validation"]["equity_end"], "week n", (out.get("live") or {}).get("n_fill"),
          "s", round(time.time() - t0, 1), flush=True)
    return out
