"""V22 FUTURES_XS run: 3 pre-registered hypotheses, dual books, FDR, gates. Denied window never loaded."""
from __future__ import print_function

import json
import math
import os

import numpy as np
import pandas as pd

from research_engine.futures_xs_v22 import (
    COST_BPS, OUT, RESEARCH, VALIDATION, VOL_WINDOW, DATASET_ID, DENIED_START,
)

HYPS = ["FX1_XS_CARRY", "FX2_XS_MOM_12_1", "FX3_TSMOM_12"]
H11_TRADES = os.path.join(os.path.dirname(OUT), "cn_a_share_strategy_v14", "H11", "TRADES.csv")


def load_panel():
    p = pd.read_csv(os.path.join(OUT, "PANEL.csv"), parse_dates=["date"])
    assert p["date"].max() < pd.Timestamp(DENIED_START)
    return p


def monthly_frames(panel):
    """Return wide daily returns, month-end signals."""
    ret = panel.pivot(index="date", columns="root", values="held_ret").sort_index()
    carry = panel.pivot(index="date", columns="root", values="carry_ann").sort_index()
    ret = ret.clip(-0.5, 0.5)  # defensive clip on data errors; contract: not a tuning knob
    vol = ret.rolling(VOL_WINDOW, min_periods=40).std().shift(1)  # ex-ante
    # month ends = last session date in each calendar month
    me = ret.groupby([ret.index.year, ret.index.month]).apply(lambda g: g.index.max()).values
    me = pd.DatetimeIndex(sorted(me))
    # monthly returns from daily compounding
    mret = (1 + ret.fillna(0)).groupby([ret.index.year, ret.index.month]).prod() - 1
    mret.index = me
    # signals at month end
    px_idx = (1 + ret.fillna(0)).cumprod()
    px_me = px_idx.loc[me]
    mom_12_1 = px_me.shift(1) / px_me.shift(12) - 1  # t-12 -> t-1
    ts_12 = px_me / px_me.shift(12) - 1
    carry_me = carry.rolling(5, min_periods=1).mean().loc[me]  # 5-day mean to reduce roll noise
    vol_me = vol.loc[me]
    return mret, mom_12_1, ts_12, carry_me, vol_me


