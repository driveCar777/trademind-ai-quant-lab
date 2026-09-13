"""Read frozen V4/V5 GOLD books + latest D1. Write follow STATUS. No train. No Grok."""
from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict, List, Optional

import numpy as np

from research_engine.hot_mt5_cost_aware.engine import CASH, LONG
from research_engine.hot_mt5_gold_follow import paths
from research_engine.hot_mt5_products.features import load_d1
from research_engine.hot_mt5_tsmom.engine import HOLD, LOOKBACK, mom_pred
from research_engine.hot_mt5_voltarget.engine import TARGET_ANN, vol_weights

PROFILE = "HOT_MT5_GOLD_FOLLOW_V4"
DISCLAIMER = (
    "不是 Candidate，不是承诺，不发单。历史过门只在 2018 起样本的 2024–26 金牛验证窗："
    "V4 验证 +84% t 2.18、全样本 MaxDD −47%；V5 验证 +73% t 2.83、MaxDD −40%。"
    "研究窗为负。空头历史每笔约 −1.4%。10%/月不是闸门。不要用 9 月小时砸盘改 252/20/10%。"
)


def _load_json(path, default=None):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _sign_name(pred: float) -> str:
    if (not np.isfinite(pred)) or int(pred) == CASH:
        return "CASH"
    return "LONG" if int(pred) == LONG else "SHORT"


def _add_weekdays(iso: str, n: int) -> str:
    d = dt.date.fromisoformat(iso)
    step = 1 if n >= 0 else -1
    left = abs(int(n))
    while left > 0:
        d = d + dt.timedelta(days=step)
        if d.weekday() < 5:
            left -= 1
    return d.isoformat()


