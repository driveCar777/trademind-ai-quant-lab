#!/usr/bin/env python3
"""TradeMind Backtest Worker v2.1 - Enhanced strategy backtesting server.

Pure Python stdlib. No pip, no Docker, no third-party packages.
Designed for AGX Xavier bare-metal deployment (Python 3.6.9).

Port: 8002
Endpoints:
  GET  /health
  POST /backtest
  GET  /strategies
  GET  /version
"""

import hashlib
import json
import math
import sys
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

import os
PORT = int(os.environ.get("TRADEMIND_BACKTEST_PORT", "8002"))
SERVICE_NAME = "backtest-worker"
VERSION = "2.1.4"
WORKER_ID = os.environ.get("TRADEMIND_WORKER_ID", "xavier-worker-03")
_start_time = datetime.utcnow()

def _seed(s):
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))

def _generate_synthetic_ohlcv(symbol, start_date, days=365):
    base_price = {
        "XAUUSD": 2000.0, "EURUSD": 1.08, "GBPUSD": 1.27, "USDJPY": 149.0,
        "600519": 1800.0, "000858": 155.0, "601318": 48.0, "300750": 210.0,
    }.get(symbol, 100.0)
    closes = [base_price]
    for i in range(1, days):
        h = _seed("%s:%s:%d" % (symbol, start_date, i))
        change = (h - 0.5) * 0.04 * closes[-1]
        closes.append(max(0.01, closes[-1] + change))
    return closes

def _generate_volumes(closes, seed_str):
    return [int(1000 + _seed(seed_str + ":vol:%d" % i) * 9000) for i in range(len(closes))]

def _apply_slippage(price, side, bps):
    f = bps / 10000.0
    return price * (1 + f) if side == "buy" else price * (1 - f)

def _apply_commission(eq, bps):
    return eq * (1 - bps / 10000.0)

def _compute_returns(ec):
    return [(ec[i] - ec[i-1]) / ec[i-1] if ec[i-1] != 0 else 0 for i in range(1, len(ec))]

def _sharpe(ret, rf=0.02):
    if len(ret) < 2: return 0.0
    rd = rf / 252.0
    ex = [r - rd for r in ret]
    avg = sum(ex) / len(ex)
    var = sum((r - avg) ** 2 for r in ex) / (len(ex) - 1)
    return round(avg / max(math.sqrt(var), 1e-10) * math.sqrt(252), 4)

def _sortino(ret, rf=0.02):
    if len(ret) < 2: return 0.0
    rd = rf / 252.0
    ex = [r - rd for r in ret]
    avg = sum(ex) / len(ex)
    dv = sum(min(0, r) ** 2 for r in ex) / len(ex)
    return round(avg / max(math.sqrt(dv), 1e-10) * math.sqrt(252), 4)

def _calmar(ec, ann_ret):
    pk = ec[0]; mdd = 0.0
    for eq in ec:
        pk = max(pk, eq)
        mdd = max(mdd, (pk - eq) / pk * 100 if pk > 0 else 0)
    return round(ann_ret / mdd, 4) if mdd > 0 else 0.0

def _pf(trades):
    gp = sum(t.get("pnl_pct", 0) for t in trades if t.get("pnl_pct", 0) > 0)
    gl = abs(sum(t.get("pnl_pct", 0) for t in trades if t.get("pnl_pct", 0) < 0))
    return round(gp / gl, 2) if gl > 0 else (round(gp, 2) if gp > 0 else 0.0)

def _sample_eq(ec, n=50):
    if len(ec) <= n: return [round(e, 2) for e in ec]
    step = (len(ec) - 1) / (n - 1)
    return [round(ec[int(i * step)], 2) for i in range(n)]

