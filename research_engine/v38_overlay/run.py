"""Run O1_TREND and O2_VOL once on the V26.8 research + validation books. Refuses a second read."""
from __future__ import print_function

import json
import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.cn_a_share_ml_v25.top_n_book import board_mask
from research_engine.cn_a_share_strategy_v14_1.scores import eligible
from research_engine.v38_overlay import OUT, READ, REDUCED, SMA, V25_OUT, VOL_MULT, VOL_WIN

TAG = "V38_OVERLAY"


def load_curve(name):
    c = np.load(os.path.join(V25_OUT, "V26_8_DAILY_CURVE_%s.npy" % name), allow_pickle=True)
    return [str(x) for x in c[:, 0]], np.array(c[:, 1], dtype=float)


def mb_ew_index(pack):
    """Equal-weight close-to-close index of the shell universe (main board, eligible, close <= 100)."""
    close = np.asarray(pack["close"], dtype=float)
    close = np.where(close > 0, close, np.nan)
    elig = eligible(pack, 20)
    shell = elig & board_mask(pack["symbols"], "MAIN")[None, :] & np.isfinite(close) & (close <= 100.0)
    r = close[1:] / close[:-1] - 1.0
    m = shell[1:] & shell[:-1] & np.isfinite(r)
    with np.errstate(all="ignore"):
        ew = np.where(m.sum(axis=1) >= 50, np.nansum(np.where(m, r, 0.0), axis=1) / np.maximum(m.sum(axis=1), 1), 0.0)
    idx = np.concatenate([[1.0], np.cumprod(1.0 + ew)])
    sma = np.full(idx.size, np.nan)
    cs = np.cumsum(idx)
    sma[SMA - 1:] = (cs[SMA - 1:] - np.concatenate([[0.0], cs[:-SMA]])) / SMA
    return dict(zip(pack["dates"], idx)), dict(zip(pack["dates"], sma))


def metrics(dates, v):
    dr = v[1:] / v[:-1] - 1.0
    dd = v / np.maximum.accumulate(v) - 1.0
    yrs = (np.datetime64(dates[-1]) - np.datetime64(dates[0])).astype(int) / 365.25
    return {"twr_total": float(v[-1] / v[0] - 1.0), "cagr": float((v[-1] / v[0]) ** (1.0 / yrs) - 1.0), "daily_maxdd": float(dd.min()),
            "sharpe_daily_ann": float(dr.mean() / dr.std(ddof=1) * np.sqrt(242.0)) if dr.std(ddof=1) > 0 else None,
            "n_days": int(v.size)}


def apply_overlay(dates, v, trades, expo):
    """expo: {signal_date: e}. Scale daily returns from each period's entry to the next entry."""
    dr = np.concatenate([[0.0], v[1:] / v[:-1] - 1.0])
    e = np.ones(v.size)
    di = dict((d, i) for i, d in enumerate(dates))
    for k, tr in enumerate(trades):
        i0 = di.get(tr["entry"])
        if i0 is None:
            continue
        i1 = di.get(trades[k + 1]["entry"], v.size) if k + 1 < len(trades) else v.size
        e[i0:i1] = expo.get(tr["signal_date"], 1.0)
    e[0] = 1.0
    v2 = v[0] * np.cumprod(1.0 + e * dr)
    return v2, e


def main():
    if os.path.isfile(READ):
        raise SystemExit("V38 overlay already read once; refusing")
    os.makedirs(OUT, exist_ok=True)
    rd = json.load(open(os.path.join(V25_OUT, "ML1_SCALED_UNIT_FULL_CONTRIB2K_MAIN_READ.json"), encoding="utf-8"))
    pack = load_pack()
    idx, sma = mb_ew_index(pack)
    curves = {"research": load_curve("RESEARCH"), "validation": load_curve("VALIDATION")}
    trades = {"research": rd["research_trades"], "validation": rd["validation_trades"]}
    # O2 threshold from research only: 20d std of research daily TWR returns
    rd_d, rd_v = curves["research"]
    r_res = rd_v[1:] / rd_v[:-1] - 1.0
    vol_series = np.array([r_res[i - VOL_WIN:i].std(ddof=1) for i in range(VOL_WIN, r_res.size)])
    vol_thr = float(np.median(vol_series) * VOL_MULT)
    # chained daily returns (research then validation) for the vol signal at validation signal dates
    vd_d, vd_v = curves["validation"]
    chain_d = rd_d + [d for d in vd_d if d > rd_d[-1]]
    chain_r = dict(zip(rd_d[1:], r_res))
    chain_r.update(dict(zip(vd_d[1:], vd_v[1:] / vd_v[:-1] - 1.0)))
    out = {"contract": "V38_OVERLAY_CONTRACT.md", "sma": SMA, "vol_win": VOL_WIN, "vol_mult": VOL_MULT, "vol_threshold": vol_thr,
           "reduced_exposure": REDUCED, "denied_window_read": False, "rules": {}}
    for rule in ("O1_TREND", "O2_VOL"):
        res = {}
        for seg in ("research", "validation"):
            d, v = curves[seg]
            expo, sig = {}, []
            for tr in trades[seg]:
                sd = tr["signal_date"]
                if rule == "O1_TREND":
                    on = bool(np.isfinite(sma.get(sd, np.nan)) and idx[sd] < sma[sd])
                else:
                    i = chain_d.index(sd) if sd in chain_d else -1
                    hist = [chain_r[x] for x in chain_d[max(1, i - VOL_WIN + 1):i + 1] if x in chain_r] if i > 0 else []
                    on = bool(len(hist) >= VOL_WIN and np.std(hist, ddof=1) > vol_thr)
                expo[sd] = REDUCED if on else 1.0
                sig.append({"signal_date": sd, "reduced": on, "ret": tr["ret"]})
            v2, e = apply_overlay(d, v, trades[seg], expo)
            base, ov = metrics(d, v), metrics(d, v2)
            res[seg] = {"base": base, "overlay": ov, "frac_periods_reduced": float(np.mean([s["reduced"] for s in sig])),
                        "mean_ret_when_reduced": float(np.mean([s["ret"] for s in sig if s["reduced"]])) if any(s["reduced"] for s in sig) else None,
                        "mean_ret_when_full": float(np.mean([s["ret"] for s in sig if not s["reduced"]])), "signals": sig}
            print(TAG, rule, seg, "base", {k: round(x, 4) for k, x in base.items() if x is not None}, "overlay", {k: round(x, 4) for k, x in ov.items() if x is not None},
                  "reduced %.0f%%" % (100 * res[seg]["frac_periods_reduced"]), flush=True)
        v = res["validation"]
        adopt = bool(v["overlay"]["daily_maxdd"] > v["base"]["daily_maxdd"] and (v["overlay"]["sharpe_daily_ann"] or -9) >= (v["base"]["sharpe_daily_ann"] or -9))
        res["verdict"] = "ADOPT_CANDIDATE" if adopt else "REJECT"
        res["gate"] = {"validation_maxdd_improved": v["overlay"]["daily_maxdd"] > v["base"]["daily_maxdd"],
                       "validation_sharpe_not_lower": (v["overlay"]["sharpe_daily_ann"] or -9) >= (v["base"]["sharpe_daily_ann"] or -9)}
        out["rules"][rule] = res
        print(TAG, rule, "VERDICT", res["verdict"], res["gate"], flush=True)
    dump_json(READ, out)
    print(TAG, "DONE", {k: v["verdict"] for k, v in out["rules"].items()}, flush=True)


if __name__ == "__main__":
    main()
