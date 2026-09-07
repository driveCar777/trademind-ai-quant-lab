"""V38-S2 O4_GLOBAL / O5_NORTH: global-index and northbound-flow exposure overlays on the frozen V26.8 book. One read.
Contract: docs/research_engine/V38_O4_O5_GLOBAL_NORTH_CONTRACT.md."""
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
from research_engine.v38_overlay import OUT, REDUCED, V25_OUT
from research_engine.v38_overlay.run import apply_overlay, load_curve, metrics
from research_engine.v38_overlay.sentiment import _roll_z

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "market", "cn_a_share", "sentiment", "raw")
READ = os.path.join(OUT, "V38_O4_O5_READ.json")
INDICES = ("^IXIC", "^DJI", "^N225", "^HSI")
Z_WIN = 250
CHG = 20
THRESH = -1.0
TAG = "V38_O4O5"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0"}


def _cache(name, fetch):
    os.makedirs(RAW, exist_ok=True)
    p = os.path.join(RAW, name + ".json.gz")
    if os.path.isfile(p):
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            return json.load(fh)["rows"]
    rows = fetch()
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        json.dump({"name": name, "n": len(rows), "rows": rows, "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, fh, ensure_ascii=False)
    return rows


def yahoo_closes(sym):
    def fetch():
        u = "https://query1.finance.yahoo.com/v8/finance/chart/%s?period1=946684800&period2=%d&interval=1d" % (urllib.parse.quote(sym), int(time.time()))
        d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60, context=CTX))
        r = d["chart"]["result"][0]
        return [(time.strftime("%Y-%m-%d", time.gmtime(t)), c) for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c is not None]
    return _cache("YAHOO_" + sym.strip("^"), fetch)


def northbound_daily():
    def fetch():
        rows, page = [], 1
        H = {"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/hsgt/"}
        while True:
            q = {"reportName": "RPT_MUTUAL_DEAL_HISTORY", "columns": "ALL", "source": "WEB", "client": "WEB", "pageSize": "500", "pageNumber": str(page),
                 "sortColumns": "TRADE_DATE", "sortTypes": "1", "filter": '(MUTUAL_TYPE in ("001","003"))'}
            u = "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(q)
            for attempt in range(6):
                try:
                    d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60, context=CTX))
                    break
                except Exception:  # noqa
                    time.sleep(2 * (attempt + 1))
            r = d.get("result") or {}
            data = r.get("data") or []
            rows.extend([{"d": x["TRADE_DATE"][:10], "t": x["MUTUAL_TYPE"], "net": x.get("NET_DEAL_AMT")} for x in data])
            if page >= int(r.get("pages") or 1) or not data:
                break
            page += 1
        return rows
    return _cache("EM_NORTHBOUND_DAILY", fetch)


def series_on_dates(dates, pairs, lag_days=0):
    """Map an irregular (date, value) series onto trading dates: last value with date <= trading date - lag_days."""
    pairs = sorted(pairs)
    out = np.full(len(dates), np.nan)
    k, cur = 0, np.nan
    for i, d in enumerate(dates):
        cut = d if lag_days == 0 else (np.datetime64(d) - np.timedelta64(lag_days, "D")).astype(str)
        while k < len(pairs) and pairs[k][0] <= cut:
            cur = pairs[k][1]
            k += 1
        out[i] = cur
    return out