def _std_metrics(ic, final_eq, ec, trades, days):
    pk = ic; mdd = 0.0
    for eq in ec:
        pk = max(pk, eq)
        mdd = max(mdd, (pk - eq) / pk * 100 if pk > 0 else 0)
    years = days / 252.0
    ann_return = ((final_eq / ic) ** (1.0 / max(years, 0.01)) - 1) * 100 if years > 0 else 0
    returns = _compute_returns(ec)
    wins = sum(1 for t in trades if t.get("pnl_pct", 0) > 0)
    total_sells = sum(1 for t in trades if t["type"] == "SELL")
    return {
        "profit": round((final_eq - ic) / ic * 100, 2),
        "max_drawdown": round(mdd, 2),
        "win_rate": round((wins / total_sells * 100) if total_sells > 0 else 0, 1),
        "total_trades": len(trades),
        "final_equity": round(final_eq, 2),
        "sharpe_ratio": _sharpe(returns),
        "sortino_ratio": _sortino(returns),
        "calmar_ratio": _calmar(ec, ann_return),
        "profit_factor": _pf(trades),
        "avg_trade_duration": 0,
        "max_consecutive_wins": 0,
        "max_consecutive_losses": 0,
        "equity_curve": _sample_eq(ec),
        "trades": _trade_rows(trades),
    }


def _trade_rows(trades):
    rows = []
    for item in (trades or [])[:200]:
        row = {}
        for key in ("type", "idx", "price", "pnl_pct"):
            if key in item and item[key] is not None:
                row[key] = item[key]
        if row.get("type"):
            rows.append(row)
    return rows

def _max_dd(ec):
    if not ec:
        return 0.0
    pk = ec[0]
    mdd = 0.0
    for item in ec:
        pk = max(pk, item)
        if pk > 0:
            mdd = max(mdd, (pk - item) / pk * 100.0)
    return round(mdd, 2)


def _replay_equity(closes, trades, initial_capital, commission_bps):
    by_idx = {}
    for item in trades or []:
        if item.get("idx") is None or item.get("price") is None:
            continue
        by_idx.setdefault(int(item["idx"]), []).append(item)
    cash = float(initial_capital)
    pos = 0.0
    eq = []
    for i, price in enumerate(closes):
        for item in by_idx.get(i, []):
            px = float(item["price"])
            if item.get("type") == "BUY" and px > 0:
                pos = cash / px
                cash = 0.0
            elif item.get("type") == "SELL" and pos > 0:
                cash = pos * px * (1 - float(commission_bps) / 10000.0)
                pos = 0.0
        eq.append(cash + pos * price)
    return eq


def _segment(ec, trades):
    if not ec:
        return {"profit": 0.0, "max_drawdown": 0.0, "total_trades": len(trades or []), "trades": trades or []}
    start = ec[0] if ec[0] else 1.0
    return {
        "profit": round((ec[-1] - start) / start * 100.0, 2),
        "max_drawdown": _max_dd(ec),
        "total_trades": len(trades or []),
        "trades": trades or [],
    }


def _attach_cut(result, closes, cut, initial_capital, commission_bps):
    try:
        cut = int(cut)
    except (TypeError, ValueError):
        return result
    if cut < 50 or cut >= len(closes) - 50:
        result["error"] = "Invalid cut"
        return result
    trades = result.get("trades") or []
    eq = _replay_equity(closes, trades, initial_capital, commission_bps)
    if len(eq) != len(closes):
        result["error"] = "Equity replay mismatch"
        return result
    is_tr = [t for t in trades if int(t.get("idx", -1)) < cut]
    oos_tr = [t for t in trades if int(t.get("idx", -1)) >= cut]
    result["cut"] = cut
    result["is"] = _segment(eq[:cut], is_tr)
    result["oos"] = _segment(eq[cut - 1:], oos_tr)
    return result


