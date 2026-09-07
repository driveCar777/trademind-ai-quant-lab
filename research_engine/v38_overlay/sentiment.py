"""V38-S2 O3_SENT: market-level retail-sentiment exposure overlay on the frozen V26.8 book. One read. Contract:
docs/research_engine/V38_O3_SENTIMENT_CONTRACT.md."""
from __future__ import print_function

import gzip
import json
import os
import ssl
import time
import urllib.parse
import urllib.request

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.cn_a_share_margin_v23 import NORM as MARGIN_NORM
from research_engine.cn_a_share_strategy_v14_1.scores import eligible
from research_engine.v38_overlay import OUT, REDUCED, V25_OUT
from research_engine.v38_overlay.run import apply_overlay, load_curve, metrics

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SENT_RAW = os.path.join(ROOT, "data", "market", "cn_a_share", "sentiment", "raw")
READ = os.path.join(OUT, "V38_O3_SENTIMENT_READ.json")
Z_WIN = 250
Z_WIN_MONTHS = 36
CHG = 20
LIMIT_UP = 0.095
THRESH = 1.0
NEWACCT_LAG_DAYS = 15
TAG = "V38_O3"


def fetch_new_accounts():
    os.makedirs(SENT_RAW, exist_ok=True)
    dest = os.path.join(SENT_RAW, "RPT_STOCK_OPEN_DATA.json.gz")
    if os.path.isfile(dest):
        with gzip.open(dest, "rt", encoding="utf-8") as fh:
            return json.load(fh)["rows"]
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    q = {"reportName": "RPT_STOCK_OPEN_DATA", "columns": "ALL", "source": "WEB", "client": "WEB", "pageSize": "500", "pageNumber": "1",
         "sortColumns": "STATISTICS_DATE", "sortTypes": "1"}
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}), timeout=60, context=ctx) as h:
        rows = json.loads(h.read().decode("utf-8"))["result"]["data"]
    with gzip.open(dest, "wt", encoding="utf-8") as fh:
        json.dump({"report": "RPT_STOCK_OPEN_DATA", "n": len(rows), "rows": rows, "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, fh, ensure_ascii=False)
    return rows


def _roll_z(x, w):
    z = np.full(x.size, np.nan)
    for i in range(w, x.size):
        h = x[i - w + 1:i + 1]
        h = h[np.isfinite(h)]
        if h.size >= w // 2 and np.isfinite(x[i]) and h.std(ddof=1) > 0:
            z[i] = (x[i] - h.mean()) / h.std(ddof=1)
    return z


def _roll_mean(x, w):
    out = np.full(x.size, np.nan)
    for i in range(w - 1, x.size):
        h = x[i - w + 1:i + 1]
        if np.isfinite(h).sum() >= w // 2:
            out[i] = np.nanmean(h)
    return out


def components(pack):
    dates = pack["dates"]
    T = len(dates)
    elig = eligible(pack, 20)
    close = np.asarray(pack["close"], dtype=float)
    pre = np.asarray(pack["preclose"], dtype=float)
    turn = np.asarray(pack["turn"], dtype=float)
    with np.errstate(all="ignore"):
        ret = np.where((close > 0) & (pre > 0), close / pre - 1.0, np.nan)
        n = np.maximum(elig.sum(axis=1), 1)
        lu = np.where(elig.sum(axis=1) >= 100, np.nansum(np.where(elig, ret >= LIMIT_UP, 0.0), axis=1) / n, np.nan)
        turn_med = np.array([np.nanmedian(turn[t][elig[t] & (turn[t] > 0)]) if elig[t].sum() >= 100 else np.nan for t in range(T)])
        rzye = np.load(os.path.join(MARGIN_NORM, "RZYE.npy"))
        agg = np.nansum(np.where(np.isfinite(rzye), rzye, 0.0), axis=1).astype(float)
        agg = np.where(agg > 0, np.log(agg), np.nan)
        mchg = np.full(T, np.nan)
        mchg[CHG:] = agg[CHG:] - agg[:-CHG]
    comp = {"MARGIN_Z": _roll_z(mchg, Z_WIN), "TURN_Z": _roll_z(_roll_mean(turn_med, CHG), Z_WIN), "LIMITUP_Z": _roll_z(_roll_mean(lu, CHG), Z_WIN)}
    # monthly new accounts -> visible from the 15th of the following month
    rows = fetch_new_accounts()
    ms = sorted((r["STATISTICS_DATE"], float(r["ADD_INVESTOR"])) for r in rows if r.get("ADD_INVESTOR") is not None)
    vals = np.array([v for _, v in ms])
    mz = _roll_z(vals, Z_WIN_MONTHS)
    vis = []
    for (ym, _), z in zip(ms, mz):
        y, m = int(ym[:4]), int(ym[5:7])
        m2, y2 = (m + 1, y) if m < 12 else (1, y + 1)
        vis.append(("%04d-%02d-%02d" % (y2, m2, NEWACCT_LAG_DAYS), z))
    na = np.full(T, np.nan)
    k = 0
    cur = np.nan
    for t, d in enumerate(dates):
        while k < len(vis) and vis[k][0] <= d:
            cur = vis[k][1]
            k += 1
        na[t] = cur
    comp["NEWACCT_Z"] = na
    stack = np.vstack([comp[c] for c in ("MARGIN_Z", "TURN_Z", "LIMITUP_Z", "NEWACCT_Z")])
    with np.errstate(all="ignore"):
        composite = np.where(np.isfinite(stack).sum(axis=0) >= 2, np.nanmean(stack, axis=0), np.nan)
    return dates, comp, composite


def main():
    if os.path.isfile(READ):
        raise SystemExit("V38 O3 already read once; refusing")
    os.makedirs(OUT, exist_ok=True)
    pack = load_pack()
    dates, comp, composite = components(pack)
    di = dict((d, i) for i, d in enumerate(dates))
    np.save(os.path.join(OUT, "O3_COMPOSITE.npy"), np.array(list(zip(dates, composite)), dtype=object), allow_pickle=True)
    rd = json.load(open(os.path.join(V25_OUT, "ML1_SCALED_UNIT_FULL_CONTRIB2K_MAIN_READ.json"), encoding="utf-8"))
    curves = {"research": load_curve("RESEARCH"), "validation": load_curve("VALIDATION")}
    trades = {"research": rd["research_trades"], "validation": rd["validation_trades"]}
    out = {"contract": "V38_O3_SENTIMENT_CONTRACT.md", "threshold": THRESH, "z_win": Z_WIN, "chg": CHG, "reduced_exposure": REDUCED,
           "denied_window_read": False, "components": list(comp.keys()), "rules": {}}
    res = {}
    for seg in ("research", "validation"):
        d, v = curves[seg]
        expo, sig = {}, []
        for tr in trades[seg]:
            sd = tr["signal_date"]
            i = di.get(sd)
            z = composite[i] if i is not None else np.nan
            on = bool(np.isfinite(z) and z > THRESH)
            expo[sd] = REDUCED if on else 1.0
            sig.append({"signal_date": sd, "z": None if not np.isfinite(z) else round(float(z), 3), "reduced": on, "ret": tr["ret"],
                        "parts": dict((c, None if not (i is not None and np.isfinite(comp[c][i])) else round(float(comp[c][i]), 2)) for c in comp)})
        v2, e = apply_overlay(d, v, trades[seg], expo)
        base, ov = metrics(d, v), metrics(d, v2)
        red = [s["ret"] for s in sig if s["reduced"]]
        res[seg] = {"base": base, "overlay": ov, "frac_periods_reduced": float(np.mean([s["reduced"] for s in sig])),
                    "mean_ret_when_reduced": float(np.mean(red)) if red else None,
                    "mean_ret_when_full": float(np.mean([s["ret"] for s in sig if not s["reduced"]])), "signals": sig}
        print(TAG, seg, "base", {k: round(x, 4) for k, x in base.items() if x is not None}, "overlay", {k: round(x, 4) for k, x in ov.items() if x is not None},
              "reduced %.0f%%" % (100 * res[seg]["frac_periods_reduced"]), "ret_reduced", res[seg]["mean_ret_when_reduced"], "ret_full", round(res[seg]["mean_ret_when_full"], 4), flush=True)
    vv = res["validation"]
    gate = {"validation_maxdd_improved": vv["overlay"]["daily_maxdd"] > vv["base"]["daily_maxdd"],
            "validation_sharpe_not_lower": (vv["overlay"]["sharpe_daily_ann"] or -9) >= (vv["base"]["sharpe_daily_ann"] or -9)}
    res["gate"] = gate
    res["verdict"] = "ADOPT_CANDIDATE" if all(gate.values()) else "REJECT"
    out["rules"]["O3_SENT"] = res
    dump_json(READ, out)
    print(TAG, "VERDICT", res["verdict"], gate, flush=True)


if __name__ == "__main__":
    main()