def build_weights(sig, vol, kind):
    """Weights for month t applied to month t+1 return."""
    W = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
    for t in sig.index:
        s = sig.loc[t].dropna()
        v = vol.loc[t].reindex(s.index)
        ok = s.index[v.notna() & (v > 0)]
        s = s.loc[ok]
        v = v.loc[ok]
        if len(s) < 10:
            continue
        iv = 1.0 / v
        if kind == "ts":
            w = np.sign(s) * iv
            w = w / iv.sum()  # gross 1.0
        else:
            n = len(s)
            k = max(1, n // 3)
            order = s.sort_values()
            short = order.index[:k]
            long = order.index[-k:]
            w = pd.Series(0.0, index=s.index)
            w.loc[long] = iv.loc[long] / iv.loc[long].sum()
            w.loc[short] = -iv.loc[short] / iv.loc[short].sum()
        W.loc[t, w.index] = w.values
    return W


def capital_book(W, mret, cost_bps):
    """Monthly net portfolio return: weights at t earn mret at t+1; cost on turnover."""
    r_next = mret.shift(-1).reindex(W.index)
    gross = (W * r_next).sum(axis=1)
    turnover = (W - W.shift(1).fillna(0)).abs().sum(axis=1)
    cost = turnover * cost_bps / 1e4
    net = gross - cost
    valid = W.abs().sum(axis=1) > 0
    return pd.DataFrame({"gross": gross, "turnover": turnover, "cost": cost, "net": net, "active": valid})


def rank_ic(sig, mret):
    r_next = mret.shift(-1)
    out = []
    for t in sig.index:
        s = sig.loc[t].dropna()
        r = r_next.loc[t].reindex(s.index).dropna()
        s = s.reindex(r.index)
        if len(s) >= 10:
            out.append(s.rank().corr(r.rank()))
        else:
            out.append(np.nan)
    return pd.Series(out, index=sig.index)


def stats(net):
    net = net.dropna()
    n = len(net)
    if n == 0:
        return {"n": 0}
    eq = (1 + net).cumprod()
    years = n / 12.0
    cagr = eq.iloc[-1] ** (1 / years) - 1 if years > 0 and eq.iloc[-1] > 0 else None
    dd = (eq / eq.cummax() - 1).min()
    mu, sd = net.mean(), net.std(ddof=1)
    sharpe = mu / sd * math.sqrt(12) if sd > 0 else None
    t = mu / (sd / math.sqrt(n)) if sd > 0 else None
    p = None
    if t is not None:
        # one-sided p via normal approx (n>=100 in research)
        p = 0.5 * math.erfc(t / math.sqrt(2))
    return {"n": n, "mean_m": mu, "std_m": sd, "total": eq.iloc[-1] - 1, "cagr": cagr,
            "maxdd": dd, "sharpe": sharpe, "t": t, "p_one_sided": p, "win_rate": float((net > 0).mean())}


def window(df, w):
    return df[(df.index >= pd.Timestamp(w[0])) & (df.index <= pd.Timestamp(w[1]))]


def bh(pvals, q=0.05):
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    disc = [False] * m
    thresh = 0
    for rank, i in enumerate(order, 1):
        if pvals[i] <= q * rank / m:
            thresh = rank
    for rank, i in enumerate(order, 1):
        if rank <= thresh:
            disc[i] = True
    return disc


def h11_monthly():
    if not os.path.isfile(H11_TRADES):
        return None
    h = pd.read_csv(H11_TRADES, parse_dates=["signal_date"])
    h["ym"] = h["signal_date"].dt.to_period("M")
    return h.groupby("ym")["ret"].mean()


def main():
    panel = load_panel()
    mret, mom, ts, carry, vol = monthly_frames(panel)
    sigs = {"FX1_XS_CARRY": (carry, "xs"), "FX2_XS_MOM_12_1": (mom, "xs"), "FX3_TSMOM_12": (ts, "ts")}
    h11 = h11_monthly()
    results = []
    pvals = []
    os.makedirs(os.path.join(OUT, "EQUITY"), exist_ok=True)
    for hid in HYPS:
        sig, kind = sigs[hid]
        W = build_weights(sig, vol, kind)
        book = capital_book(W, mret, COST_BPS)
        book2 = capital_book(W, mret, COST_BPS * 2)
        ic = rank_ic(sig, mret)
        # the last row has no next-month return -> drop
        book = book.iloc[:-1]
        book2 = book2.iloc[:-1]
        book = book[book["active"]]
        book2 = book2.loc[book.index]
        res_b, val_b = window(book, RESEARCH), window(book, VALIDATION)
        res_b2 = window(book2, RESEARCH)
        r = {
            "id": hid,
            "research": {"capital": stats(res_b["net"]), "gross": stats(res_b["gross"]),
                         "capital_cost_x2": stats(res_b2["net"]),
                         "rank_ic_mean": float(window(ic, RESEARCH).mean()),
                         "avg_turnover": float(res_b["turnover"].mean())},
            "validation": {"capital": stats(val_b["net"]), "gross": stats(val_b["gross"]),
                           "rank_ic_mean": float(window(ic, VALIDATION).mean())},
        }
        pvals.append(r["research"]["capital"]["p_one_sided"] if r["research"]["capital"].get("p_one_sided") is not None else 1.0)
        # corr vs H11 on overlapping months (research+validation), diagnostic
        if h11 is not None:
            b = book["net"].copy()
            b.index = b.index.to_period("M")
            joined = pd.concat([b, h11], axis=1, join="inner").dropna()
            r["corr_vs_h11_month"] = float(joined.iloc[:, 0].corr(joined.iloc[:, 1])) if len(joined) >= 8 else None
            r["corr_vs_h11_n"] = int(len(joined))
        # yearly
        yr = book["net"].groupby(book.index.year).apply(lambda x: (1 + x).prod() - 1)
        r["yearly_net"] = {str(k): float(v) for k, v in yr.items()}
        eq = pd.DataFrame({"net": book["net"], "gross": book["gross"], "turnover": book["turnover"],
                           "equity": (1 + book["net"]).cumprod()})
        eq.to_csv(os.path.join(OUT, "EQUITY", hid + ".csv"))
        results.append(r)
        print(hid, "RES cagr", r["research"]["capital"].get("cagr"), "sharpe", r["research"]["capital"].get("sharpe"),
              "p", r["research"]["capital"].get("p_one_sided"), "| VAL cagr", r["validation"]["capital"].get("cagr"),
              "total", r["validation"]["capital"].get("total"), "| IC", r["research"]["rank_ic_mean"], r["validation"]["rank_ic_mean"])
    disc = bh(pvals)
    level1 = []
    for r, d in zip(results, disc):
        r["fdr_discovery"] = bool(d)
        g1 = d
        g2 = (r["research"]["capital_cost_x2"].get("cagr") or -1) > 0
        g3 = (r["validation"]["capital"].get("total") or -1) > 0 and (r["validation"]["capital"].get("mean_m") or -1) > 0
        g4 = r.get("corr_vs_h11_month") is None or r["corr_vs_h11_month"] <= 0.9
        r["gates"] = {"fdr": g1, "research_cost_x2_pos": g2, "validation_capital_pos": g3, "corr_h11_le_0_9": g4}
        r["level1"] = bool(g1 and g2 and g3 and g4)
        if r["level1"]:
            level1.append(r["id"])
    decision = "FUTURES_XS_V1_LEVEL_1_CANDIDATE" if level1 else "FUTURES_XS_V1_NO_CANDIDATE"
    payload = {
        "id": "V22_FUTURES_XS_RESULTS", "dataset_id": DATASET_ID, "cost_model": "FUTURES_XS_COST_MODEL_V1 %.0fbps one-way" % COST_BPS,
        "windows": {"research": RESEARCH, "validation": VALIDATION, "denied_from": DENIED_START, "denied_read": False},
        "m": len(HYPS), "fdr_q": 0.05, "fdr_discoveries": [r["id"] for r in results if r["fdr_discovery"]],
        "level1": level1, "decision": decision, "hypotheses": results,
    }
    with open(os.path.join(OUT, "RESULTS.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=lambda o: None if (isinstance(o, float) and math.isnan(o)) else str(o))
    print("FDR", payload["fdr_discoveries"], "LEVEL1", level1, decision)


if __name__ == "__main__":
    main()
