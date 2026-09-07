"""Informal mechanical proxy of published USIC / TraderLion playbooks.

NOT a research contract. NOT a Candidate. Does not reopen V13-V21.
Does not modify frozen hashes. Next-bar open only. No MT5. No order_send.

Locked before any result is computed:

Universe (listed before 2020, growth-ish, no earnings PIT filter):
  AAPL MSFT AMZN GOOGL META NVDA TSLA AMD NFLX AVGO CRM ADBE PYPL SHOP UBER
Benchmark: SPY
Window: 2020-01-02 through last available daily bar.

Shared execution:
  signal on close[t], fill open[t+1]
  stop: if low/high gaps through, fill at open; else fill at stop
  cost: 5bp commission + 10bp slip each side (same bp as Profit Discovery)
  long only, cash start 100000, no short
  enter only if SPY close > SPY EMA20 (their market-regime rule, mechanical)
  enter only if 63d return >= universe median (leader filter proxy)
  max 5 names
  skip entry if close > EMA10 + 2.5*ATR14 (no chase exhaustion)

PROXY_KELL_CYCLE
  EMA10 / EMA20, ATR14
  wedge_pop: prior close below both EMAs, today close above both
  crossback: EMA10>EMA20, prior 3 closes above EMA10, today low<=EMA10, close>=EMA10
  exit: close < EMA10 (wedge-drop proxy) or close < EMA20
  size: equal 1/5 of equity at entry (cash, no margin)

PROXY_LUK_PULLBACK
  rising: EMA10>EMA20 and EMA20[t] > EMA20[t-5]
  first pullback: prior 5 closes > EMA10, no EMA10-touch in prior 8 days,
                  today low<=EMA10 or low<=EMA20, close>EMA10
  stop 2.5% below entry; exit also if close < EMA20
  size: 0.5% equity risk / 2.5% stop = 20% equity per name (cash book)
  PROXY_LUK_LEV: same signals, notional cap 2.8x (championship-like heat)

Baselines:
  BH_SPY, BH_EQW monthly rebalance, EMA20_TREND (flat if SPY close<=EMA20)
"""
from __future__ import print_function

import csv
import json
import math
import os
import ssl
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "tmp", "usic_proxy_backtest")
UNIVERSE = [
    "AAPL",
    "MSFT",
    "AMZN",
    "GOOGL",
    "META",
    "NVDA",
    "TSLA",
    "AMD",
    "NFLX",
    "AVGO",
    "CRM",
    "ADBE",
    "PYPL",
    "SHOP",
    "UBER",
]
BENCH = "SPY"
START = "2020-01-02"
START_EQUITY = 100000.0
COMMISSION_BP = 5.0
SLIPPAGE_BP = 10.0
MAX_POS = 5
RS_LOOKBACK = 63
ATR_N = 14
STOP_PCT = 0.025
LUK_RISK = 0.005
KELL_WEIGHT = 1.0 / MAX_POS
LEV_CAP = 2.8
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TradeMindDiagnostic/1.0"


def _ensure_out():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return resp.read()


def fetch_yahoo(symbol):
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + symbol
        + "?interval=1d&range=10y&events=div%7Csplit"
    )
    raw = json.loads(_get(url).decode("utf-8"))
    res = raw["chart"]["result"][0]
    ts = res.get("timestamp") or []
    q = res["indicators"]["quote"][0]
    out = []
    for i, t in enumerate(ts):
        o, h, l, c, v = q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i]
        if o is None or h is None or l is None or c is None:
            continue
        if o <= 0 or h <= 0 or l <= 0 or c <= 0:
            continue
        day = datetime.fromtimestamp(int(t), tz=timezone.utc).strftime("%Y-%m-%d")
        out.append(
            {
                "date": day,
                "open": float(o),
                "high": float(h),
                "low": float(l),
                "close": float(c),
                "volume": float(v or 0),
            }
        )
    return out


def load_or_fetch(symbol):
    path = os.path.join(OUT, "bars_%s.csv" % symbol)
    if os.path.isfile(path):
        rows = []
        with open(path, "r", newline="") as f:
            for rec in csv.DictReader(f):
                rows.append(
                    {
                        "date": rec["date"],
                        "open": float(rec["open"]),
                        "high": float(rec["high"]),
                        "low": float(rec["low"]),
                        "close": float(rec["close"]),
                        "volume": float(rec["volume"]),
                    }
                )
        if rows and rows[-1]["date"] >= "2026-08-01":
            return rows
    rows = fetch_yahoo(symbol)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "open", "high", "low", "close", "volume"])
        w.writeheader()
        w.writerows(rows)
    time.sleep(0.4)
    return rows


