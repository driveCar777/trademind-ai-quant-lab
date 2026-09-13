"""GOLD H1 V2: same-day London ORB + Donchian24. No overnight. No tree."""
from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from research_engine.hot_mt5_gold_h1.data import load_h1
from research_engine.hot_mt5_gold_h1_v2.paths import HIST, RES
from research_engine.hot_mt5_products.products import SLIP, VAL_FRAC

RANGE_HOUR = 7
EXIT_HOUR = 20
LAST_SIGNAL_HOUR = 19
DONCHIAN = 24
MIN_COVERAGE = 0.15
MIN_VAL_TRADES = 8
PROFILE = "HOT_MT5_GOLD_H1_V2_SESSION"


def ensure():
    RES.mkdir(parents=True, exist_ok=True)
    return RES


def _meta() -> Dict[str, Any]:
    p = HIST / "GOLD_META.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"point": 0.01, "spread_points_now": 34, "bid": 4300.0}


def _hour(ts: str) -> int:
    return int(ts[11:13])


def _days(ts: List[str]) -> List[Tuple[str, List[int]]]:
    groups: List[Tuple[str, List[int]]] = []
    cur_d, cur = None, []
    for i, t in enumerate(ts):
        d = t[:10]
        if d != cur_d:
            if cur:
                groups.append((cur_d, cur))
            cur_d, cur = d, [i]
        else:
            cur.append(i)
    if cur:
        groups.append((cur_d, cur))
    return groups


def _fill_cost(bar, meta, t_in: int) -> float:
    px = float(bar["open"][t_in])
    pt = float(meta.get("point") or 0.01)
    raw = float(bar["spread"][t_in]) * pt / max(1e-12, float(bar["close"][t_in]))
    now = float(meta.get("spread_points_now") or 0) * pt / max(1e-12, float(meta.get("bid") or px))
    spread = max(0.0, now) if (not np.isfinite(raw) or raw <= 0) else max(raw, now * 0.25)
    return spread + 2 * SLIP


def _summ(rets: List[float], cal_yrs: Optional[float] = None) -> Dict[str, Any]:
    x = np.array(rets, dtype=np.float64)
    empty = {"n_periods": 0, "twr": None, "cagr": None, "mean": None, "t": None,
             "hit": None, "maxdd": None, "payoff": None}
    if len(x) == 0:
        return empty
    eq = np.cumprod(1.0 + x)
    yrs = cal_yrs if cal_yrs and cal_yrs > 0 else max(1e-9, len(x) / 252.0)
    peak = np.maximum.accumulate(eq)
    dd = float(np.min(eq / peak - 1.0))
    t = float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else None
    wins, loss = x[x > 0], x[x <= 0]
    payoff = float(wins.mean() / (-loss.mean())) if len(wins) and len(loss) and loss.mean() < 0 else None
    return {
        "n_periods": int(len(x)), "twr": float(eq[-1] - 1.0),
        "cagr": float(eq[-1] ** (1.0 / max(1e-9, yrs)) - 1.0),
        "mean": float(x.mean()), "t": t, "hit": float((x > 0).mean()),
        "maxdd": dd, "payoff": payoff,
    }


def _eligible_days(groups: List[Tuple[str, List[int]]], ts: List[str]) -> List[str]:
    out = []
    for d, idxs in groups:
        hours = [_hour(ts[i]) for i in idxs]
        if RANGE_HOUR in hours and any(h >= EXIT_HOUR for h in hours):
            out.append(d)
    return out


def _exit_i(idxs: List[int], ts: List[str], after: int) -> Optional[int]:
    for i in idxs:
        if i > after and _hour(ts[i]) >= EXIT_HOUR:
            return i
    return None


def _range_i(idxs: List[int], ts: List[str]) -> Optional[int]:
    hit = [i for i in idxs if _hour(ts[i]) == RANGE_HOUR]
    return hit[0] if len(hit) == 1 else None


