"""A-share paper desk: read live JSON, preview V26.8 lots for a new capital. No orders."""
from __future__ import print_function

import csv
import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LIVE = ROOT / "data" / "market" / "cn_a_share" / "live"
SIGNALS = LIVE / "signals"
LEDGER = LIVE / "ledger"
SETTINGS = LIVE / "PAPER_SETTINGS.json"
V26_READ = ROOT / "data" / "market" / "research_engine" / "cn_a_share_ml_v25" / "ML1_SCALED_UNIT_FULL_CONTRIB2K_MAIN_READ.json"

LOT = 100
UNIT = 2000.0
FEE_RESERVE = 200.0
DEFAULTS = {
    "capital": 20000.0,
    "monthly_contrib": 2000.0,
    "max_price": 100.0,
    "n_target": 10,
    "boards": "MAIN",
    "exposure": 1.0,
}

BOARD_PREFIX = {
    "ALL": None,
    "MAIN_CHINEXT": ("sh.60", "sz.00", "sz.30"),
    "MAIN": ("sh.60", "sz.00"),
}


def _read(path):
    if not path or not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _latest(folder, prefix):
    if not os.path.isdir(folder):
        return None
    names = [n for n in os.listdir(folder) if n.startswith(prefix) and n.endswith(".json")]
    names.sort()
    return str(Path(folder) / names[-1]) if names else None


def load_settings():
    raw = _read(SETTINGS) or {}
    out = dict(DEFAULTS)
    for k in DEFAULTS:
        if k in raw and raw[k] is not None:
            out[k] = raw[k]
    return out


