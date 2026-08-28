#!/usr/bin/env python3
"""V2.1 Backtest Worker - standalone test (no import)."""
import hashlib
import json
import math
import sys
import time

OUT = open(r'd:\AGXXAIVER-4-WINDOWS-1-STOCK\test-v21-out.txt', 'w', encoding='utf-8')
def P(msg):
    OUT.write(msg + '\n')
    OUT.flush()

def _seed(s):
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF

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

def _std_metrics(initial_capital, final_eq, equity_curve, trades, days):
    pk = initial_capital; mdd = 0.0
    for eq in equity_curve:
        pk = max(pk, eq)
        mdd = max(mdd, (pk - eq) / pk * 100 if pk > 0 else 0)
    years = days / 252.0
    ann_return = ((final_eq / initial_capital) ** (1.0 / max(years, 0.01)) - 1) * 100 if years > 0 else 0
    returns = _compute_returns(equity_curve)
    wins = sum(1 for t in trades if t.get("pnl_pct", 0) > 0)
    total_sells = sum(1 for t in trades if t["type"] == "SELL")
    return {
        "profit": round((final_eq - initial_capital) / initial_capital * 100, 2),
        "max_drawdown": round(mdd, 2),
        "win_rate": round((wins / total_sells * 100) if total_sells > 0 else 0, 1),
        "total_trades": len(trades),
        "final_equity": round(final_eq, 2),
        "sharpe_ratio": _sharpe(returns),
        "sortino_ratio": _sortino(returns),
        "calmar_ratio": _calmar(equity_curve, ann_return),
        "profit_factor": _pf(trades),
        "equity_curve": _sample_eq(equity_curve),
    }

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
        elif ml[i] < sl[i] and ml[i-1] >= sl[i-1] and pos > 0:
            sp = _apply_slippage(p, "sell", slippage_bps)
            bal = _apply_commission(pos * sp, commission_bps)
            trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2),"idx":i})
            pos = 0
        ec.append(bal + pos * p)
    if pos > 0:
        sp = _apply_slippage(closes[-1], "sell", slippage_bps)
        bal = _apply_commission(pos * sp, commission_bps)
        trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2),"idx":len(closes)-1})
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
            trades.append({"type":"BUY"})
        elif r>overbought and pos>0:
            sp=_apply_slippage(p,"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
            trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2)})
            pos=0
        ec.append(bal+pos*p)
    if pos>0:
        sp=_apply_slippage(closes[-1],"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
        trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2)})
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
            elif sf[i]<ss[i] and sf[i-1]>=ss[i-1] and pos>0:
                sp=_apply_slippage(p,"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
                trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2)})
                pos=0
        ec.append(bal+pos*p)
    if pos>0:
        sp=_apply_slippage(closes[-1],"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
        trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2)})
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
                trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2)}); pos=0
            else: sl=max(sl, p-2*av)
        elif p>hh:
            bp=_apply_slippage(p,"buy",slippage_bps); pos=bal/bp; ep=bp; sl=bp-2*av
            bal=_apply_commission(0,commission_bps); trades.append({"type":"BUY"})
        ec.append(bal+pos*p)
    if pos>0:
        sp=_apply_slippage(closes[-1],"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
        trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2)})
    return _std_metrics(initial_capital, bal, ec, trades, len(closes))

def _grid(closes, grid_size_pct=2.0, grid_levels=5, slippage_bps=0, commission_bps=0, initial_capital=10000):
    if len(closes)<2: return {"error":"Not enough data"}
    bp=closes[0]; ipl=initial_capital/grid_levels; pos={}; bal=float(initial_capital); trades=[]; ec=[bal]
    for i in range(1,len(closes)):
        p=closes[i]
        for lv in range(1,grid_levels+1):
            tb=bp*(1-lv*grid_size_pct/100.0); ts=bp*(1+lv*grid_size_pct/100.0)
            if p<=tb and lv not in pos:
                bpx=_apply_slippage(p,"buy",slippage_bps); pos[lv]={"shares":ipl/bpx,"bp":bpx}; bal-=_apply_commission(ipl,commission_bps)
                trades.append({"type":"BUY"})
            if p>=ts and lv in pos:
                sps=pos[lv]; sp2=_apply_slippage(p,"sell",slippage_bps); bal+=_apply_commission(sps["shares"]*sp2,commission_bps)
                trades.append({"type":"SELL","pnl_pct":round((sp2-sps["bp"])/sps["bp"]*100,2)}); del pos[lv]
        ec.append(bal+sum(v["shares"]*p for v in pos.values()))
    for lv in sorted(pos.keys()):
        sp=_apply_slippage(closes[-1],"sell",slippage_bps); bal+=_apply_commission(pos[lv]["shares"]*sp,commission_bps)
        trades.append({"type":"SELL","pnl_pct":round((sp-pos[lv]["bp"])/pos[lv]["bp"]*100,2)})
    return _std_metrics(initial_capital, bal, ec, trades, len(closes))