def _ema_macd(closes, short=12, long=26, signal=9, slippage_bps=0, commission_bps=0, initial_capital=10000):
    if len(closes) < long + signal: return {"error": "Not enough data"}
    def ema(data, p):
        r = [data[0]]; k = 2.0/(p+1)
        for i in range(1, len(data)): r.append(data[i]*k + r[-1]*(1-k))
        return r
    es = ema(closes, short); el = ema(closes, long)
    ml = [es[i]-el[i] for i in range(len(closes))]; sl = ema(ml, signal)
    bal = float(initial_capital); pos = 0; ep = 0.0; trades = []; ec = [bal]
    for i in range(long+signal, len(closes)):
        p = closes[i]
        if ml[i] > sl[i] and ml[i-1] <= sl[i-1] and pos == 0:
            bp = _apply_slippage(p, "buy", slippage_bps)
            pos = bal / bp; ep = bp; bal = _apply_commission(0, commission_bps)
            trades.append({"type":"BUY","idx":i,"price":round(bp,5)})
        elif ml[i] < sl[i] and ml[i-1] >= sl[i-1] and pos > 0:
            sp = _apply_slippage(p, "sell", slippage_bps)
            bal = _apply_commission(pos * sp, commission_bps)
            trades.append({"type":"SELL","idx":i,"price":round(sp,5),"pnl_pct":round((sp-ep)/ep*100,2)})
            pos = 0
        ec.append(bal + pos * p)
    if pos > 0:
        last = len(closes) - 1
        sp = _apply_slippage(closes[-1], "sell", slippage_bps)
        bal = _apply_commission(pos * sp, commission_bps)
        trades.append({"type":"SELL","idx":last,"price":round(sp,5),"pnl_pct":round((sp-ep)/ep*100,2)})
    return _std_metrics(initial_capital, bal, ec, trades, len(closes))