def _replay_open(bar: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    pred = mom_pred(bar["close"])
    dates, o, c = bar["dates"], bar["open"], bar["close"]
    n = len(dates)
    t = LOOKBACK
    last = None
    while t + 1 < n:
        s = pred[t]
        if (not np.isfinite(s)) or int(s) == CASH:
            t += 1
            continue
        t_in = t + 1
        t_out = t + 1 + HOLD
        side = _sign_name(s)
        open_leg = t_out >= n
        mark_i = n - 1 if open_leg else t_out
        last = {
            "signal": dates[t],
            "entry": dates[t_in],
            "exit": None if open_leg else dates[t_out],
            "side": side,
            "open_leg": open_leg,
            "signal_i": t,
            "entry_i": t_in,
            "exit_i": None if open_leg else t_out,
            "mom_252": float(c[t] / c[t - LOOKBACK] - 1.0),
            "entry_open": float(o[t_in]),
            "mark_open": float(o[mark_i]),
            "mark_close": float(c[mark_i]),
            "mark_date": dates[mark_i],
        }
        if open_leg:
            break
        t = t_out
    return last


def _h1_dump() -> Optional[Dict[str, Any]]:
    raw = _load_json(paths.H1_DIAG)
    if not isinstance(raw, dict):
        return None
    overlay = raw.get("overlay") or []
    open_row = None
    for row in overlay:
        leg = (row or {}).get("leg") or {}
        if leg.get("open_leg"):
            open_row = row
            break
    if open_row is None and overlay:
        open_row = overlay[-1]
    path = (open_row or {}).get("v4_h1") or {}
    worst = path.get("worst_hour") or {}
    win = raw.get("window") or {}
    return {
        "window": "%s→%s" % (win.get("from") or "", win.get("to") or ""),
        "mtm": path.get("mtm"),
        "maxdd": path.get("maxdd"),
        "worst_ts": worst.get("ts"),
        "worst_px": worst.get("px"),
        "source": "GOLD_LAST_MONTH.json",
    }


def _book_snip(rep: Optional[Dict[str, Any]], trades: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    if not isinstance(rep, dict):
        return {}
    longs = shorts = 0
    if isinstance(trades, list):
        for tr in trades:
            if tr.get("side") == "LONG":
                longs += 1
            elif tr.get("side") == "SHORT":
                shorts += 1
    val = rep.get("validation_30") or {}
    res = rep.get("research_70") or {}
    lng = rep.get("long_sample") or {}
    return {
        "verdict": rep.get("verdict"),
        "val_twr": val.get("twr"),
        "val_t": val.get("t"),
        "maxdd": lng.get("maxdd"),
        "research_twr": res.get("twr"),
        "n_long": longs,
        "n_short": shorts,
        "n_trades": rep.get("n_trades_long"),
        "last": rep.get("last"),
    }


def build_status() -> Dict[str, Any]:
    if not paths.D1.is_file():
        return {
            "profile": PROFILE, "ok": False, "error": "NO_D1",
            "candidate": False, "deploy": False, "writes_9000": False,
            "feeds_grok": False, "order_send": False, "disclaimer": DISCLAIMER,
        }
    bar = load_d1(paths.D1)
    dates, c = bar["dates"], bar["close"]
    n = len(dates)
    pred = mom_pred(c)
    weights = vol_weights(c)
    last_i = n - 1
    last_bar_sign = _sign_name(pred[last_i]) if last_i >= LOOKBACK else "CASH"
    mom_last = None
    close_252 = None
    if last_i >= LOOKBACK and c[last_i - LOOKBACK] > 0:
        close_252 = float(c[last_i - LOOKBACK])
        mom_last = float(c[last_i] / c[last_i - LOOKBACK] - 1.0)
    w_last = float(weights[last_i]) if last_i < len(weights) else None
    leg = _replay_open(bar)
    if leg is None:
        stance, since_signal, since_entry, open_leg = last_bar_sign, None, None, False
        v5_w = w_last
        mtm_o = mtm_c = None
        entry_open = None
        bars_held = bars_left = None
        planned = None
        signal_mom = None
    else:
        stance = str(leg["side"])
        since_signal = leg["signal"]
        since_entry = leg["entry"]
        open_leg = bool(leg["open_leg"])
        v5_w = float(weights[leg["signal_i"]])
        entry_open = float(leg["entry_open"])
        sign = 1.0 if stance == "LONG" else -1.0
        mtm_o = sign * (leg["mark_open"] / entry_open - 1.0) if entry_open > 0 else None
        mtm_c = sign * (leg["mark_close"] / entry_open - 1.0) if entry_open > 0 else None
        bars_held = int(last_i - leg["entry_i"])
        bars_left = int(HOLD - bars_held) if open_leg else 0
        planned = None if not open_leg else _add_weekdays(dates[last_i], max(0, bars_left))
        signal_mom = float(leg["mom_252"])
    meta = _load_json(paths.META, {}) or {}
    v4 = _load_json(paths.V4_GOLD, {})
    v5 = _load_json(paths.V5_GOLD, {})
    v4t = _load_json(paths.V4_TRADES, [])
    v5t = _load_json(paths.V5_TRADES, [])
    return {
        "profile": PROFILE,
        "ok": True,
        "candidate": False,
        "deploy": False,
        "level1": False,
        "promise": False,
        "writes_9000": False,
        "feeds_grok": False,
        "order_send": False,
        "no_ml": True,
        "broker_symbol": meta.get("broker") or "GOLD",
        "logical": "XAUUSD",
        "not_xauusd_if_broker_lists_GOLD": True,
        "stance": stance,
        "last_bar_sign": last_bar_sign,
        "since_signal": since_signal,
        "since_entry": since_entry,
        "open_leg": open_leg,
        "last_bar": dates[last_i],
        "last_close": float(c[last_i]),
        "close_252": close_252,
        "mom_252": mom_last,
        "signal_mom_252": signal_mom,
        "entry_open": entry_open,
        "mtm_to_last_open": mtm_o,
        "mtm_to_last_close": mtm_c,
        "v5_weight": v5_w,
        "v5_weight_last": w_last,
        "v5_target_ann": TARGET_ANN,
        "lookback": LOOKBACK,
        "hold": HOLD,
        "bars_held": bars_held,
        "bars_left": bars_left,
        "planned_exit_est": planned,
        "h1_dump": _h1_dump(),
        "book_v4": _book_snip(v4, v4t),
        "book_v5": _book_snip(v5, v5t),
        "disclaimer": DISCLAIMER,
        "asof_written": dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "note": "Frozen V4 sign + optional V5 size cap. Human follow only.",
    }


def write_status(out_path=None) -> Dict[str, Any]:
    paths.ensure()
    status = build_status()
    dest = out_path or paths.STATUS
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return status


def read_status() -> Optional[Dict[str, Any]]:
    raw = _load_json(paths.STATUS)
    return raw if isinstance(raw, dict) else None
