"""Book 2: V26.8 names filtered by Grok on anonymous prices only."""
from __future__ import annotations

import os
from typing import Any, Callable, Dict, List, Optional

from research_engine.cn_a_share_alpha.cost import SLIPPAGE, stamp_duty_sell
from research_engine.cn_a_share_ml_v25 import VALIDATION
from research_engine.cn_a_share_ml_v25.scale_book import daily_curve
from research_engine.cn_a_share_ml_v25.top_n_book import (
    FEE_RESERVE_FULL,
    HOLD,
    LOT,
    UNIT_YUAN,
    _exit_fill,
    _fee,
    eq_money_period,
    eq_money_select,
)
from research_engine.cn_a_share_strategy_v14_1.capital_ref import exec_reason
from research_engine.hot_three_books import anon
from research_engine.hot_three_books.assets import SHELL, load_assets
from research_engine.hot_three_books.paths import B2_LOG, B2_PATH, B2_RUN, dump, load

KeepFn = Callable[[Dict[str, Any], List[str]], List[str]]


def period_from_picks(pack, xok, t, equity, picks, hold=HOLD):
    dates = pack["dates"]
    t0, t1 = t + 1, t + 1 + hold
    if t1 >= len(dates) or not picks:
        return {
            "signal_date": dates[t], "entry": dates[t0] if t0 < len(dates) else dates[t],
            "exit": dates[t1] if t1 < len(dates) else None, "n_sel": 0, "n_fill": 0,
            "invested": 0.0, "pnl": 0.0, "ret": 0.0, "names": [],
            "cash_idle_frac": 1.0,
        }
    pnl, invested, n_fill, names = 0.0, 0.0, 0, []
    for j, lots in picks:
        r0 = "FILL" if bool(xok[t0, j]) else exec_reason(pack, t0, j)
        if r0 != "FILL":
            names.append({"symbol": pack["symbols"][j], "lots": lots, "status": r0, "net": 0.0})
            continue
        o0 = float(pack["open"][t0, j])
        shares = lots * LOT
        cost_in = shares * o0 * (1.0 + SLIPPAGE)
        px1, exit_day, r1 = _exit_fill(pack, xok, t1, j)
        if px1 is None:
            names.append({"symbol": pack["symbols"][j], "lots": lots, "status": r1, "net": 0.0})
            continue
        proceeds = shares * px1 * (1.0 - SLIPPAGE)
        fees = _fee(cost_in) + _fee(proceeds) + proceeds * stamp_duty_sell(exit_day)
        net = proceeds - cost_in - fees
        pnl += net
        invested += cost_in
        n_fill += 1
        names.append({"symbol": pack["symbols"][j], "lots": lots, "status": r1, "exit": exit_day,
                      "net": round(net, 2), "yuan": round(cost_in, 2)})
    return {
        "signal_date": dates[t], "entry": dates[t0], "exit": dates[t1],
        "n_sel": len(picks), "n_fill": n_fill, "invested": round(invested, 2),
        "cash_idle_frac": round(1.0 - invested / equity, 4) if equity else 1.0,
        "pnl": round(pnl, 2), "ret": (pnl / equity) if equity else 0.0, "names": names,
    }


