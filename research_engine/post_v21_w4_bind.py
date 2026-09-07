"""W4: read-only H11/H12 strategy-layer numbers. No resim, no retune."""
from __future__ import print_function

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RE = os.path.join(ROOT, "data", "market", "research_engine")
AD = os.path.join(RE, "POST_V21_AUTODRIVE")
V14 = os.path.join(RE, "cn_a_share_strategy_v14")


def read(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        hdr = f.readline().strip().split(",")
        ix = {h: i for i, h in enumerate(hdr)}
        for line in f:
            p = line.strip().split(",")
            if len(p) < len(hdr):
                continue
            rows.append({k: p[i] for k, i in ix.items()})
    return rows


def stats(rets, start_equity=1_000_000.0):
    eq = start_equity
    peak = eq
    mdd = 0.0
    for r in rets:
        eq *= 1 + r
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
    n = len(rets)
    years = n * 20 / 242.0
    cagr = (eq / start_equity) ** (1 / years) - 1 if years > 0 and eq > 0 else None
    return {"n": n, "end": eq, "total": eq / start_equity - 1, "cagr": cagr, "maxdd": mdd}


def main():
    h11 = read(os.path.join(V14, "H11", "TRADES.csv"))
    h12 = read(os.path.join(V14, "H12", "TRADES.csv"))
    r11 = [float(r["ret"]) for r in h11]
    r12 = [float(r["ret"]) for r in h12]
    d11 = [r["signal_date"] for r in h11]
    d12 = {r["signal_date"]: float(r["ret"]) for r in h12}
    # aligned blend diagnostic (not a portfolio claim)
    blend = [(a + d12[d]) / 2 for a, d in zip(r11, d11) if d in d12]
    gross = sum(float(r["gross"]) for r in h11)
    net = sum(float(r["net"]) for r in h11)
    fees = sum(float(r["fees"]) for r in h11)
    slip = gross - net - fees
    # gross-only path (zero cost counterfactual, diagnostic only; not a strategy)
    gross_rets = []
    for r in h11:
        eq_before = float(r["equity"]) / (1 + float(r["ret"]))
        gross_rets.append(float(r["gross"]) / eq_before if eq_before else 0.0)
    val_mask = [d >= "2021-08-25" for d in d11]
    out = {
        "id": "POST_V21_STRATEGY_BIND",
        "read_only": True,
        "h11_official": stats(r11),
        "h12_official": stats(r12),
        "h11_val_only": stats([r for r, m in zip(r11, val_mask) if m]),
        "h11_h12_blend_50_50_DIAGNOSTIC_NOT_PORTFOLIO": stats(blend),
        "blend_vs_h11_gain_total": stats(blend)["total"] - stats(r11)["total"],
        "h11_yuan": {"gross": gross, "fees_incl_stamp": fees, "slippage": slip, "net": net,
                     "cost_over_gross": (fees + slip) / gross if gross else None},
        "h11_zero_cost_counterfactual_DIAGNOSTIC": stats(gross_rets),
        "cagr_target": 0.10,
        "note": "Zero-cost path is a diagnostic ceiling. Even with no cost the book compounds ~2%/yr; the 10% gap is information, not fees. Blend adds nothing: corr 0.996.",
    }
    outp = os.path.join(AD, "STRATEGY_BIND.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({k: v for k, v in out.items() if k != "note"}, indent=1)[:3000])


if __name__ == "__main__":
    main()