def signals_orb(bar) -> List[Tuple[int, int, int, str]]:
    ts, h, l, c = bar["ts"], bar["high"], bar["low"], bar["close"]
    out = []
    for d, idxs in _days(ts):
        r = _range_i(idxs, ts)
        if r is None:
            continue
        rh, rl = float(h[r]), float(l[r])
        side, sig = 0, None
        for i in idxs:
            if i <= r or _hour(ts[i]) > LAST_SIGNAL_HOUR:
                continue
            px = float(c[i])
            if not np.isfinite(px):
                continue
            if px > rh:
                side, sig = 1, i
                break
            if px < rl:
                side, sig = -1, i
                break
        if sig is None:
            continue
        t_in = sig + 1
        if t_in >= len(ts) or ts[t_in][:10] != d:
            continue
        t_out = _exit_i(idxs, ts, t_in)
        if t_out is None:
            continue
        out.append((sig, t_in, t_out, side))
    return out


def signals_donchian(bar) -> List[Tuple[int, int, int, int]]:
    ts, h, l, c = bar["ts"], bar["high"], bar["low"], bar["close"]
    n = len(ts)
    out = []
    for d, idxs in _days(ts):
        r = _range_i(idxs, ts)
        if r is None or r < DONCHIAN:
            continue
        side, sig = 0, None
        for i in idxs:
            if i < r or _hour(ts[i]) > LAST_SIGNAL_HOUR:
                continue
            if i < DONCHIAN:
                continue
            px = float(c[i])
            if not np.isfinite(px):
                continue
            prior_h = float(np.max(h[i - DONCHIAN:i]))
            prior_l = float(np.min(l[i - DONCHIAN:i]))
            if px > prior_h:
                side, sig = 1, i
                break
            if px < prior_l:
                side, sig = -1, i
                break
        if sig is None:
            continue
        t_in = sig + 1
        if t_in >= n or ts[t_in][:10] != d:
            continue
        t_out = _exit_i(idxs, ts, t_in)
        if t_out is None:
            continue
        out.append((sig, t_in, t_out, side))
    return out


def _fills(bar, meta, raw_sig: List[Tuple[int, int, int, int]]) -> List[Dict[str, Any]]:
    ts, o = bar["ts"], bar["open"]
    trades = []
    for sig, t_in, t_out, side in raw_sig:
        if o[t_in] <= 0 or not np.isfinite(o[t_in]) or not np.isfinite(o[t_out]):
            continue
        raw = (float(o[t_out]) / float(o[t_in]) - 1.0) * side
        cost = _fill_cost(bar, meta, t_in)
        trades.append({
            "signal": ts[sig], "entry": ts[t_in], "exit": ts[t_out],
            "side": "LONG" if side > 0 else "SHORT",
            "hours": int(t_out - t_in),
            "raw": float(raw), "cost": float(cost), "net": float(raw - cost),
        })
    return trades


def _cal_yrs(trades: List[Dict[str, Any]]) -> Optional[float]:
    if not trades:
        return None
    try:
        d0 = dt.date.fromisoformat(trades[0]["signal"][:10])
        d1 = dt.date.fromisoformat(trades[-1]["exit"][:10])
        return max(1e-9, (d1 - d0).days / 365.25)
    except Exception:
        return None


def _slice(trades, start_d: Optional[str], end_d: Optional[str]) -> List[Dict[str, Any]]:
    out = []
    for t in trades:
        d = t["signal"][:10]
        if start_d and d < start_d:
            continue
        if end_d and d > end_d:
            continue
        out.append(t)
    return out


def _gate(val_s: Dict[str, Any]) -> Tuple[str, Optional[str], bool]:
    cover_fail = bool((val_s.get("n_periods") or 0) < MIN_VAL_TRADES or (val_s.get("coverage") or 0) < MIN_COVERAGE)
    viable = bool(not cover_fail and (val_s.get("twr") or 0) > 0 and (val_s.get("t") or 0) > 1.0)
    if cover_fail:
        return "NO_CANDIDATE", "VALIDATION_COVERAGE", False
    if viable:
        return "VIABLE_HISTORICAL", None, True
    return "NO_CANDIDATE", "VALIDATION_GATE", False


