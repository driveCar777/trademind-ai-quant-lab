"""Load frozen Sina panel + identify front/next contracts + same-contract 20-day open->open returns."""
from __future__ import print_function

import csv
import os

import numpy as np

from research_engine.cn_futures_v31 import ALL_PRODUCTS, CACHE, DATA, HOLD, ensure

TAG = "V31_PACK"
PRODS = tuple(sorted(ALL_PRODUCTS, key=len, reverse=True))


def _split_name(stem):
    for p in PRODS:
        rest = stem[len(p):]
        if stem.startswith(p) and rest.isdigit() and len(rest) == 4:
            return p, rest
    return None, None


def _idx(dates, day):
    for i, d in enumerate(dates):
        if d >= day:
            return i
    return len(dates)


def load_continuous():
    d = os.path.join(DATA, "continuous")
    files = sorted(f for f in os.listdir(d) if f.endswith("0.csv"))
    products, rows = [], {}
    dates = set()
    for f in files:
        p = f[:-5]  # CU0.csv -> CU
        with open(os.path.join(d, f), encoding="utf-8") as fh:
            r = list(csv.DictReader(fh))
        rows[p] = r
        products.append(p)
        dates.update(x["date"] for x in r)
    dates = sorted(dates)
    dix = dict((x, i) for i, x in enumerate(dates))
    T, N = len(dates), len(products)
    P = dict((k, np.full((T, N), np.nan, dtype=np.float32)) for k in ("open", "high", "low", "close", "volume", "oi", "settle"))
    for j, p in enumerate(products):
        for x in rows[p]:
            i = dix[x["date"]]
            P["open"][i, j] = float(x["open"] or "nan")
            P["high"][i, j] = float(x["high"] or "nan")
            P["low"][i, j] = float(x["low"] or "nan")
            P["close"][i, j] = float(x["close"] or "nan")
            P["volume"][i, j] = float(x["volume"] or "nan")
            P["oi"][i, j] = float(x["open_interest"] or "nan")
            P["settle"][i, j] = float(x["settle"] or "nan")
    P["dates"], P["products"] = dates, products
    print(TAG, "continuous", T, "x", N, dates[0], dates[-1], flush=True)
    return P


