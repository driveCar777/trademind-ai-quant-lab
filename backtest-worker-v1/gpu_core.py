# Shared CUDA helpers for TradeMind Xavier workers. Python 3.6.
from __future__ import print_function

import math
import os
import threading

_cuda = "/usr/local/cuda-10.0/lib64"
_old = os.environ.get("LD_LIBRARY_PATH", "")
if _cuda not in _old:
    os.environ["LD_LIBRARY_PATH"] = _cuda + (":" + _old if _old else "")

_LOCK = threading.Lock()
_TORCH = None
_DEVICE = None
_NAME = ""
_READY = False
_ERR = ""


def _init():
    global _TORCH, _DEVICE, _NAME, _READY, _ERR
    if _READY or _ERR:
        return
    try:
        import torch
        _TORCH = torch
        if torch.cuda.is_available():
            _DEVICE = torch.device("cuda:0")
            _NAME = torch.cuda.get_device_name(0)
        else:
            _DEVICE = torch.device("cpu")
            _NAME = "cpu"
        _READY = True
    except Exception as exc:
        _ERR = str(exc)
        _READY = False


_init()


def gpu_ok():
    return bool(_READY and _DEVICE is not None and _DEVICE.type == "cuda")


def gpu_info():
    return {
        "gpu": gpu_ok(),
        "gpu_name": _NAME or "",
        "accelerator": "cuda" if gpu_ok() else "cpu",
        "gpu_error": _ERR,
    }


def warmup():
    if not gpu_ok():
        return False
    torch = _TORCH
    with _LOCK:
        x = torch.randn(1024, 1024, device=_DEVICE, dtype=torch.float32)
        y = torch.matmul(x, x)
        torch.cuda.synchronize()
        del x, y
    return True


def _t(values):
    return _TORCH.tensor(values, dtype=_TORCH.float64, device=_DEVICE)


def sma(values, period):
    n = len(values)
    if n < period or period < 1:
        return [None] * n
    if not gpu_ok():
        out = []
        for i in range(n):
            if i < period - 1:
                out.append(None)
            else:
                out.append(sum(values[i - period + 1:i + 1]) / float(period))
        return out
    with _LOCK:
        x = _t(values)
        means = x.unfold(0, period, 1).mean(dim=1)
        out = [None] * (period - 1)
        out.extend([float(v) for v in means.detach().cpu()])
        return out


def ema(values, period):
    if not values:
        return []
    k = 2.0 / (period + 1.0)
    if not gpu_ok():
        out = [values[0]]
        for i in range(1, len(values)):
            out.append(values[i] * k + out[-1] * (1.0 - k))
        return out
    torch = _TORCH
    with _LOCK:
        x = _t(values)
        n = int(x.numel())
        out_t = torch.empty_like(x)
        prev = x[0]
        out_t[0] = prev
        one_k = 1.0 - k
        for i in range(1, n):
            prev = x[i] * k + prev * one_k
            out_t[i] = prev
        return [float(v) for v in out_t.detach().cpu()]


def rsi(values, period=14):
    n = len(values)
    if n < period + 1:
        return []
    if not gpu_ok():
        gains = [max(0.0, values[i] - values[i - 1]) for i in range(1, n)]
        losses = [max(0.0, values[i - 1] - values[i]) for i in range(1, n)]
        out = [50.0] * period
        for i in range(period, n):
            ag = sum(gains[i - period:i]) / float(period)
            al = sum(losses[i - period:i]) / float(period)
            out.append(100.0 - 100.0 / (1.0 + ag / al) if al > 0 else 100.0)
        return out
    torch = _TORCH
    with _LOCK:
        x = _t(values)
        delta = x[1:] - x[:-1]
        gains = torch.clamp(delta, min=0.0)
        losses = torch.clamp(-delta, min=0.0)
        gwin = gains.unfold(0, period, 1).mean(dim=1)
        lwin = losses.unfold(0, period, 1).mean(dim=1)
        rs = gwin / torch.clamp(lwin, min=1e-12)
        rsi_t = torch.where(
            lwin > 0,
            100.0 - 100.0 / (1.0 + rs),
            torch.ones_like(lwin) * 100.0,
        )
        out = [50.0] * period
        out.extend([float(v) for v in rsi_t.detach().cpu()])
        return out


def rolling_mean_std(values, period):
    n = len(values)
    if n < period:
        return [], []
    if not gpu_ok():
        means, stds = [], []
        for i in range(period, n + 1):
            w = values[i - period:i]
            m = sum(w) / float(period)
            s = math.sqrt(sum((x - m) ** 2 for x in w) / float(period))
            means.append(m)
            stds.append(s)
        return means, stds
    torch = _TORCH
    with _LOCK:
        x = _t(values)
        w = x.unfold(0, period, 1)
        means = w.mean(dim=1)
        stds = w.std(dim=1, unbiased=False)
        return (
            [float(v) for v in means.detach().cpu()],
            [float(v) for v in stds.detach().cpu()],
        )


def atr(values, period):
    if len(values) < 2:
        return []
    trs = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
    if not gpu_ok():
        return [
            sum(trs[max(0, i - period + 1):i + 1]) / float(min(period, i + 1))
            for i in range(len(trs))
        ]
    torch = _TORCH
    with _LOCK:
        x = _t(trs)
        n = int(x.numel())
        csum = torch.cumsum(x, dim=0)
        out = []
        for i in range(n):
            start = max(0, i - period + 1)
            tot = csum[i] - (csum[start - 1] if start > 0 else 0.0)
            out.append(float(tot / float(i - start + 1)))
        return out