def ema(values, n):
    if not values:
        return []
    a = 2.0 / (n + 1.0)
    out = [values[0]]
    i = 1
    while i < len(values):
        out.append(a * values[i] + (1.0 - a) * out[-1])
        i += 1
    return out


def atr(bars, n):
    out = [0.0] * len(bars)
    if len(bars) < 2:
        return out
    trs = [0.0]
    i = 1
    while i < len(bars):
        h = bars[i]["high"]
        l = bars[i]["low"]
        pc = bars[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
        i += 1
    if len(trs) <= n:
        return out
    first = sum(trs[1 : n + 1]) / float(n)
    out[n] = first
    i = n + 1
    prev = first
    while i < len(bars):
        prev = (prev * (n - 1) + trs[i]) / float(n)
        out[i] = prev
        i += 1
    return out


def align(store, start):
    dates = None
    for sym, rows in store.items():
        keep = [r["date"] for r in rows if r["date"] >= start]
        dates = set(keep) if dates is None else dates.intersection(keep)
    dates = sorted(dates)
    out = {}
    for sym, rows in store.items():
        by = {r["date"]: r for r in rows}
        out[sym] = [by[d] for d in dates if d in by]
        if len(out[sym]) != len(dates):
            raise RuntimeError("align fail %s" % sym)
    return dates, out


def add_ind(bars):
    closes = [b["close"] for b in bars]
    e10 = ema(closes, 10)
    e20 = ema(closes, 20)
    a14 = atr(bars, ATR_N)
    i = 0
    while i < len(bars):
        b = bars[i]
        b["ema10"] = e10[i]
        b["ema20"] = e20[i]
        b["atr"] = a14[i]
        if i >= RS_LOOKBACK:
            b["r63"] = closes[i] / closes[i - RS_LOOKBACK] - 1.0
        else:
            b["r63"] = None
        i += 1


def cost_px(open_px, side, is_exit):
    slip = open_px * (SLIPPAGE_BP / 10000.0)
    fee_frac = COMMISSION_BP / 10000.0
    adverse = slip
    if side > 0:
        px = open_px + adverse if not is_exit else open_px - adverse
    else:
        px = open_px - adverse if not is_exit else open_px + adverse
    return px, fee_frac


def stop_fill(bar, side, stop_px):
    if side > 0:
        if bar["low"] <= stop_px:
            return bar["open"] if bar["open"] < stop_px else stop_px
        return None
    if bar["high"] >= stop_px:
        return bar["open"] if bar["open"] > stop_px else stop_px
    return None


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return None
    if n % 2:
        return xs[n // 2]
    return 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def spy_risk_on(spy, t):
    b = spy[t]
    return b["close"] > b["ema20"]


def rs_ok(panel, t, sym):
    vals = []
    for s, bars in panel.items():
        r = bars[t]["r63"]
        if r is not None:
            vals.append((s, r))
    if len(vals) < 8:
        return False
    med = median([v[1] for v in vals])
    mine = panel[sym][t]["r63"]
    return mine is not None and mine >= med


def extended(bar):
    if bar["atr"] <= 0:
        return False
    return bar["close"] > bar["ema10"] + 2.5 * bar["atr"]


def kell_entry(bars, t):
    if t < 21:
        return False
    a, b = bars[t - 1], bars[t]
    if extended(b):
        return False
    pop = (
        a["close"] < a["ema10"]
        and a["close"] < a["ema20"]
        and b["close"] > b["ema10"]
        and b["close"] > b["ema20"]
    )
    if pop:
        return True
    if not (b["ema10"] > b["ema20"]):
        return False
    i = 1
    while i <= 3:
        if bars[t - i]["close"] <= bars[t - i]["ema10"]:
            return False
        i += 1
    return b["low"] <= b["ema10"] and b["close"] >= b["ema10"]


def kell_exit(bar):
    return bar["close"] < bar["ema10"] or bar["close"] < bar["ema20"]


def luk_entry(bars, t):
    if t < 21:
        return False
    b = bars[t]
    if not (b["ema10"] > b["ema20"] and b["ema20"] > bars[t - 5]["ema20"]):
        return False
    if extended(b):
        return False
    i = 1
    while i <= 5:
        if bars[t - i]["close"] <= bars[t - i]["ema10"]:
            return False
        i += 1
    j = 1
    while j <= 8:
        prev = bars[t - j]
        if prev["low"] <= prev["ema10"]:
            return False
        j += 1
    touched = b["low"] <= b["ema10"] or b["low"] <= b["ema20"]
    return touched and b["close"] > b["ema10"]


def luk_exit(bar):
    return bar["close"] < bar["ema20"]


def _holdings(positions, bar_by_sym, t):
    total = 0.0
    for sym, pos in positions.items():
        total += pos["qty"] * bar_by_sym[sym][t]["close"]
    return total


def _notional(positions, bar_by_sym, t):
    total = 0.0
    for sym, pos in positions.items():
        total += abs(pos["qty"] * bar_by_sym[sym][t]["close"])
    return total


def run_book(name, dates, panel, spy, entry_fn, exit_fn, sizer, lev_cap):
    cash = START_EQUITY
    positions = {}
    pending = {}
    trades = []
    curve = []
    t = 0
    n = len(dates)
    while t < n:
        for sym in list(pending.keys()):
            spec = pending[sym]
            if spec["entry_i"] != t:
                continue
            bar = panel[sym][t]
            px, fee_frac = cost_px(bar["open"], 1, False)
            eq_now = cash + _holdings(positions, panel, t)
            qty = spec["qty_fn"](eq_now, px)
            notion = qty * px
            if lev_cap <= 1.0001 and notion > cash:
                qty = math.floor((max(cash, 0.0) / px) * 1000) / 1000.0
                notion = qty * px
            used = _notional(positions, panel, t) + notion
            if qty > 0 and used <= lev_cap * max(eq_now, 1.0) + 1e-6:
                fee = notion * fee_frac
                cash -= fee + notion
                positions[sym] = {
                    "side": 1,
                    "qty": qty,
                    "entry": px,
                    "stop": px * (1.0 - STOP_PCT),
                    "entry_i": t,
                    "entry_date": dates[t],
                }
            del pending[sym]
        # stops / exits
        for sym in list(positions.keys()):
            pos = positions[sym]
            bar = panel[sym][t]
            hit = stop_fill(bar, pos["side"], pos["stop"])
            reason = None
            px = None
            if hit is not None:
                px = hit
                reason = "STOP"
            elif t != pos["entry_i"] and exit_fn(bar):
                px, _ff = cost_px(bar["open"], 1, True)
                reason = "SIGNAL"
            if px is not None:
                pnl = pos["qty"] * (px - pos["entry"])
                fee = abs(pos["qty"] * px) * (COMMISSION_BP / 10000.0)
                cash += pos["qty"] * px - fee
                trades.append(
                    {
                        "book": name,
                        "symbol": sym,
                        "entry_date": pos["entry_date"],
                        "exit_date": dates[t],
                        "entry": pos["entry"],
                        "exit": px,
                        "qty": pos["qty"],
                        "pnl": pnl - fee,
                        "reason": reason,
                    }
                )
                del positions[sym]
        # new signals
        if t + 1 < n:
            cands = []
            for sym, bars in panel.items():
                if sym in positions or sym in pending:
                    continue
                if not spy_risk_on(spy, t):
                    continue
                if not rs_ok(panel, t, sym):
                    continue
                if entry_fn(bars, t):
                    r = bars[t]["r63"]
                    cands.append((r if r is not None else -9, sym))
            cands.sort(reverse=True)
            slots = MAX_POS - len(positions) - len(pending)
            for _r, sym in cands[: max(0, slots)]:
                def _qty_fn(equity, px, _sizer=sizer):
                    return _sizer(equity, px, None)

                pending[sym] = {
                    "entry_i": t + 1,
                    "qty_fn": _qty_fn,
                }
        mtm = 0.0
        for sym, pos in positions.items():
            mtm += pos["qty"] * panel[sym][t]["close"]
        # cash already had notional removed, so equity = cash + mtm
        eq = cash + mtm
        curve.append({"date": dates[t], "equity": eq, "n_pos": len(positions), "cash": cash})
        t += 1
    # flatten last bar at close for leftover
    last = n - 1
    for sym in list(positions.keys()):
        pos = positions[sym]
        px = panel[sym][last]["close"]
        pnl = pos["qty"] * (px - pos["entry"])
        fee = abs(pos["qty"] * px) * (COMMISSION_BP / 10000.0)
        cash += pos["qty"] * px - fee
        trades.append(
            {
                "book": name,
                "symbol": sym,
                "entry_date": pos["entry_date"],
                "exit_date": dates[last],
                "entry": pos["entry"],
                "exit": px,
                "qty": pos["qty"],
                "pnl": pnl - fee,
                "reason": "EOD",
            }
        )
        del positions[sym]
    if curve:
        curve[-1]["equity"] = cash
    return curve, trades


def kell_size(cash, px, _bar):
    eq_proxy = max(cash, 1.0)
    notion = eq_proxy * KELL_WEIGHT
    qty = math.floor((notion / px) * 1000) / 1000.0
    return qty if qty * px >= 1 else 0.0


def luk_size(cash, px, _bar):
    stop_dist = px * STOP_PCT
    if stop_dist <= 0:
        return 0.0
    risk_cash = max(cash, 1.0) * LUK_RISK
    qty = math.floor((risk_cash / stop_dist) * 1000) / 1000.0
    return qty if qty * px >= 1 else 0.0


def bh_spy(dates, spy):
    curve = []
    start = None
    i = 0
    while i < len(dates):
        px = spy[i]["close"]
        if start is None:
            start = px
        curve.append({"date": dates[i], "equity": START_EQUITY * (px / start), "n_pos": 1, "cash": 0})
        i += 1
    return curve


def bh_eqw(dates, panel):
    syms = sorted(panel.keys())
    # monthly rebalance on first date of each YYYY-MM
    shares = {}
    cash = 0.0
    last_month = None
    curve = []
    i = 0
    while i < len(dates):
        month = dates[i][:7]
        prices = {s: panel[s][i]["close"] for s in syms}
        if month != last_month:
            eq = cash + sum(shares.get(s, 0.0) * prices[s] for s in syms)
            if last_month is None:
                eq = START_EQUITY
            piece = eq / float(len(syms))
            shares = {}
            for s in syms:
                shares[s] = piece / prices[s]
            cash = 0.0
            last_month = month
        eq = cash + sum(shares[s] * prices[s] for s in syms)
        curve.append({"date": dates[i], "equity": eq, "n_pos": len(syms), "cash": 0})
        i += 1
    return curve


def ema20_trend(dates, spy):
    curve = []
    cash = START_EQUITY
    shares = 0.0
    pending = None
    i = 0
    while i < len(dates):
        bar = spy[i]
        if pending is not None:
            px, fee_frac = cost_px(bar["open"], 1, pending < 0)
            if pending > 0 and shares == 0:
                fee = cash * fee_frac
                px_buy = px
                shares = (cash - fee) / px_buy
                cash = 0.0
            elif pending < 0 and shares > 0:
                cash = shares * px
                cash -= cash * fee_frac
                shares = 0.0
            pending = None
        want = 1 if spy_risk_on(spy, i) else 0
        have = 1 if shares > 0 else 0
        if want != have and i + 1 < len(dates):
            pending = 1 if want else -1
        eq = cash + shares * bar["close"]
        curve.append({"date": dates[i], "equity": eq, "n_pos": have, "cash": cash})
        i += 1
    return curve


def metrics(curve, trades, start_date, end_date):
    pts = [p for p in curve if start_date <= p["date"] <= end_date]
    if len(pts) < 2:
        return None
    s = pts[0]["equity"]
    e = pts[-1]["equity"]
    days = max(1, (datetime.strptime(pts[-1]["date"], "%Y-%m-%d") - datetime.strptime(pts[0]["date"], "%Y-%m-%d")).days)
    years = days / 365.25
    if s <= 0 or e <= 0:
        cagr = float("nan")
    else:
        cagr = (e / s) ** (1.0 / years) - 1.0
    peak = pts[0]["equity"]
    maxdd = 0.0
    for p in pts:
        if p["equity"] > peak:
            peak = p["equity"]
        if peak > 0:
            dd = p["equity"] / peak - 1.0
            if dd < maxdd:
                maxdd = dd
    tr = [x for x in trades if start_date <= x["exit_date"] <= end_date]
    wins = [x for x in tr if x["pnl"] > 0]
    losses = [x for x in tr if x["pnl"] <= 0]
    gp = sum(x["pnl"] for x in wins)
    gl = abs(sum(x["pnl"] for x in losses))
    pf = gp / gl if gl > 0 else None
    invested = 0
    for p in pts:
        if p["n_pos"] > 0:
            invested += 1
    return {
        "start": pts[0]["date"],
        "end": pts[-1]["date"],
        "start_eq": round(s, 2),
        "end_eq": round(e, 2),
        "total_return": round(e / s - 1.0, 6),
        "cagr": None if math.isnan(cagr) else round(cagr, 6),
        "maxdd": round(maxdd, 6),
        "n_trades": len(tr),
        "win_rate": round(len(wins) / float(len(tr)), 4) if tr else None,
        "profit_factor": None if pf is None else round(pf, 4),
        "time_in_mkt": round(invested / float(len(pts)), 4),
    }


def write_csv(path, rows, fields):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})