def list_validation_signals(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Candidate names/lots follow the book-1 V26.8 equity path (not book-2's filtered equity)."""
    pack, scores, elig, xok = load_assets()
    dates = pack["dates"]
    a, b = VALIDATION
    i0, i1 = dates.index(a), dates.index(b)
    equity, t, last_month = float(SHELL["capital"]), i0, None
    fee_reserve = FEE_RESERVE_FULL
    rows = []
    while t <= i1:
        if SHELL["monthly_contrib"] > 0 and dates[t][:7] != last_month and last_month is not None:
            equity += SHELL["monthly_contrib"]
        unit = max(UNIT_YUAN, equity / SHELL["n_target"])
        sel = eq_money_select(
            pack, scores[t], elig[t], t, equity, SHELL["exposure"], unit,
            SHELL["boards"], SHELL["max_price"], SHELL["topup"], fee_reserve,
        )
        per = None
        if sel is not None:
            per = eq_money_period(
                pack, scores[t], elig[t], xok, t, equity, SHELL["exposure"], unit,
                SHELL["boards"], SHELL["max_price"], HOLD, SHELL["topup"], fee_reserve,
            )
        if sel is None or per is None:
            if t + 1 + HOLD >= len(dates):
                break
            t += 1
            continue
        last_month = dates[t][:7]
        equity += per["pnl"]
        rows.append({
            "t": t, "signal_date": dates[t],
            "picks": [(int(j), int(lots)) for j, lots in sel["picks"]],
        })
        if limit and len(rows) >= limit:
            break
        t = t + 1 + HOLD
    return rows


def _keep_picks(picks, keep_ids):
    wanted = set(keep_ids)
    out = []
    for i, (j, lots) in enumerate(picks):
        if ("U%02d" % (i + 1)) in wanted:
            out.append((j, lots))
    return out


def default_keep_fn(payload: Dict[str, Any], valid_ids: List[str]) -> List[str]:
    if os.environ.get("TRADEMIND_HOT_SMOKE") or os.environ.get("TRADEMIND_BOOK2_KEEP_ALL"):
        return list(valid_ids)
    from research_engine.hot_three_books.grok_keep import ask_keep
    return ask_keep(payload, valid_ids)


def run_window(limit: Optional[int] = None, keep_fn: Optional[KeepFn] = None, resume: bool = True,
               tail: Optional[int] = None) -> Dict[str, Any]:
    keep_fn = keep_fn or default_keep_fn
    pack, _scores, _elig, xok = load_assets()
    if tail:
        signals = list_validation_signals(limit=None)[-int(tail):]
    elif limit:
        signals = list_validation_signals(limit=int(limit))
    else:
        signals = list_validation_signals(limit=None)
    log = load(B2_LOG, None) or {"items": []}
    done_dates = set()
    trades = []
    if resume:
        prev = load(B2_PATH, None) or {}
        for tr in prev.get("periods") or []:
            if tr.get("signal_date"):
                done_dates.add(tr["signal_date"])
                trades.append(tr)
    if not resume:
        trades, done_dates, log = [], set(), {"items": []}
    else:
        # a trailing GROK_TIMEOUT period is never "done": pop it and retry (it carried no pnl/contrib)
        while trades and trades[-1].get("status") == "GROK_TIMEOUT":
            done_dates.discard(trades[-1].get("signal_date"))
            trades.pop()
        expected = [s["signal_date"] for s in signals]
        have = [tr.get("signal_date") for tr in trades]
        if have != expected[: len(have)]:
            trades, done_dates, log = [], set(), {"items": []}

    equity = float(SHELL["capital"])
    deposits, last_month, twr = 0.0, None, 1.0
    # replay equity up to first unfinished signal (timeout periods carry ret=0 and are excluded)
    for tr in trades:
        equity = float(tr.get("equity") or equity)
        deposits = float(tr.get("deposits_to_date") or deposits)
        last_month = (tr.get("signal_date") or "")[:7] or last_month
        if tr.get("status") != "GROK_TIMEOUT":
            twr *= 1.0 + float(tr.get("ret") or 0.0)

    dump(B2_RUN, {"running": True, "stage": "账本2 进行中", "done": len(trades), "total": len(signals)})
    stopped_reason = None
    for row in signals:
        if load(B2_RUN, {}).get("stop"):
            stopped_reason = "STOP_REQUESTED"
            break
        sd = row["signal_date"]
        if sd in done_dates:
            continue
        t, picks = row["t"], row["picks"]
        contrib = 0.0
        if SHELL["monthly_contrib"] > 0 and sd[:7] != last_month and last_month is not None:
            contrib = float(SHELL["monthly_contrib"])
        js = [j for j, _ in picks]
        payload, mapping = anon.pack_window(pack, t, js)
        valid = [s["id"] for s in payload["series"]]
        try:
            keep_ids = keep_fn(payload, valid)
        except Exception as exc:  # GrokTimeout or transport failure: record, stop, resume later
            err = str(exc)[:300]
            per = {
                "signal_date": sd, "entry": None, "exit": None, "n_sel": 0, "n_fill": 0,
                "invested": 0.0, "pnl": 0.0, "ret": 0.0, "names": [], "cash_idle_frac": 1.0,
                "status": "GROK_TIMEOUT", "error": err,
                "equity": round(equity, 2), "deposits_to_date": round(deposits, 2),
                "keep": None, "n_ml1": len(picks),
            }
            trades.append(per)
            log.setdefault("items", []).append({"signal_date": sd, "sent": payload, "keep": None,
                                                "map": mapping, "status": "GROK_TIMEOUT", "error": err})
            dump(B2_LOG, log)
            stopped_reason = "GROK_TIMEOUT"
            break
        equity += contrib
        deposits += contrib
        filtered = _keep_picks(picks, keep_ids)
        per = period_from_picks(pack, xok, t, equity, filtered)
        twr *= 1.0 + per["ret"]
        equity += per["pnl"]
        per["equity"] = round(equity, 2)
        per["deposits_to_date"] = round(deposits, 2)
        per["keep"] = keep_ids
        per["n_ml1"] = len(picks)
        per["status"] = "OK"
        last_month = sd[:7]
        trades.append(per)
        per["anon_protocol"] = anon.PROTOCOL
        log.setdefault("items", []).append({
            "signal_date": sd,
            "protocol": anon.PROTOCOL,
            "sent": payload,
            "keep": keep_ids,
            "map": mapping,
        })
        dump(B2_LOG, log)
        _write_ledger(pack, trades, twr, equity, running=True, total_n=len(signals), last_keep=keep_ids, sd=sd)

    out = _write_ledger(pack, trades, twr, equity, running=False, total_n=len(signals), stopped_reason=stopped_reason)
    return out


def _write_ledger(pack, trades, twr, equity, running, total_n, last_keep=None, sd=None, stopped_reason=None):
    scored = [tr for tr in trades if tr.get("status") != "GROK_TIMEOUT"]
    n_timeout = len(trades) - len(scored)
    yrs = max(len(scored) * (HOLD + 1) / 242.0, 1e-9)
    total = twr - 1.0
    try:
        cd, idx, _ = daily_curve(pack, scored, SHELL["capital"])
        daily = [{"date": d, "equity": round(float(v), 2)} for d, v in zip(cd, idx)]
    except Exception:
        daily = [{"date": tr.get("exit") or tr.get("entry"), "equity": tr.get("equity")} for tr in scored]
    complete = len(scored) >= total_n and n_timeout == 0
    out = {
        "profile": "HOT_B2_ANON_GROK",
        "candidate": False,
        "window": "validation",
        "start": VALIDATION[0],
        "end": VALIDATION[1],
        "twr": total,
        "cagr": float((1.0 + total) ** (1.0 / yrs) - 1.0) if scored else None,
        "equity_end": equity,
        "n_periods": len(scored),
        "n_timeout": n_timeout,
        "total_expected": total_n,
        "complete": complete,
        "anon_protocol": anon.PROTOCOL,
        "anon_protocol_note": "v1.1（2026-09-11）：bars=[o,h,l,c] 数组、2 位小数、索引隐含；信息同 v1.0，体积约一半。2026-09-10 的单期一枪用的是 v1.0。",
        "denied_window_read": False,
        "note": "匿名价格过滤。不是 Candidate。出名走势仍可能被认出来。GROK_TIMEOUT 期不计入 TWR，单独计数。",
        "daily": daily,
        "periods": [{
            "signal_date": tr.get("signal_date"), "entry": tr.get("entry"), "exit": tr.get("exit"),
            "status": tr.get("status") or "OK", "error": tr.get("error"),
            "n_fill": tr.get("n_fill"), "n_ml1": tr.get("n_ml1"), "keep": tr.get("keep"),
            "invested": tr.get("invested"), "pnl": tr.get("pnl"), "ret": tr.get("ret"),
            "equity": tr.get("equity"), "deposits_to_date": tr.get("deposits_to_date"),
            "names": tr.get("names") or [],
        } for tr in trades],
    }
    dump(B2_PATH, out)
    if running and sd:
        stage = "账本2 %s" % sd
    elif complete:
        stage = "完成"
    elif stopped_reason == "GROK_TIMEOUT":
        stage = "已停止：Grok 超时（再点「跑验证窗」会从该期续跑）"
    else:
        stage = "已停止"
    run = {"running": running, "done": len(scored), "total": total_n, "n_timeout": n_timeout, "stage": stage}
    if stopped_reason:
        run["stopped_reason"] = stopped_reason
        if stopped_reason == "GROK_TIMEOUT":
            run["error"] = "GROK_TIMEOUT：该期未记分，账本未混入 keep-all/keep-none。"
    if last_keep is not None:
        run["last_keep"] = last_keep
    dump(B2_RUN, run)
    return out