def _rsi_bt(closes, period=14, overbought=70, oversold=30, slippage_bps=0, commission_bps=0, initial_capital=10000):
    if len(closes) < period+1: return {"error":"Not enough data"}
    gains=[max(0,closes[i]-closes[i-1]) for i in range(1,len(closes))]
    losses=[max(0,closes[i-1]-closes[i]) for i in range(1,len(closes))]
    rsi=[50.0]*period
    for i in range(period,len(closes)):
        ag=sum(gains[i-period:i])/period; al=sum(losses[i-period:i])/period
        rsi.append(100-100/(1+ag/al) if al>0 else 100.0)
    bal=float(initial_capital); pos=0; ep=0.0; trades=[]; ec=[bal]
    for i in range(period,len(closes)):
        p=closes[i]; r=rsi[i]
        if r<oversold and pos==0:
            bp=_apply_slippage(p,"buy",slippage_bps); pos=bal/bp; ep=bp; bal=0
            trades.append({"type":"BUY","idx":i,"price":round(bp,5)})
        elif r>overbought and pos>0:
            sp=_apply_slippage(p,"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
            trades.append({"type":"SELL","idx":i,"price":round(sp,5),"pnl_pct":round((sp-ep)/ep*100,2)}); pos=0
        ec.append(bal+pos*p)
    if pos>0:
        last=len(closes)-1
        sp=_apply_slippage(closes[-1],"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
        trades.append({"type":"SELL","idx":last,"price":round(sp,5),"pnl_pct":round((sp-ep)/ep*100,2)})
    return _std_metrics(initial_capital, bal, ec, trades, len(closes))

def _sma_cross(closes, fast=20, slow=50, slippage_bps=0, commission_bps=0, initial_capital=10000):
    if len(closes)<slow+1: return {"error":"Not enough data"}
    def sma(d,p):
        r=[]
        for i in range(len(d)): r.append(None if i<p-1 else sum(d[i-p+1:i+1])/p)
        return r
    sf=sma(closes,fast); ss=sma(closes,slow)
    bal=float(initial_capital); pos=0; ep=0.0; trades=[]; ec=[bal]
    for i in range(slow+1,len(closes)):
        p=closes[i]
        if sf[i] and ss[i] and sf[i-1] and ss[i-1]:
            if sf[i]>ss[i] and sf[i-1]<=ss[i-1] and pos==0:
                bp=_apply_slippage(p,"buy",slippage_bps); pos=bal/bp; ep=bp; bal=0
                trades.append({"type":"BUY","idx":i,"price":round(bp,5)})
            elif sf[i]<ss[i] and sf[i-1]>=ss[i-1] and pos>0:
                sp=_apply_slippage(p,"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
                trades.append({"type":"SELL","idx":i,"price":round(sp,5),"pnl_pct":round((sp-ep)/ep*100,2)}); pos=0
        ec.append(bal+pos*p)
    if pos>0:
        last=len(closes)-1
        sp=_apply_slippage(closes[-1],"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
        trades.append({"type":"SELL","idx":last,"price":round(sp,5),"pnl_pct":round((sp-ep)/ep*100,2)})
    return _std_metrics(initial_capital, bal, ec, trades, len(closes))

def _turtle(closes, entry_period=20, exit_period=10, atr_period=14, slippage_bps=0, commission_bps=0, initial_capital=10000):
    if len(closes)<max(entry_period,atr_period)+2: return {"error":"Not enough data"}
    trs=[abs(closes[i]-closes[i-1]) for i in range(1,len(closes))]
    atr=[sum(trs[max(0,i-atr_period+1):i+1])/min(atr_period,i+1) for i in range(len(trs))]
    bal=float(initial_capital); pos=0; ep=0.0; sl=0.0; trades=[]; ec=[bal]
    for i in range(max(entry_period,atr_period),len(closes)):
        p=closes[i]; hh=max(closes[i-entry_period:i]); ll=min(closes[i-exit_period:i])
        av=atr[i-1] if i-1<len(atr) else atr[-1]
        if pos>0:
            if p<=sl or p<ll:
                sp=_apply_slippage(p,"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
                trades.append({"type":"SELL","idx":i,"price":round(sp,5),"pnl_pct":round((sp-ep)/ep*100,2)}); pos=0
            else: sl=max(sl, p-2*av)
        elif p>hh:
            bp=_apply_slippage(p,"buy",slippage_bps); pos=bal/bp; ep=bp; sl=bp-2*av
            bal=_apply_commission(0,commission_bps); trades.append({"type":"BUY","idx":i,"price":round(bp,5)})
        ec.append(bal+pos*p)
    if pos>0:
        last=len(closes)-1
        sp=_apply_slippage(closes[-1],"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
        trades.append({"type":"SELL","idx":last,"price":round(sp,5),"pnl_pct":round((sp-ep)/ep*100,2)})
    return _std_metrics(initial_capital, bal, ec, trades, len(closes))

def _grid(closes, grid_size_pct=2.0, grid_levels=5, slippage_bps=0, commission_bps=0, initial_capital=10000):
    if len(closes)<2: return {"error":"Not enough data"}
    bp=closes[0]; ipl=initial_capital/grid_levels; pos={}; bal=float(initial_capital); trades=[]; ec=[bal]
    for i in range(1,len(closes)):
        p=closes[i]
        for lv in range(1,grid_levels+1):
            tb=bp*(1-lv*grid_size_pct/100.0); ts=bp*(1+lv*grid_size_pct/100.0)
            if p<=tb and lv not in pos:
                bpx=_apply_slippage(p,"buy",slippage_bps); pos[lv]={"shares":ipl/bpx,"bp":bpx}
                bal-=_apply_commission(ipl,commission_bps); trades.append({"type":"BUY"})
            if p>=ts and lv in pos:
                sps=pos[lv]; sp2=_apply_slippage(p,"sell",slippage_bps)
                bal+=_apply_commission(sps["shares"]*sp2,commission_bps)
                trades.append({"type":"SELL","pnl_pct":round((sp2-sps["bp"])/sps["bp"]*100,2)}); del pos[lv]
        ec.append(bal+sum(v["shares"]*p for v in pos.values()))
    for lv in sorted(pos.keys()):
        sp=_apply_slippage(closes[-1],"sell",slippage_bps)
        bal+=_apply_commission(pos[lv]["shares"]*sp,commission_bps)
        trades.append({"type":"SELL","pnl_pct":round((sp-pos[lv]["bp"])/pos[lv]["bp"]*100,2)})
    return _std_metrics(initial_capital, bal, ec, trades, len(closes))

def _bollinger(closes, period=20, num_std=2.0, slippage_bps=0, commission_bps=0, initial_capital=10000):
    if len(closes)<period+1: return {"error":"Not enough data"}
    bal=float(initial_capital); pos=0; ep=0.0; trades=[]; ec=[bal]
    for i in range(period,len(closes)):
        p=closes[i]; w=closes[i-period:i]; m=sum(w)/period
        s=math.sqrt(sum((x-m)**2 for x in w)/period)
        u=m+num_std*s; l=m-num_std*s
        if pos>0 and p>=u:
            sp=_apply_slippage(p,"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
            trades.append({"type":"SELL","idx":i,"price":round(sp,5),"pnl_pct":round((sp-ep)/ep*100,2)}); pos=0
        elif pos==0 and p<=l:
            bp=_apply_slippage(p,"buy",slippage_bps); pos=bal/bp; ep=bp
            bal=_apply_commission(0,commission_bps); trades.append({"type":"BUY","idx":i,"price":round(bp,5)})
        ec.append(bal+pos*p)
    if pos>0:
        last=len(closes)-1
        sp=_apply_slippage(closes[-1],"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
        trades.append({"type":"SELL","idx":last,"price":round(sp,5),"pnl_pct":round((sp-ep)/ep*100,2)})
    return _std_metrics(initial_capital, bal, ec, trades, len(closes))

def _vwap(closes, volumes=None, volume_confirm_ratio=1.2, slippage_bps=0, commission_bps=0, initial_capital=10000):
    if len(closes)<21: return {"error":"Not enough data"}
    if volumes is None: volumes=_generate_volumes(closes,"vwap")
    bal=float(initial_capital); pos=0; ep=0.0; trades=[]; ec=[bal]
    cpv=0.0; cv=0.0; av20=sum(volumes[:20])/20.0
    for i in range(len(closes)):
        p=closes[i]; v=volumes[i]; cpv+=p*v; cv+=v; vwap=cpv/cv if cv>0 else p
        if i<20: av20=(av20*19+v)/20; ec.append(bal+pos*p); continue
        av20=(av20*19+v)/20; vc=v>av20*volume_confirm_ratio
        if pos>0 and p>vwap:
            sp=_apply_slippage(p,"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
            trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2)}); pos=0
        elif pos==0 and p<vwap and vc:
            bp=_apply_slippage(p,"buy",slippage_bps); pos=bal/bp; ep=bp
            bal=_apply_commission(0,commission_bps); trades.append({"type":"BUY"})
        ec.append(bal+pos*p)
    if pos>0:
        sp=_apply_slippage(closes[-1],"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
        trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2)})
    return _std_metrics(initial_capital, bal, ec, trades, len(closes))

REGIME_SMA = 50
REGIME_SLOPE = 0.004


def label_regimes(closes):
    n = len(closes)
    labels = ["range"] * n
    if n < REGIME_SMA:
        return labels
    acc = 0.0
    sma = []
    for i, price in enumerate(closes):
        acc += price
        if i >= REGIME_SMA:
            acc -= closes[i - REGIME_SMA]
        if i >= REGIME_SMA - 1:
            sma.append(acc / float(REGIME_SMA))
        else:
            sma.append(price)
    for i in range(REGIME_SMA, n):
        mid = sma[i] if sma[i] else 1.0
        slope = closes[i] / mid - 1.0
        if slope > REGIME_SLOPE:
            labels[i] = "up"
        elif slope < -REGIME_SLOPE:
            labels[i] = "down"
        else:
            labels[i] = "range"
    return labels


def _regime_counts(labels, start=0, end=None):
    if end is None:
        end = len(labels)
    out = {"up": 0, "down": 0, "range": 0}
    for name in labels[start:end]:
        out[name] = out.get(name, 0) + 1
    return out


def _holding(n, trades):
    flags = [0] * n
    hold = 0
    events = {}
    for item in trades or []:
        if item.get("idx") is None:
            continue
        events.setdefault(int(item["idx"]), []).append(item)
    for i in range(n):
        for item in events.get(i, []):
            if item.get("type") == "BUY":
                hold = 1
            elif item.get("type") == "SELL":
                hold = 0
        flags[i] = hold
    return flags


def _tag_regimes(result, closes):
    labels = label_regimes(closes)
    for item in result.get("trades") or []:
        idx = item.get("idx")
        if idx is None:
            continue
        idx = int(idx)
        if 0 <= idx < len(labels) and not item.get("regime"):
            item["regime"] = labels[idx]
    result["regimes"] = labels
    result["regime_counts"] = _regime_counts(labels)
    return result


def _regime_switch(closes, slippage_bps=0, commission_bps=0, initial_capital=10000):
    sma = _sma_cross(closes, slippage_bps=0, commission_bps=0, initial_capital=initial_capital)
    boll = _bollinger(closes, slippage_bps=0, commission_bps=0, initial_capital=initial_capital)
    if sma.get("error"):
        return sma
    if boll.get("error"):
        return boll
    labels = label_regimes(closes)
    pos_s = _holding(len(closes), sma.get("trades"))
    pos_b = _holding(len(closes), boll.get("trades"))
    bal = float(initial_capital)
    pos = 0.0
    ep = 0.0
    trades = []
    ec = [bal]
    for i, price in enumerate(closes):
        name = labels[i]
        if name == "up":
            want = pos_s[i]
        elif name == "range":
            want = pos_b[i]
        else:
            want = 0
        if want == 1 and pos == 0:
            bp = _apply_slippage(price, "buy", slippage_bps)
            pos = bal / bp if bp else 0.0
            ep = bp
            bal = 0.0
            trades.append({"type": "BUY", "idx": i, "price": round(bp, 5), "regime": name})
        elif want == 0 and pos > 0:
            sp = _apply_slippage(price, "sell", slippage_bps)
            bal = _apply_commission(pos * sp, commission_bps)
            trades.append({"type": "SELL", "idx": i, "price": round(sp, 5), "pnl_pct": round((sp - ep) / ep * 100, 2), "regime": name})
            pos = 0.0
        if i > 0:
            ec.append(bal + pos * price)
    if pos > 0:
        last = len(closes) - 1
        sp = _apply_slippage(closes[-1], "sell", slippage_bps)
        bal = _apply_commission(pos * sp, commission_bps)
        trades.append({"type": "SELL", "idx": last, "price": round(sp, 5), "pnl_pct": round((sp - ep) / ep * 100, 2), "regime": labels[-1]})
    return _std_metrics(initial_capital, bal, ec, trades, len(closes))


STRATEGIES = {
    "EMA_MACD": _ema_macd, "RSI": _rsi_bt, "SMA_CROSS": _sma_cross,
    "TURTLE": _turtle, "GRID": _grid, "BOLLINGER": _bollinger, "VWAP": _vwap,
    "REGIME_SWITCH": _regime_switch,
}

STRATEGY_DEFAULTS = {
    "EMA_MACD": {"short": 12, "long": 26, "signal": 9},
    "RSI": {"period": 14, "overbought": 70, "oversold": 30},
    "SMA_CROSS": {"fast": 20, "slow": 50},
    "TURTLE": {"entry_period": 20, "exit_period": 10, "atr_period": 14},
    "GRID": {"grid_size_pct": 2.0, "grid_levels": 5},
    "BOLLINGER": {"period": 20, "num_std": 2.0},
    "VWAP": {"volume_confirm_ratio": 1.2},
    "REGIME_SWITCH": {},
}

def run_backtest(strategy, symbol, start_date, params=None, slippage_bps=0, commission_bps=0, initial_capital=10000, closes=None, cut=None):
    if strategy not in STRATEGIES:
        return {"error": "Unknown strategy: %s. Supported: %s" % (strategy, ", ".join(sorted(STRATEGIES.keys())))}
    if closes:
        try:
            series = [float(x) for x in closes]
        except (TypeError, ValueError):
            return {"error": "Invalid close series"}
        if len(series) < 50:
            return {"error": "Not enough data"}
        closes = series
    else:
        closes = _generate_synthetic_ohlcv(symbol, start_date, days=365)
    volumes = _generate_volumes(closes, symbol + ":" + start_date)
    merged = dict(STRATEGY_DEFAULTS.get(strategy, {}))
    if params: merged.update(params)
    func = STRATEGIES[strategy]
    if strategy == "VWAP":
        result = func(closes, volumes=volumes, slippage_bps=slippage_bps, commission_bps=commission_bps, initial_capital=initial_capital, **merged)
    else:
        result = func(closes, slippage_bps=slippage_bps, commission_bps=commission_bps, initial_capital=initial_capital, **merged)
    if "error" not in result:
        result = _tag_regimes(result, closes)
    if cut is not None and "error" not in result:
        result = _attach_cut(result, closes, cut, initial_capital, commission_bps)
        labels = result.pop("regimes", None)
        if labels:
            result["regime_counts_is"] = _regime_counts(labels, 0, int(cut))
            result["regime_counts_oos"] = _regime_counts(labels, int(cut))
    result.pop("regimes", None)
    return result

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class BacktestHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        sys.stderr.write("[%s] %s\n" % (ts, fmt % args))

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0: return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            now = datetime.utcnow()
            self._send_json({
                "status": "healthy", "service": SERVICE_NAME, "version": VERSION,
                "worker_id": WORKER_ID, "strategies": sorted(STRATEGIES.keys()),
                "stock_count": len(STRATEGIES),
                "uptime_seconds": round((now - _start_time).total_seconds(), 3),
                "timestamp": now.isoformat(),
            })
        elif path == "/strategies":
            self._send_json({
                "strategies": {n: STRATEGY_DEFAULTS.get(n, {}) for n in STRATEGIES},
                "total": len(STRATEGIES), "version": VERSION,
            })
        elif path == "/version":
            self._send_json({
                "name": SERVICE_NAME, "version": VERSION, "worker_id": WORKER_ID,
                "strategies": sorted(STRATEGIES.keys()),
                "python": "%d.%d.%d" % sys.version_info[:3],
            })
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/backtest":
            try: body = self._read_body()
            except Exception:
                self._send_json({"error": "Invalid JSON"}, 400); return
            strategy = body.get("strategy", "")
            symbol = body.get("symbol", "")
            start = body.get("start", "")
            if not strategy or not symbol or not start:
                self._send_json({"error": "Missing required fields: strategy, symbol, start"}, 400); return
            slippage_bps = body.get("slippage_bps", body.get("params", {}).get("slippage_bps", 0))
            commission_bps = body.get("commission_bps", body.get("params", {}).get("commission_bps", 0))
            initial_capital = body.get("initial_capital", body.get("params", {}).get("initial_capital", 10000))
            raw_close = body.get("close") or body.get("closes")
            raw_cut = body.get("cut", body.get("params", {}).get("cut"))
            t0 = time.perf_counter()
            result = run_backtest(strategy, symbol, start, body.get("params"), slippage_bps, commission_bps, initial_capital, closes=raw_close, cut=raw_cut)
            elapsed = (time.perf_counter() - t0) * 1000
            if "error" in result:
                self._send_json({"success": False, "error": result["error"], "strategy": strategy,
                    "symbol": symbol, "start": start, "calculation_time_ms": round(elapsed, 3),
                    "timestamp": datetime.utcnow().isoformat()}); return
            self._send_json({
                "success": True, "strategy": strategy, "symbol": symbol, "start": start,
                "slippage_bps": slippage_bps, "commission_bps": commission_bps,
                "initial_capital": initial_capital, "profit": result["profit"],
                "max_drawdown": result["max_drawdown"], "win_rate": result["win_rate"],
                "total_trades": result["total_trades"], "final_equity": result["final_equity"],
                "sharpe_ratio": result["sharpe_ratio"], "sortino_ratio": result["sortino_ratio"],
                "calmar_ratio": result["calmar_ratio"], "profit_factor": result["profit_factor"],
                "avg_trade_duration": result["avg_trade_duration"],
                "max_consecutive_wins": result["max_consecutive_wins"],
                "max_consecutive_losses": result["max_consecutive_losses"],
                "equity_curve": result["equity_curve"],
                "trades": result.get("trades") or [],
                "cut": result.get("cut"),
                "is": result.get("is"),
                "oos": result.get("oos"),
                "regime_counts": result.get("regime_counts"),
                "regime_counts_is": result.get("regime_counts_is"),
                "regime_counts_oos": result.get("regime_counts_oos"),
                "calculation_time_ms": round(elapsed, 3),
                "timestamp": datetime.utcnow().isoformat(),
            })
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

def main():
    server = ThreadedHTTPServer(("0.0.0.0", PORT), BacktestHandler)
    print("=" * 60)
    print("  TradeMind Backtest Worker v%s" % VERSION)
    print("  Worker ID: %s" % WORKER_ID)
    print("  Port: %d" % PORT)
    print("  Strategies: %d (%s)" % (len(STRATEGIES), ", ".join(sorted(STRATEGIES.keys()))))
    print("  Features: slippage/commission, Sharpe/Sortino/Calmar, equity curve")
    print("  Python: %s" % sys.version.split()[0])
    print("  Started: %s" % datetime.now().isoformat())
    print("=" * 60)
    sys.stdout.flush()
    try: server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == "__main__":
    main()