def save_settings(payload):
    cur = load_settings()
    if payload.get("capital") is not None:
        cap = float(payload["capital"])
        if cap <= 0:
            raise ValueError("capital must be > 0")
        cur["capital"] = cap
    if payload.get("monthly_contrib") is not None:
        cur["monthly_contrib"] = float(payload["monthly_contrib"])
    if payload.get("max_price") is not None:
        cur["max_price"] = float(payload["max_price"])
    if payload.get("n_target") is not None:
        nt = int(payload["n_target"])
        if nt < 1:
            raise ValueError("n_target must be >= 1")
        cur["n_target"] = nt
    if payload.get("boards") in BOARD_PREFIX:
        cur["boards"] = payload["boards"]
    cur["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    LIVE.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS, "w", encoding="utf-8") as fh:
        json.dump(cur, fh, indent=1, ensure_ascii=False)
    return cur


def _board_ok(symbol, boards):
    pref = BOARD_PREFIX.get(boards, BOARD_PREFIX["MAIN"])
    if pref is None:
        return True
    return symbol.startswith(pref)


def preview_lots(universe, capital, n_target=10, max_price=100.0, boards="MAIN", exposure=1.0):
    """Same arithmetic as write_shortlist_eq_money. universe = SIGNAL names with score+last_close."""
    capital = float(capital)
    if capital <= 0:
        raise ValueError("capital must be > 0")
    unit = max(UNIT, capital / float(n_target)) if n_target else UNIT
    n = int((exposure * capital) // unit)
    ranked = []
    for row in universe:
        px = row.get("last_close")
        sc = row.get("score")
        sym = row.get("symbol")
        if not sym or px is None or sc is None:
            continue
        px = float(px)
        if px <= 0 or px > float(max_price) or not _board_ok(sym, boards):
            continue
        ranked.append((float(sc), sym, px))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    rows, skipped = [], 0
    for sc, sym, px in ranked:
        lots = int(unit // (LOT * px))
        if lots == 0:
            skipped += 1
            continue
        rows.append({"rank": len(rows) + 1, "symbol": sym, "score": sc, "last_close": px,
                     "lots_100_est": lots, "est_yuan": round(lots * LOT * px, 2)})
        if len(rows) >= n:
            break
    if rows and exposure >= 0.999:
        budget = exposure * capital - FEE_RESERVE - sum(r["est_yuan"] for r in rows)
        while True:
            added = False
            for r in rows:
                lc = LOT * r["last_close"]
                if lc <= budget:
                    r["lots_100_est"] += 1
                    r["est_yuan"] = round(r["est_yuan"] + lc, 2)
                    budget -= lc
                    added = True
            if not added:
                break
    invested = round(sum(r["est_yuan"] for r in rows), 2)
    return {
        "contract": "ML1_SCALED_UNIT_N%d_FULL_CONTRIB2K_MAIN" % int(n_target),
        "capital": capital,
        "unit_yuan": round(unit, 2),
        "n_target": int(n_target),
        "n_names": len(rows),
        "est_invested_yuan": invested,
        "cash_yuan": round(capital - invested, 2),
        "skipped_price_too_high": skipped,
        "preview": True,
        "boards": boards,
        "max_price": float(max_price),
        "names": rows,
        "note": "手数按最近一次 SIGNAL 收盘重算；开盘手数以开盘价为准。改 N 只是预览。",
    }


def _august_summary(raw):
    if not raw:
        return None
    cal = raw.get("august_calendar") or {}
    jul = raw.get("jul30_period") or {}
    return {
        "month": raw.get("month"),
        "hold_pnl": jul.get("pnl"),
        "hold_ret": jul.get("ret"),
        "hold_entry": jul.get("entry"),
        "hold_exit": jul.get("exit"),
        "hold_n_fill": jul.get("n_fill"),
        "ew_hold": cal.get("main_ew_hold_entry_to_exit"),
        "aug_twr_0803_0828": cal.get("aug_session_twr_0803_to_0828"),
        "money_0731_close": cal.get("money_0731_close"),
        "money_0803": cal.get("money_0803"),
        "money_0825_peak": cal.get("money_0825_peak"),
        "money_0828_settled": cal.get("money_0828_settled"),
        "curve": cal.get("money_curve") or cal.get("curve_jul_book_in_august") or [],
    }


def _open_period(ledger):
    for p in (ledger or {}).get("periods") or []:
        if p.get("status") == "OPEN":
            return p
    return {}


def _trade_curve(trades, start_equity=20000.0):
    if not trades:
        return []
    first = trades[0]
    pts = [{"date": first.get("entry"), "equity": float(start_equity)}]
    for t in trades:
        pts.append({"date": t.get("exit") or t.get("entry"), "equity": t.get("equity")})
    return [p for p in pts if p.get("date") and p.get("equity") is not None]


def _curve_pack(label, points, extra=None):
    pts = [{"date": p.get("date"), "equity": p.get("equity")} for p in (points or []) if p.get("date") is not None and p.get("equity") is not None]
    out = {
        "label": label,
        "start": pts[0]["date"] if pts else None,
        "end": pts[-1]["date"] if pts else None,
        "n": len(pts),
        "points": pts,
    }
    if extra:
        out.update(extra)
    return out


_STOCK_NAMES = None
_TRADING_DAYS = None


def _stock_names():
    global _STOCK_NAMES
    if _STOCK_NAMES is not None:
        return _STOCK_NAMES
    _STOCK_NAMES = {}
    path = LIVE / "basics.csv"
    if path.is_file():
        with open(path, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("symbol"):
                    _STOCK_NAMES[row["symbol"]] = row.get("name") or ""
    return _STOCK_NAMES


def _trading_days():
    global _TRADING_DAYS
    if _TRADING_DAYS is not None:
        return _TRADING_DAYS
    days = []
    path = LIVE / "calendar.csv"
    if path.is_file():
        with open(path, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                flag = str(row.get("is_trading_day") or "")
                if flag in ("1", "True", "true"):
                    days.append(row.get("calendar_date"))
    _TRADING_DAYS = days
    return days


def _plus_sessions(day, n):
    if not day:
        return None
    days = _trading_days()
    if day not in days:
        return None
    i = days.index(day) + int(n)
    if i < 0 or i >= len(days):
        return None
    return days[i]


def _px(v):
    if v is None:
        return "—"
    try:
        return "%.2f" % float(v)
    except (TypeError, ValueError):
        return "—"


def _yuan(v):
    if v is None:
        return "—"
    try:
        return "¥%.2f" % float(v)
    except (TypeError, ValueError):
        return "—"


def _ticket_open(row, meta):
    names = _stock_names()
    lots = int(row.get("lots") or 0)
    shares = lots * LOT
    buy_date = row.get("buy_date") or meta.get("entry")
    mark_date = row.get("mark_date") or meta.get("mark_date")
    sell_date = row.get("sell_date") or meta.get("exit_date")
    recipe = (
        "%s 开盘买入 %s 手（%s 股）@%s，金额 %s，佣金 %s。"
        "%s %s @%s。预计 %s 开盘卖出。系统不发单。"
        % (buy_date or "买入日", lots, shares, _px(row.get("buy_price")),
           _yuan(row.get("cost_in")), _yuan(row.get("buy_fee")),
           "现价" if not row.get("sell_price") else "卖出",
           mark_date or sell_date or "市值日",
           _px(row.get("sell_price") if row.get("sell_price") is not None else row.get("mark_price")),
           sell_date or "约 20 个交易日后")
    )
    out = dict(row)
    out.update({
        "name": names.get(row.get("symbol"), ""),
        "shares": shares,
        "buy_date": buy_date,
        "mark_date": mark_date,
        "sell_date": sell_date,
        "side": "HOLD",
        "kind": "OPEN",
        "recipe": recipe,
    })
    return out


def _ticket_closed(row, meta):
    names = _stock_names()
    lots = int(row.get("lots") or 0)
    shares = lots * LOT
    buy_date = row.get("buy_date") or meta.get("entry")
    sell_date = row.get("sell_date") or row.get("exit") or meta.get("exit")
    cost = row.get("cost_in") if row.get("cost_in") is not None else row.get("yuan")
    pnl = row.get("pnl") if row.get("pnl") is not None else row.get("net")
    buy_px = row.get("buy_price")
    if buy_px is None and cost and shares:
        buy_px = round(float(cost) / shares, 4)
    recipe = (
        "%s 开盘买入 %s 手（%s 股）@%s，成本 %s。"
        "%s 开盘卖出 @%s，净利 %s。已平仓，系统未发单。"
        % (buy_date or "买入日", lots, shares, _px(buy_px),
           _yuan(cost), sell_date or "卖出日", _px(row.get("sell_price")),
           _yuan(pnl))
    )
    out = dict(row)
    if out.get("pnl") is None:
        out["pnl"] = pnl
    if out.get("cost_in") is None:
        out["cost_in"] = cost
    if out.get("buy_price") is None:
        out["buy_price"] = buy_px
    out.update({
        "name": names.get(row.get("symbol"), ""),
        "shares": shares,
        "buy_date": buy_date,
        "sell_date": sell_date,
        "side": "CLOSED",
        "kind": "CLOSED",
        "recipe": recipe,
    })
    return out


def _periods(trades):
    rows = []
    for i, tr in enumerate(trades or []):
        rows.append({
            "rank": i + 1,
            "signal_date": tr.get("signal_date"),
            "entry": tr.get("entry"),
            "exit": tr.get("exit"),
            "n_fill": tr.get("n_fill"),
            "invested": tr.get("invested"),
            "pnl": tr.get("pnl"),
            "ret": tr.get("ret"),
            "equity": tr.get("equity"),
            "kind": "PERIOD",
            "recipe": (
                "信号 %s，%s 开盘买入 %s 只，%s 开盘卖出。投入 %s，本期净利 %s。"
                % (tr.get("signal_date") or "—", tr.get("entry") or "—",
                   tr.get("n_fill") or 0, tr.get("exit") or "—",
                   _yuan(tr.get("invested")), _yuan(tr.get("pnl")))
            ),
        })
    return rows


def _today_action(window):
    """Plain-language state for the hero card. No orders; the owner acts by hand."""
    days = _trading_days()
    asof, entry, exit_d = window.get("asof_session"), window.get("entry"), window.get("exit_date")
    hold = int(window.get("hold_target") or 20)
    out = {"today_action": "UNKNOWN", "sessions_held": None, "sessions_total": hold, "sessions_left": None}
    if not (asof in days and entry in days):
        return out
    i_asof, i_entry = days.index(asof), days.index(entry)
    held = i_asof - i_entry  # sessions elapsed since the buy open; held + left == hold_target
    out["sessions_held"] = max(0, held)
    if exit_d in days:
        i_exit = days.index(exit_d)
        out["sessions_left"] = max(0, i_exit - i_asof)
        if i_asof < i_exit:
            out["today_action"] = "HOLD"
        elif i_asof == i_exit:
            out["today_action"] = "SELL"
        else:
            out["today_action"] = "BUY"
    return out


def _holdings(ledger, book_shortlist, window):
    open_p = _open_period(ledger)
    fills = ((ledger or {}).get("fills_by_period") or {}).get(open_p.get("signal_date") or "") or []
    scores = {}
    for row in (book_shortlist or {}).get("names") or []:
        scores[row.get("symbol")] = row
    meta = {"entry": window.get("entry"), "mark_date": window.get("mark_date"),
            "exit_date": window.get("exit_date")}
    rows = []
    for i, f in enumerate(fills):
        src = scores.get(f.get("symbol")) or {}
        rows.append(_ticket_open({
            "rank": src.get("rank") or i + 1,
            "symbol": f.get("symbol"),
            "buy_price": f.get("open"),
            "mark_price": f.get("mark_close"),
            "lots": f.get("lots"),
            "cost_in": f.get("cost_in"),
            "buy_fee": f.get("buy_fee"),
            "unrealized": f.get("unrealized"),
            "score": src.get("score"),
            "status": f.get("status"),
            "buy_date": window.get("entry"),
            "mark_date": f.get("mark_date") or window.get("mark_date"),
        }, meta))
    return rows


def _august_fills(raw, window):
    jul = (raw or {}).get("jul30_period") or {}
    meta = {"entry": jul.get("entry") or window.get("month_entry"), "exit": jul.get("exit")}
    rows = []
    for i, n in enumerate(jul.get("names") or []):
        rows.append(_ticket_closed({
            "rank": i + 1,
            "symbol": n.get("symbol"),
            "lots": n.get("lots"),
            "cost_in": n.get("yuan"),
            "pnl": n.get("net"),
            "status": n.get("status"),
            "buy_date": jul.get("entry"),
            "sell_date": n.get("exit") or jul.get("exit"),
        }, meta))
    return rows


def desk():
    settings = load_settings()
    status = _read(LIVE / "STATUS.json") or {}
    shortlist_path = _latest(SIGNALS, "SHORTLIST_20") or _latest(SIGNALS, "SHORTLIST_")
    # prefer dated SHORTLIST_YYYY not SHADOW
    dated = [n for n in (os.listdir(SIGNALS) if os.path.isdir(SIGNALS) else [])
             if n.startswith("SHORTLIST_20") and n.endswith(".json")]
    dated.sort()
    if dated:
        shortlist_path = str(SIGNALS / dated[-1])
    shortlist = _read(shortlist_path)
    ledger = _read(LEDGER / "LEDGER_TOP20.json")
    audit_aug = _read(LEDGER / "AUDIT_2026_08.json") or {}
    august = _august_summary(audit_aug)
    audit_open = _read(LEDGER / "AUDIT_OPEN.json") or {}
    live_open = audit_open.get("live_open") or {}
    read = _read(V26_READ) or {}
    r_tr = read.get("research_trades") or []
    v_tr = read.get("validation_trades") or []
    open_p = _open_period(ledger)
    book_path = SIGNALS / ("SHORTLIST_SHADOW_%s.json" % (open_p.get("signal_date") or ""))
    book_sl = _read(str(book_path)) if book_path.is_file() else None
    signal_path = _latest(SIGNALS, "SIGNAL_")
    pack = (status.get("live_pack") or {})
    entry = open_p.get("entry") or live_open.get("entry")
    hold_n = live_open.get("hold_target") or 20
    exit_date = _plus_sessions(entry, hold_n)
    window = {
        "asof_session": status.get("asof_session") or pack.get("asof"),
        "signal_date": open_p.get("signal_date"),
        "entry": entry,
        "mark_date": open_p.get("mark_date") or ((live_open.get("curve") or [{}])[-1] or {}).get("date"),
        "exit_expected": exit_date or open_p.get("exit_expected"),
        "exit_date": exit_date,
        "hold_target": hold_n,
        "next_signal": (status.get("signal") or {}).get("next_signal_date"),
        "research_start": (r_tr[0].get("entry") if r_tr else "2012-01-05"),
        "research_end": (r_tr[-1].get("exit") if r_tr else "2021-08-24"),
        "validation_start": (v_tr[0].get("entry") if v_tr else "2021-08-26"),
        "validation_end": (v_tr[-1].get("exit") if v_tr else "2024-01-26"),
        "denied_start": "2024-03-01",
        "denied_end": "2026-08-28",
        "denied_note": "已读过，不再用来选变体",
        "month_entry": (audit_aug.get("jul30_period") or {}).get("entry"),
        "month_exit": (audit_aug.get("jul30_period") or {}).get("exit"),
    }
    window.update(_today_action(window))
    holdings = _holdings(ledger, book_sl, window)
    august_rows = _august_fills(audit_aug, window)
    v_sum = read.get("validation") or {}
    r_sum = read.get("research") or {}
    curves = {
        "live": _curve_pack("本期影子市值", live_open.get("curve") or []),
        "august": _curve_pack("2026年8月诊断", (august or {}).get("curve") or []),
        "validation": _curve_pack("V26.8 验证期", _trade_curve(v_tr, 20000.0), {
            "equity_end": v_sum.get("equity_end"),
            "cagr": v_sum.get("cagr"),
            "periods": _periods(v_tr),
        }),
        "research": _curve_pack("V26.8 研究期", _trade_curve(r_tr, 20000.0), {
            "equity_end": r_sum.get("equity_end"),
            "cagr": r_sum.get("cagr"),
            "periods": _periods(r_tr),
        }),
    }
    official_holdings = holdings
    official_august_rows = august_rows
    preset = None
    path = _replay_cache_path(
        settings["capital"], int(settings["n_target"]), settings["monthly_contrib"],
        settings.get("boards") or "MAIN", settings["max_price"])
    cached = _read(str(path))
    live_ok = (cached or {}).get("live") or {}
    if cached and live_ok.get("preview") and "n_fill" in live_ok and not live_ok.get("error") and cached.get("ticket_v") == 2:
        preset = cached
        for key in ("live", "august", "validation", "research"):
            if preset.get(key):
                curves[key] = preset[key]
        meta_open = {"entry": window.get("entry"), "mark_date": window.get("mark_date"),
                     "exit_date": window.get("exit_date")}
        if "holdings" in preset:
            holdings = [_ticket_open(r, meta_open) for r in (preset.get("holdings") or [])]
        if preset.get("august_holdings") is not None:
            jul = audit_aug.get("jul30_period") or {}
            meta_m = {"entry": jul.get("entry"), "exit": jul.get("exit")}
            august_rows = [_ticket_closed(r, meta_m) for r in (preset.get("august_holdings") or [])]
        for key in ("validation", "research"):
            pack = curves.get(key) or {}
            if pack.get("periods"):
                pack["periods"] = _periods(pack["periods"])
    books = {
        "live": {"kind": "OPEN", "label": "本期持仓", "rows": holdings},
        "august": {"kind": "CLOSED", "label": "本月已平仓", "rows": august_rows},
        "validation": {"kind": "PERIODS", "label": "验证期每一期", "rows": (curves.get("validation") or {}).get("periods") or _periods(v_tr)},
        "research": {"kind": "PERIODS", "label": "研究期每一期", "rows": (curves.get("research") or {}).get("periods") or _periods(r_tr)},
    }
    return {
        "asof_session": status.get("asof_session") or pack.get("asof"),
        "contract": (shortlist or {}).get("contract") or (ledger or {}).get("summary", {}).get("contract"),
        "status": status,
        "settings": settings,
        "shortlist": shortlist,
        "shortlist_file": shortlist_path,
        "signal_file": signal_path,
        "holdings": holdings,
        "holdings_official": official_holdings,
        "holdings_august": august_rows,
        "holdings_august_official": official_august_rows,
        "books": books,
        "window": window,
        "curves": curves,
        "preset_replay": preset,
        "ledger": ledger,
        "august": august,
        "orders_sent": False,
    }


def preview(body):
    settings = load_settings()
    capital = float(body.get("capital") if body.get("capital") is not None else settings["capital"])
    n_target = int(body.get("n_target") if body.get("n_target") is not None else settings["n_target"])
    max_price = float(body.get("max_price") if body.get("max_price") is not None else settings["max_price"])
    boards = body.get("boards") or settings["boards"]
    if boards not in BOARD_PREFIX:
        boards = "MAIN"
    signal = _read(_latest(SIGNALS, "SIGNAL_"))
    if not signal or not signal.get("names"):
        raise FileNotFoundError("SIGNAL missing")
    out = preview_lots(signal["names"], capital, n_target, max_price, boards, settings["exposure"])
    mc = body.get("monthly_contrib")
    out["monthly_contrib"] = float(mc if mc is not None else settings["monthly_contrib"])
    out["signal_date"] = signal.get("signal_date")
    out["replay"] = _replay_books(capital, n_target, out["monthly_contrib"], boards, max_price, settings.get("exposure", 1.0))
    if out["replay"] is None:
        out["note"] = (out.get("note") or "") + " 历史曲线仍是官方 ¥20,000（这次没跑成预览回测）。"
        return out
    rp = out["replay"]
    if rp.get("error"):
        return out
    meta_o = {"entry": None, "mark_date": None, "exit_date": None}
    rp["holdings"] = [_ticket_open(r, meta_o) for r in (rp.get("holdings") or [])]
    rp["august_holdings"] = [_ticket_closed(r, {}) for r in (rp.get("august_holdings") or [])]
    for key in ("validation", "research"):
        pack = rp.get(key) or {}
        if pack.get("periods"):
            pack["periods"] = _periods(pack["periods"])
    return out


def _replay_cache_path(capital, n_target, monthly_contrib, boards, max_price):
    name = "REPLAY_c%d_n%d_m%d_%s_p%d.json" % (
        int(round(capital)), int(n_target), int(round(monthly_contrib)), boards, int(round(max_price)))
    folder = LIVE / "preview"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / name


def _replay_books(capital, n_target, monthly_contrib, boards, max_price, exposure):
    path = _replay_cache_path(capital, n_target, monthly_contrib, boards, max_price)
    cached = _read(str(path))
    live_ok = (cached or {}).get("live") or {}
    aug_ok = (cached or {}).get("august") or {}
    if cached and live_ok.get("preview") and "n_fill" in live_ok and not live_ok.get("error") and "n_fill" in aug_ok and cached.get("ticket_v") == 2:
        return cached
    import sys
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from research_engine.ml1_live.preview_replay import replay
        data = replay(capital, n_target, monthly_contrib, boards, max_price, exposure)
    except Exception as exc:
        return {"preview": True, "error": str(exc), "note": "预览回测失败，曲线仍显示官方 ¥20,000。"}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
    return data