def _report(trades, elig: List[str], start_d: str, end_d: Optional[str]) -> Dict[str, Any]:
    days = [d for d in elig if d >= start_d and (end_d is None or d <= end_d)]
    sub = _slice(trades, start_d, end_d)
    stats = _summ([t["net"] for t in sub], _cal_yrs(sub))
    stats["coverage"] = (len(sub) / float(len(days))) if days else 0.0
    stats["n_eligible_days"] = len(days)
    stats["n_cash_days"] = max(0, len(days) - len(sub))
    return stats


def _book(trades, elig: List[str]) -> Dict[str, Any]:
    if not elig:
        empty = _summ([])
        empty.update({"coverage": 0.0, "n_eligible_days": 0, "n_cash_days": 0})
        return {
            "long_sample": empty, "research_70": empty, "validation_30": empty,
            "last_month_diagnostic": _summ([]),
            "verdict": "NO_CANDIDATE", "deny": "VALIDATION_COVERAGE",
            "viable_historical": False, "n_trades_long": 0,
        }
    cut = int((1.0 - VAL_FRAC) * len(elig))
    if cut < 1:
        cut = 1
    if cut >= len(elig):
        cut = len(elig) - 1
    res_end = elig[cut - 1]
    val_start = elig[cut]
    long_s = _report(trades, elig, elig[0], None)
    res_s = _report(trades, elig, elig[0], res_end)
    val_s = _report(trades, elig, val_start, None)
    verdict, deny, viable = _gate(val_s)
    month = [t for t in trades if t["signal"][:10] >= "2026-08-11"]
    return {
        "long_sample": long_s, "research_70": res_s, "validation_30": val_s,
        "last_month_diagnostic": _summ([t["net"] for t in month]),
        "verdict": verdict, "deny": deny, "viable_historical": viable,
        "n_trades_long": len(trades),
        "val_start": val_start,
    }


def run() -> Dict[str, Any]:
    print("GOLD H1 V2 session", flush=True)
    ensure()
    path = HIST / "GOLD_H1.csv"
    if not path.is_file():
        return {"ok": False, "error": "NO_H1"}
    bar = load_h1(path)
    meta = _meta()
    groups = _days(bar["ts"])
    elig = _eligible_days(groups, bar["ts"])
    orb_tr = _fills(bar, meta, signals_orb(bar))
    don_tr = _fills(bar, meta, signals_donchian(bar))
    orb = _book(orb_tr, elig)
    don = _book(don_tr, elig)
    summary = {
        "profile": PROFILE, "ok": True, "candidate": False, "level1": False, "promise": False,
        "writes_9000": False, "us_shares": False, "timeframe": "H1",
        "overnight": False, "range_hour_utc": RANGE_HOUR, "exit_hour_utc": EXIT_HOUR,
        "n_bars": len(bar["ts"]), "first": bar["ts"][0], "last": bar["ts"][-1],
        "n_eligible_days": len(elig),
        "books": {
            "LONDON_ORB": {**orb, "rule": "07:00 UTC 高低突破，当日 ≥20:00 开盘出"},
            "DONCHIAN24_SESSION": {**don, "rule": "07–19 时第一次收盘破前 24 根高低，当日 ≥20:00 开盘出"},
        },
        "n_viable": int(orb["viable_historical"]) + int(don["viable_historical"]),
        "note": "V2 当日场次。不是 V1 补丁。不是 Candidate。15/30 另开。",
    }
    (RES / "READ.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (RES / "ORB_trades.json").write_text(json.dumps(orb_tr, ensure_ascii=False), encoding="utf-8")
    (RES / "DONCHIAN_trades.json").write_text(json.dumps(don_tr, ensure_ascii=False), encoding="utf-8")
    return summary