def _bollinger(closes, period=20, num_std=2.0, slippage_bps=0, commission_bps=0, initial_capital=10000):
    if len(closes)<period+1: return {"error":"Not enough data"}
    bal=float(initial_capital); pos=0; ep=0.0; trades=[]; ec=[bal]
    for i in range(period,len(closes)):
        p=closes[i]; w=closes[i-period:i]; m=sum(w)/period; s=math.sqrt(sum((x-m)**2 for x in w)/period)
        u=m+num_std*s; l=m-num_std*s
        if pos>0 and p>=u:
            sp=_apply_slippage(p,"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
            trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2)}); pos=0
        elif pos==0 and p<=l:
            bp=_apply_slippage(p,"buy",slippage_bps); pos=bal/bp; ep=bp; bal=_apply_commission(0,commission_bps)
            trades.append({"type":"BUY"})
        ec.append(bal+pos*p)
    if pos>0:
        sp=_apply_slippage(closes[-1],"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
        trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2)})
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
            bp=_apply_slippage(p,"buy",slippage_bps); pos=bal/bp; ep=bp; bal=_apply_commission(0,commission_bps)
            trades.append({"type":"BUY"})
        ec.append(bal+pos*p)
    if pos>0:
        sp=_apply_slippage(closes[-1],"sell",slippage_bps); bal=_apply_commission(pos*sp,commission_bps)
        trades.append({"type":"SELL","pnl_pct":round((sp-ep)/ep*100,2)})
    return _std_metrics(initial_capital, bal, ec, trades, len(closes))

# === TESTS ===
STRATEGIES = {
    "EMA_MACD": _ema_macd, "RSI": _rsi_bt, "SMA_CROSS": _sma_cross,
    "TURTLE": _turtle, "GRID": _grid, "BOLLINGER": _bollinger, "VWAP": _vwap,
}
passed = 0; failed = 0
P("=== V2.1 Backtest Worker Smoke Test ===")
P("Strategies: %d — %s" % (len(STRATEGIES), ", ".join(sorted(STRATEGIES.keys()))))
P("")
for name in sorted(STRATEGIES.keys()):
    closes = _generate_synthetic_ohlcv("XAUUSD", "2025-01-01")
    result = STRATEGIES[name](closes)
    if "error" in result:
        P("[FAIL] %s: %s" % (name, result["error"])); failed += 1
    else:
        ec_len = len(result.get("equity_curve", []))
        P("[PASS] %s: profit=%.2f%% sharpe=%.4f sortino=%.4f calmar=%.4f pf=%.2f trades=%d eq=%d" % (
            name, result["profit"], result["sharpe_ratio"], result["sortino_ratio"],
            result["calmar_ratio"], result["profit_factor"], result["total_trades"], ec_len))
        passed += 1

P("")
P("=== Slippage Test ===")
closes = _generate_synthetic_ohlcv("XAUUSD", "2025-01-01")
r0 = _ema_macd(closes)
r50 = _ema_macd(closes, slippage_bps=50, commission_bps=10)
P("Without cost: profit=%.2f%%" % r0["profit"])
P("With cost:    profit=%.2f%%" % r50["profit"])
slip = r50["profit"] < r0["profit"]
P("[%s] Slippage reduces profit" % ("PASS" if slip else "FAIL"))
if slip: passed += 1
else: failed += 1

P("")
P("=== Cross-Symbol (10x7=70 combos) ===")
combos_ok = 0; combos_total = 0
for sym in ["XAUUSD","EURUSD","GBPUSD","USDJPY","600519","000858","601318","300750","AAPL","GOOGL"]:
    closes = _generate_synthetic_ohlcv(sym, "2025-01-01")
    for name, func in STRATEGIES.items():
        combos_total += 1
        r = func(closes)
        if "error" not in r: combos_ok += 1
        else: P("  ERROR: %s/%s: %s" % (name, sym, r["error"]))
ok = combos_ok == combos_total
P("[%s] %d/%d combos OK" % ("PASS" if ok else "FAIL", combos_ok, combos_total))
if ok: passed += 1
else: failed += 1

P("")
P("=" * 50)
P("Results: %d passed, %d failed" % (passed, failed))
P("=" * 50)
OUT.close()