def main():
    _ensure_out()
    store = {}
    for sym in [BENCH] + UNIVERSE:
        print("fetch", sym, flush=True)
        store[sym] = load_or_fetch(sym)
        print("  ", store[sym][0]["date"], "->", store[sym][-1]["date"], "n=", len(store[sym]), flush=True)
    dates, aligned = align(store, START)
    spy = aligned[BENCH]
    panel = {s: aligned[s] for s in UNIVERSE}
    add_ind(spy)
    for s in UNIVERSE:
        add_ind(panel[s])
    last = dates[-1]
    print("aligned", dates[0], "->", last, "bars", len(dates), flush=True)

    books = {}
    books["BH_SPY"] = (bh_spy(dates, spy), [])
    books["BH_EQW"] = (bh_eqw(dates, panel), [])
    books["EMA20_TREND"] = (ema20_trend(dates, spy), [])
    books["PROXY_KELL_CYCLE"] = run_book(
        "PROXY_KELL_CYCLE", dates, panel, spy, kell_entry, kell_exit, kell_size, 1.0
    )
    books["PROXY_LUK_PULLBACK"] = run_book(
        "PROXY_LUK_PULLBACK", dates, panel, spy, luk_entry, luk_exit, luk_size, 1.0
    )
    books["PROXY_LUK_LEV"] = run_book(
        "PROXY_LUK_LEV", dates, panel, spy, luk_entry, luk_exit, luk_size, LEV_CAP
    )

    windows = [
        ("FULL", dates[0], last),
        ("Y2020", "2020-01-02", "2020-12-31"),
        ("Y2021", "2021-01-01", "2021-12-31"),
        ("Y2022", "2022-01-01", "2022-12-31"),
        ("Y2023", "2023-01-01", "2023-12-31"),
        ("Y2024", "2024-01-01", "2024-12-31"),
        ("Y2025", "2025-01-01", "2025-12-31"),
        ("Y2026", "2026-01-01", last),
    ]
    summary = []
    for book, (curve, trades) in books.items():
        write_csv(
            os.path.join(OUT, "equity_%s.csv" % book),
            curve,
            ["date", "equity", "n_pos", "cash"],
        )
        if trades:
            write_csv(
                os.path.join(OUT, "trades_%s.csv" % book),
                trades,
                ["book", "symbol", "entry_date", "exit_date", "entry", "exit", "qty", "pnl", "reason"],
            )
        for wname, a, b in windows:
            m = metrics(curve, trades, a, b)
            if m is None:
                continue
            row = {"book": book, "window": wname}
            row.update(m)
            summary.append(row)
    write_csv(
        os.path.join(OUT, "SUMMARY.csv"),
        summary,
        [
            "book",
            "window",
            "start",
            "end",
            "start_eq",
            "end_eq",
            "total_return",
            "cagr",
            "maxdd",
            "n_trades",
            "win_rate",
            "profit_factor",
            "time_in_mkt",
        ],
    )
    meta = {
        "label": "INFORMAL_USIC_PROXY_DIAGNOSTIC",
        "not_a_candidate": True,
        "not_research_contract": True,
        "universe": UNIVERSE,
        "benchmark": BENCH,
        "start": dates[0],
        "end": last,
        "n_bars": len(dates),
        "cost_bp_each_side": {"commission": COMMISSION_BP, "slippage": SLIPPAGE_BP},
        "source": "Yahoo Finance v8 chart, split-adjusted OHLC",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(os.path.join(OUT, "META.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))
    print("SUMMARY rows", len(summary))
    for row in summary:
        if row["window"] == "FULL":
            print(
                row["book"],
                "ret",
                row["total_return"],
                "cagr",
                row["cagr"],
                "maxdd",
                row["maxdd"],
                "trades",
                row["n_trades"],
            )


if __name__ == "__main__":
    main()