def main():
    if os.path.isfile(READ):
        raise SystemExit("V38 O4/O5 already read once; refusing")
    os.makedirs(OUT, exist_ok=True)
    rd = json.load(open(os.path.join(V25_OUT, "ML1_SCALED_UNIT_FULL_CONTRIB2K_MAIN_READ.json"), encoding="utf-8"))
    curves = {"research": load_curve("RESEARCH"), "validation": load_curve("VALIDATION")}
    trades = {"research": rd["research_trades"], "validation": rd["validation_trades"]}
    # calendar of all trading dates (from the curves) for the signal series
    from research_engine.cn_a_share_alpha.pack import load_pack
    dates = load_pack()["dates"]
    # O4: mean of 4 index 20d returns (each index on its own calendar; mapped to A-share dates with 1 calendar-day lag)
    rets = []
    for sym in INDICES:
        pairs = yahoo_closes(sym)
        px = np.array([p for _, p in pairs], dtype=float)
        r20 = np.full(px.size, np.nan)
        r20[CHG:] = px[CHG:] / px[:-CHG] - 1.0
        rets.append(series_on_dates(dates, [(d, v) for (d, _), v in zip(pairs, r20) if np.isfinite(v)], lag_days=1))
    g = np.nanmean(np.vstack(rets), axis=0)
    g_z = _roll_z(g, Z_WIN)
    # O5: northbound 20d cumulative net buy (SH + SZ), same-day available
    nb = northbound_daily()
    agg = {}
    for x in nb:
        if x["net"] is not None:
            agg[x["d"]] = agg.get(x["d"], 0.0) + float(x["net"])
    nd = sorted(agg)
    nv = np.array([agg[d] for d in nd])
    cum20 = np.full(nv.size, np.nan)
    cs = np.cumsum(nv)
    cum20[CHG - 1:] = cs[CHG - 1:] - np.concatenate([[0.0], cs[:-CHG]])
    n = series_on_dates(dates, [(d, v) for d, v in zip(nd, cum20) if np.isfinite(v)])
    n_z = _roll_z(n, Z_WIN)
    di = dict((d, i) for i, d in enumerate(dates))
    out = {"contract": "V38_O4_O5_GLOBAL_NORTH_CONTRACT.md", "threshold": THRESH, "z_win": Z_WIN, "chg": CHG, "reduced_exposure": REDUCED,
           "indices": list(INDICES), "northbound_first": nd[0] if nd else None, "northbound_last_used": nd[-1] if nd else None,
           "denied_window_read": False, "rules": {}}
    for rule, z in (("O4_GLOBAL", g_z), ("O5_NORTH", n_z)):
        res = {}
        for seg in ("research", "validation"):
            d, v = curves[seg]
            expo, sig = {}, []
            for tr in trades[seg]:
                sd = tr["signal_date"]
                i = di.get(sd)
                zz = z[i] if i is not None else np.nan
                on = bool(np.isfinite(zz) and zz < THRESH)
                expo[sd] = REDUCED if on else 1.0
                sig.append({"signal_date": sd, "z": None if not np.isfinite(zz) else round(float(zz), 3), "reduced": on, "ret": tr["ret"]})
            v2, _ = apply_overlay(d, v, trades[seg], expo)
            base, ov = metrics(d, v), metrics(d, v2)
            red = [s["ret"] for s in sig if s["reduced"]]
            res[seg] = {"base": base, "overlay": ov, "frac_periods_reduced": float(np.mean([s["reduced"] for s in sig])),
                        "mean_ret_when_reduced": float(np.mean(red)) if red else None,
                        "mean_ret_when_full": float(np.mean([s["ret"] for s in sig if not s["reduced"]])), "signals": sig}
            print(TAG, rule, seg, "base", {k: round(x, 4) for k, x in base.items() if x is not None}, "overlay", {k: round(x, 4) for k, x in ov.items() if x is not None},
                  "reduced %.0f%%" % (100 * res[seg]["frac_periods_reduced"]), "ret_reduced", res[seg]["mean_ret_when_reduced"], flush=True)
        vv = res["validation"]
        gate = {"validation_maxdd_improved": vv["overlay"]["daily_maxdd"] > vv["base"]["daily_maxdd"],
                "validation_sharpe_not_lower": (vv["overlay"]["sharpe_daily_ann"] or -9) >= (vv["base"]["sharpe_daily_ann"] or -9)}
        res["gate"] = gate
        res["verdict"] = ("ADOPT_CANDIDATE" if all(gate.values()) else "REJECT") + ("_DIAGNOSTIC_NOT_DEPLOYABLE" if rule == "O5_NORTH" else "")
        out["rules"][rule] = res
        print(TAG, rule, "VERDICT", res["verdict"], gate, flush=True)
    dump_json(READ, out)
    print(TAG, "DONE", {k: v["verdict"] for k, v in out["rules"].items()}, flush=True)


if __name__ == "__main__":
    main()