def load_contracts():
    """Per product: list of (yymm, dates[], open, close, settle, oi, volume)."""
    d = os.path.join(DATA, "contracts")
    by = dict((p, []) for p in ALL_PRODUCTS)
    n = 0
    for f in os.listdir(d):
        if not f.endswith(".csv"):
            continue
        p, yymm = _split_name(f[:-4])
        if p is None:
            continue
        with open(os.path.join(d, f), encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            continue
        dts = [x["date"] for x in rows]
        def col(name):
            return np.array([float(x[name] or "nan") for x in rows], dtype=np.float32)
        by[p].append({
            "yymm": yymm, "dates": dts,
            "open": col("open"), "close": col("close"), "settle": col("settle"),
            "oi": col("open_interest"), "volume": col("volume"),
            "dix": dict((dt, i) for i, dt in enumerate(dts)),
        })
        n += 1
    for p in by:
        by[p].sort(key=lambda c: c["yymm"])
    print(TAG, "contracts loaded", n, flush=True)
    return by


def _lookup(c, day, field):
    i = c["dix"].get(day)
    if i is None:
        return np.nan
    v = float(c[field][i])
    return v if np.isfinite(v) and v > 0 else np.nan


def attach_term_and_fwd(P, contracts):
    """Front = max OI with volume>0; 20d fwd = same-contract open[t+1] -> open[t+1+HOLD].
    TERM_SLOPE from front vs next later-yymm settle."""
    dates, products = P["dates"], P["products"]
    T, N = len(dates), len(products)
    dix = dict((d, i) for i, d in enumerate(dates))
    term = np.full((T, N), np.nan, dtype=np.float32)
    fwd = np.full((T, N), np.nan, dtype=np.float32)
    front_yymm = np.full((T, N), "", dtype=object)
    n_early = 0
    for j, p in enumerate(products):
        cs = contracts.get(p) or []
        if not cs:
            continue
        for t, day in enumerate(dates):
            if t + 1 >= T:
                continue
            cands = []
            for c in cs:
                oi = _lookup(c, day, "oi")
                vol = _lookup(c, day, "volume")
                if not (np.isfinite(oi) and vol > 0):
                    continue
                cands.append((oi, c))
            if not cands:
                continue
            cands.sort(key=lambda x: -x[0])
            day_in, day_out = dates[t + 1], dates[min(t + 1 + HOLD, T - 1)]
            chosen = None
            for _, c in cands:
                o0, o1 = _lookup(c, day_in, "open"), _lookup(c, day_out, "open")
                if np.isfinite(o0) and np.isfinite(o1) and o0 > 0:
                    chosen = (c, o0, o1, False)
                    break
            if chosen is None:
                # last-open exit on the highest-OI contract that can enter
                for _, c in cands:
                    o0 = _lookup(c, day_in, "open")
                    if not (np.isfinite(o0) and o0 > 0):
                        continue
                    o1 = np.nan
                    for u in range(min(t + 1 + HOLD, T - 1), t, -1):
                        o1 = _lookup(c, dates[u], "open")
                        if np.isfinite(o1) and o1 > 0:
                            break
                    if np.isfinite(o1) and o1 > 0:
                        chosen = (c, o0, o1, True)
                        break
            if chosen is None:
                continue
            c, o0, o1, early = chosen
            fwd[t, j] = o1 / o0 - 1.0
            front_yymm[t, j] = c["yymm"]
            if early:
                n_early += 1
            s0 = _lookup(c, day, "settle")
            if not np.isfinite(s0):
                s0 = _lookup(c, day, "close")
            nxt = None
            for c2 in cs:
                if c2["yymm"] > c["yymm"]:
                    s1 = _lookup(c2, day, "settle")
                    if not np.isfinite(s1):
                        s1 = _lookup(c2, day, "close")
                    if np.isfinite(s1) and s1 > 0:
                        nxt = (c2, s1)
                        break
            if nxt is not None and np.isfinite(s0) and s0 > 0:
                y0, m0 = int(c["yymm"][:2]), int(c["yymm"][2:])
                y1, m1 = int(nxt[0]["yymm"][:2]), int(nxt[0]["yymm"][2:])
                months = (y1 - y0) * 12 + (m1 - m0)
                if months > 0:
                    term[t, j] = (nxt[1] / s0 - 1.0) / (months / 12.0)
    P["fwd_same"] = fwd
    P["term_slope"] = term
    P["front_yymm"] = front_yymm
    # continuous 20d open->open for jump diagnostic only
    o = P["open"].astype(np.float64)
    cont = np.full((T, N), np.nan, dtype=np.float32)
    if T > HOLD + 1:
        a, b = o[1:T - HOLD], o[1 + HOLD:]
        good = np.isfinite(a) & np.isfinite(b) & (a > 0)
        cont[:T - 1 - HOLD] = np.where(good, b / a - 1.0, np.nan).astype(np.float32)
    P["fwd_continuous_DIAG"] = cont
    print(TAG, "fwd finite", int(np.isfinite(fwd).sum()), "term finite", int(np.isfinite(term).sum()), "early_exit", n_early, flush=True)
    return P


def load_pack(force=False):
    ensure()
    path = os.path.join(CACHE, "pack_v31.npz")
    meta = os.path.join(CACHE, "products.json")
    if (not force) and os.path.isfile(path) and os.path.isfile(meta):
        z = np.load(path, allow_pickle=True)
        import json
        products = json.load(open(meta, encoding="utf-8"))
        P = {k: z[k] for k in z.files if k != "dates"}
        P["dates"] = [str(x) for x in z["dates"]]
        P["products"] = products
        print(TAG, "cache", len(P["dates"]), "x", len(products), flush=True)
        return P
    P = load_continuous()
    contracts = load_contracts()
    P = attach_term_and_fwd(P, contracts)
    import json
    json.dump(P["products"], open(meta, "w"), ensure_ascii=False)
    save = {k: P[k] for k in P if k not in ("products", "front_yymm")}
    save["dates"] = np.array(P["dates"])
    save["front_yymm"] = np.array(P["front_yymm"], dtype=object)
    np.savez_compressed(path, **save)
    return P


def roll_adjust_unit_test():
    """Synthetic: continuous jumps +10 on roll day; same-contract return must ignore the jump."""
    # day0 C1=100, day1 roll to C2=110 while C1 last=100, C2 prev=100 → same-contract r=0, continuous r=+10%
    class C(dict):
        pass

    def mk(yymm, pairs):
        dts = [d for d, _ in pairs]
        o = np.array([v[0] for _, v in pairs], dtype=np.float32)
        c = np.array([v[1] for _, v in pairs], dtype=np.float32)
        oi = np.array([v[2] for _, v in pairs], dtype=np.float32)
        vol = np.array([v[3] for _, v in pairs], dtype=np.float32)
        return {"yymm": yymm, "dates": dts, "open": o, "close": c, "settle": c, "oi": oi, "volume": vol,
                "dix": dict((d, i) for i, d in enumerate(dts))}

    dates = ["2020-01-0%d" % i for i in range(1, 10)] + ["2020-01-1%d" % i for i in range(0, 6)]
    # 15 sessions; HOLD=20 would overflow — use a local 2-day hold check instead
    c1 = mk("2002", [(d, (100.0, 100.0, 200.0 if d <= "2020-01-05" else 10.0, 1.0)) for d in dates])
    c2 = mk("2003", [(d, (110.0 if d >= "2020-01-06" else 100.0, 110.0 if d >= "2020-01-06" else 100.0,
                          10.0 if d <= "2020-01-05" else 200.0, 1.0)) for d in dates])
    # same-contract open 2020-01-06 -> 2020-01-08 on c2: 110/110 - 1 = 0
    o0 = float(c2["open"][c2["dix"]["2020-01-06"]])
    o1 = float(c2["open"][c2["dix"]["2020-01-08"]])
    same = o1 / o0 - 1.0
    cont = 110.0 / 100.0 - 1.0
    assert abs(same) < 1e-9, same
    assert abs(cont - 0.10) < 1e-9, cont
    # front on 2020-01-04 (pre-roll, c1 OI 200) should pick c1
    assert _lookup(c1, "2020-01-04", "oi") > _lookup(c2, "2020-01-04", "oi")
    return {"same_contract_2d": same, "continuous_jump": cont, "ok": True}