def max_drawdown_pct(equity):
    if not equity:
        return 0.0
    if not gpu_ok():
        pk = equity[0]
        mdd = 0.0
        for item in equity:
            pk = max(pk, item)
            if pk > 0:
                mdd = max(mdd, (pk - item) / pk * 100.0)
        return float(mdd)
    torch = _TORCH
    with _LOCK:
        # JetPack 4.2 ships PyTorch 1.4 — no torch.cummax yet.
        x = _t(equity)
        n = int(x.numel())
        peak = torch.empty_like(x)
        prev = x[0]
        peak[0] = prev
        for i in range(1, n):
            prev = torch.max(prev, x[i])
            peak[i] = prev
        dd = torch.where(peak > 0, (peak - x) / peak * 100.0, torch.zeros_like(x))
        return float(dd.max())


def sharpe(returns, rf=0.02):
    if len(returns) < 2:
        return 0.0
    if not gpu_ok():
        rd = rf / 252.0
        ex = [r - rd for r in returns]
        avg = sum(ex) / float(len(ex))
        var = sum((r - avg) ** 2 for r in ex) / float(len(ex) - 1)
        return avg / max(math.sqrt(var), 1e-10) * math.sqrt(252.0)
    torch = _TORCH
    with _LOCK:
        r = _t(returns)
        ex = r - (rf / 252.0)
        avg = ex.mean()
        var = ((ex - avg) ** 2).sum() / (ex.numel() - 1)
        return float(avg / _TORCH.clamp(var.sqrt(), min=1e-10) * math.sqrt(252.0))


def sortino(returns, rf=0.02):
    if len(returns) < 2:
        return 0.0
    if not gpu_ok():
        rd = rf / 252.0
        ex = [r - rd for r in returns]
        avg = sum(ex) / float(len(ex))
        dv = sum(min(0.0, r) ** 2 for r in ex) / float(len(ex))
        return avg / max(math.sqrt(dv), 1e-10) * math.sqrt(252.0)
    torch = _TORCH
    with _LOCK:
        r = _t(returns)
        ex = r - (rf / 252.0)
        avg = ex.mean()
        dv = _TORCH.clamp(ex, max=0.0).pow(2).mean()
        return float(avg / _TORCH.clamp(dv.sqrt(), min=1e-10) * math.sqrt(252.0))


def score_factors(rows):
    if not rows or not gpu_ok():
        return None
    torch = _TORCH

    def col(key, default=0.0):
        return [float(r.get(key, default) or 0.0) for r in rows]

    with _LOCK:
        pe = _t(col("pe", 15))
        pb = _t(col("pb", 3))
        ps = _t(col("ps", 3))
        div_y = _t(col("dividend_yield", 1.5))
        roe = _t(col("roe", 15))
        roa = _t(col("roa", 5))
        roe_3y = _t(col("roe_3y_avg", 15))
        pg = _t(col("profit_growth", 10))
        mom = _t(col("momentum_60d", 0))
        dr = _t(col("debt_ratio", 50))
        cr = _t(col("current_ratio", 1.5))
        vol = _t(col("volatility_60d", 20))
        vr = _t(col("volume_ratio", 1.0))
        mc = _t(col("market_cap_bn", 1000))

        pe_score = torch.clamp(25 - pe * 0.6, 0, 25)
        pb_score = torch.clamp(15 - pb * 1.2, 0, 15)
        ps_score = torch.clamp(10 - ps * 1.0, 0, 10)
        div_score = torch.clamp(div_y * 3, 0, 15)
        value = torch.clamp((pe_score + pb_score + ps_score + div_score) * 25 / 60, max=25)

        roe_score = torch.clamp(roe * 0.8, 0, 15)
        roa_score = torch.clamp(roa * 1.2, 0, 10)
        stability = torch.clamp(10 - (roe - roe_3y).abs() * 0.5, 0, 10)
        quality = torch.clamp((roe_score + roa_score + stability) * 25 / 35, max=25)

        pg_score = torch.clamp(pg * 0.5, -5, 15)
        mom_score = torch.clamp(mom * 1.0 + 5, 0, 15)
        momentum = torch.clamp((pg_score + mom_score) * 20 / 30, 0, 20)

        dr_score = torch.clamp((100 - dr) * 0.15, 0, 8)
        cr_score = torch.clamp(cr * 2, 0, 5)
        vol_score = torch.clamp((35 - vol) * 0.3, 0, 7)
        risk = torch.clamp((dr_score + cr_score + vol_score) * 15 / 20, max=15)

        vr_mid = (vr >= 0.8) & (vr <= 1.5)
        vr_low = vr < 0.8
        vr_score = torch.where(
            vr_mid,
            torch.ones_like(vr) * 10,
            torch.where(vr_low, torch.clamp(vr * 10, min=0), torch.clamp(15 - vr * 5, min=0)),
        )
        mc_score = torch.clamp(torch.log10(torch.clamp(mc, min=100)) * 2 - 4, 0, 10)
        liquidity = torch.clamp((vr_score + mc_score) * 15 / 20, max=15)

        total = torch.clamp(value + quality + momentum + risk + liquidity, 0, 100)
        out = []
        for i in range(len(rows)):
            out.append({
                "value": round(float(value[i]), 1),
                "quality": round(float(quality[i]), 1),
                "momentum": round(float(momentum[i]), 1),
                "risk": round(float(risk[i]), 1),
                "liquidity": round(float(liquidity[i]), 1),
                "total": round(float(total[i]), 1),
            })
        return out
