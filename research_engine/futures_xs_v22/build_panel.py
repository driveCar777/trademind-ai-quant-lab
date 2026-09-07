"""Build front/next daily panel from frozen zst CSVs. Deterministic. Writes PANEL.csv + PANEL_QUALITY.json."""
from __future__ import print_function

import glob
import hashlib
import io
import json
import os
import re

import pandas as pd
import zstandard

from research_engine.futures_xs_v22 import IMM, OUT, ROOTS, DENIED_START

OUTRIGHT = re.compile(r"^([A-Z0-9]{2,3}?)([FGHJKMNQUVXZ])(\d{1,2})$")
MONTH = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}


def parse_symbol(sym, session_year):
    m = OUTRIGHT.match(sym)
    if not m:
        return None
    root, mc, yy = m.group(1), m.group(2), m.group(3)
    if root not in ROOTS:
        # roots like "6E" are 2 chars; regex greedy issue handled by trying alternatives
        for r in ROOTS:
            if sym.startswith(r) and OUTRIGHT.match(sym) and sym[len(r):len(r) + 1] in MONTH:
                root = r
                mc = sym[len(r)]
                yy = sym[len(r) + 1:]
                break
        else:
            return None
    if len(yy) == 1:
        decade = (session_year // 10) * 10
        year = decade + int(yy)
        if year < session_year - 1:
            year += 10
    else:
        year = 2000 + int(yy)
    return root, year * 12 + MONTH[mc]


def load_raw():
    frames = []
    for f in sorted(glob.glob(os.path.join(IMM, "raw", "*.ohlcv-1d.csv.zst"))):
        raw = zstandard.ZstdDecompressor().stream_reader(open(f, "rb")).read()
        frames.append(pd.read_csv(io.BytesIO(raw)))
    df = pd.concat(frames, ignore_index=True)
    df["date"] = pd.to_datetime(df["ts_event"].str[:10])
    df = df[~df["symbol"].str.contains("-", na=False)]
    yrs = df["date"].dt.year.values
    parsed = [parse_symbol(s, int(y)) for s, y in zip(df["symbol"].values, yrs)]
    df["root"] = [p[0] if p else None for p in parsed]
    df["expm"] = [p[1] if p else None for p in parsed]
    df = df[df["root"].notna()].copy()
    df["expm"] = df["expm"].astype(int)
    df = df[(df["close"] > 0) & (df["volume"] >= 0)]
    return df


def build():
    df = load_raw()
    # drop denied window at panel level so no downstream code can read it
    df = df[df["date"] < pd.Timestamp(DENIED_START)]
    rows = []
    for (root, date), g in df.groupby(["root", "date"], sort=True):
        g = g[g["volume"] > 0]
        if g.empty:
            continue
        front = g.loc[g["volume"].idxmax()]
        later = g[g["expm"] > front["expm"]].sort_values("expm")
        nxt = later.iloc[0] if not later.empty else None
        rows.append({
            "date": date, "root": root,
            "front_symbol": front["symbol"], "front_expm": int(front["expm"]),
            "front_close": float(front["close"]), "front_volume": int(front["volume"]),
            "next_symbol": None if nxt is None else nxt["symbol"],
            "next_expm": None if nxt is None else int(nxt["expm"]),
            "next_close": None if nxt is None else float(nxt["close"]),
        })
    panel = pd.DataFrame(rows).sort_values(["root", "date"]).reset_index(drop=True)
    # held-contract daily return: same symbol close-to-close; on roll day use prior front symbol's return
    close_map = df.set_index(["symbol", "date"])["close"]
    prev_sym = panel.groupby("root")["front_symbol"].shift(1)
    prev_date = panel.groupby("root")["date"].shift(1)
    rets = []
    for sym, d, pd_, pc in zip(prev_sym, panel["date"], prev_date, panel["front_close"]):
        if not isinstance(sym, str):
            rets.append(None)
            continue
        c1 = close_map.get((sym, d))
        c0 = close_map.get((sym, pd_))
        rets.append(None if (c1 is None or c0 is None or c0 <= 0) else c1 / c0 - 1.0)
    panel["held_ret"] = rets
    panel["roll"] = (prev_sym.notna()) & (prev_sym != panel["front_symbol"])
    mb = (panel["next_expm"] - panel["front_expm"]).astype(float)
    panel["carry_ann"] = (panel["front_close"] / panel["next_close"] - 1.0) * 12.0 / mb
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    p = os.path.join(OUT, "PANEL.csv")
    panel.to_csv(p, index=False)
    sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
    q = {
        "n_rows": int(len(panel)),
        "roots": sorted(panel["root"].unique().tolist()),
        "n_roots": int(panel["root"].nunique()),
        "date_min": str(panel["date"].min().date()),
        "date_max": str(panel["date"].max().date()),
        "denied_excluded_from": DENIED_START,
        "per_root_days": panel.groupby("root").size().to_dict(),
        "per_root_first": {k: str(v.date()) for k, v in panel.groupby("root")["date"].min().items()},
        "roll_days": int(panel["roll"].sum()),
        "next_missing_frac": float(panel["next_close"].isna().mean()),
        "held_ret_missing_frac": float(panel["held_ret"].isna().mean()),
        "abs_daily_ret_gt_20pct": int((panel["held_ret"].abs() > 0.2).sum()),
        "panel_sha256": sha,
    }
    with open(os.path.join(OUT, "PANEL_QUALITY.json"), "w", encoding="utf-8") as f:
        json.dump(q, f, indent=2)
    print(json.dumps({k: v for k, v in q.items() if k not in ("per_root_days", "per_root_first")}, indent=1))
    print("roots", q["n_roots"], q["roots"])
    return panel


if __name__ == "__main__":
    build()
