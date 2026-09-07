"""W1: pairwise correlation of existing capital_ret series. Read-only. No resim."""
from __future__ import print_function

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RE = os.path.join(ROOT, "data", "market", "research_engine")
AD = os.path.join(RE, "POST_V21_AUTODRIVE")

BEAT_EW = [
    "H21_RESID_REV_20_H20", "H22_RESID_REV_60_H20", "H23_RESID_REV_20_H5",
    "H24_DISP_HIGH_RESID_20_H20", "H25_DISP_UP_RESID_20_H20", "H26_DISP_HIGH_LOW_BREADTH_20_H20",
    "H29_PX_AMT_CORR_20_H20",
    "A1_SEASONED_AGE", "A2_RELATIVE_AGE", "A5_MONTH_END_SEASONED", "A6_QUARTER_END_SEASONED",
    "IM5_GVZ_IND_DEF_60", "IM6_GVZ_IND_DEF_120",
]
ANCHORS = ["H11_VOL_60", "H12_VOL_120", "X1_HS300_SET"]

FILES = {}
for h in BEAT_EW[:7]:
    FILES[h] = (os.path.join(RE, "cn_a_share_alpha_v2", "TRADES", h + ".csv"), "capital_ret")
for h in BEAT_EW[7:11]:
    FILES[h] = (os.path.join(RE, "cn_a_share_altinfo_v18", "TRADES", h + ".csv"), "capital_ret")
for h in BEAT_EW[11:]:
    FILES[h] = (os.path.join(RE, "cn_a_share_indmacro_v19", "TRADES", h + ".csv"), "capital_ret")
FILES["H11_VOL_60"] = (os.path.join(RE, "cn_a_share_strategy_v14", "H11", "TRADES.csv"), "ret")
FILES["H12_VOL_120"] = (os.path.join(RE, "cn_a_share_strategy_v14", "H12", "TRADES.csv"), "ret")
FILES["X1_HS300_SET"] = (os.path.join(RE, "cn_a_share_index_v20", "TRADES", "X1_HS300_SET.csv"), "capital_ret")

VAL_START = "2021-08-25"


def read_series(path, col):
    out = {}
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        hdr = f.readline().strip().split(",")
        ix = {h: i for i, h in enumerate(hdr)}
        for line in f:
            p = line.strip().split(",")
            if len(p) < len(hdr):
                continue
            try:
                out[p[ix["signal_date"]]] = float(p[ix[col]])
            except (KeyError, ValueError):
                continue
    return out


def pearson(xs, ys):
    n = len(xs)
    if n < 8:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    dy = math.sqrt(sum((b - my) ** 2 for b in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def month_key(d):
    return d[:7]


def by_month(series):
    out = {}
    for d, v in series.items():
        out.setdefault(month_key(d), []).append(v)
    return {m: sum(vs) / len(vs) for m, vs in out.items()}


def corr_pair(a, b, mode, window=None):
    if mode == "exact":
        keys = sorted(set(a) & set(b))
    else:
        a = by_month(a)
        b = by_month(b)
        keys = sorted(set(a) & set(b))
    if window == "val":
        keys = [k for k in keys if k >= VAL_START[: len(keys[0])] ] if keys else []
    xs = [a[k] for k in keys]
    ys = [b[k] for k in keys]
    return pearson(xs, ys), len(keys)


def main():
    if not os.path.isdir(AD):
        os.makedirs(AD)
    ids = BEAT_EW + ANCHORS
    series = {}
    missing = []
    for h in ids:
        path, col = FILES[h]
        s = read_series(path, col)
        if s is None or not s:
            missing.append(h)
        else:
            series[h] = s
    present = [h for h in ids if h in series]

    def matrix(mode, window):
        m = {}
        for a in present:
            m[a] = {}
            for b in present:
                if a == b:
                    m[a][b] = {"corr": 1.0, "n": len(series[a])}
                    continue
                c, n = corr_pair(series[a], series[b], mode, window)
                m[a][b] = {"corr": c, "n": n}
        return m

    exact_full = matrix("exact", None)
    month_full = matrix("month", None)
    month_val = matrix("month", "val")

    def summarize(m):
        vs_h11 = {a: m[a].get("H11_VOL_60", {}).get("corr") for a in BEAT_EW if a in m}
        vs_x1 = {a: m[a].get("X1_HS300_SET", {}).get("corr") for a in BEAT_EW if a in m}
        pair_vals = []
        for i, a in enumerate(BEAT_EW):
            for b in BEAT_EW[i + 1:]:
                if a in m and b in m and m[a][b]["corr"] is not None:
                    pair_vals.append(m[a][b]["corr"])
        pair_vals.sort()
        med = None
        if pair_vals:
            k = len(pair_vals) // 2
            med = pair_vals[k] if len(pair_vals) % 2 else (pair_vals[k - 1] + pair_vals[k]) / 2
        h11_vals = [v for v in vs_h11.values() if v is not None]
        return {
            "vs_H11": vs_h11,
            "vs_X1": vs_x1,
            "n_vs_H11_gt_0_9": sum(1 for v in h11_vals if v > 0.9),
            "n_vs_H11_gt_0_8": sum(1 for v in h11_vals if v > 0.8),
            "n_vs_H11_gt_0_7": sum(1 for v in h11_vals if v > 0.7),
            "n_vs_H11_available": len(h11_vals),
            "within13_pair_n": len(pair_vals),
            "within13_pair_median": med,
            "within13_pair_min": pair_vals[0] if pair_vals else None,
            "within13_pair_max": pair_vals[-1] if pair_vals else None,
            "within13_n_gt_0_9": sum(1 for v in pair_vals if v > 0.9),
            "within13_n_gt_0_7": sum(1 for v in pair_vals if v > 0.7),
        }

    s_exact = summarize(exact_full)
    s_month = summarize(month_full)
    s_val = summarize(month_val)

    # crude clustering on month_full: link if corr>0.8
    thr = 0.8
    parent = {h: h for h in present}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a in present:
        for b in present:
            if a < b and month_full[a][b]["corr"] is not None and month_full[a][b]["corr"] > thr:
                parent[find(a)] = find(b)
    clusters = {}
    for h in present:
        clusters.setdefault(find(h), []).append(h)
    cluster_list = sorted(clusters.values(), key=lambda c: -len(c))

    h11_cluster = None
    for c in cluster_list:
        if "H11_VOL_60" in c:
            h11_cluster = c
    n13_with_h11 = len([h for h in (h11_cluster or []) if h in BEAT_EW])

    # verdict
    if s_month["n_vs_H11_gt_0_9"] >= 7:
        shadow = "SAME_LOW_VOL_SHADOW"
    elif s_month["n_vs_H11_gt_0_7"] >= 7 or n13_with_h11 >= 7:
        shadow = "MOSTLY_SAME_SLEEVE_NOT_STRICT_0_9"
    else:
        shadow = "NOT_ONE_SHADOW"

    payload = {
        "id": "POST_V21_BEAT_EW_CLUSTER",
        "read_only": True,
        "ids_13": BEAT_EW,
        "anchors": ANCHORS,
        "missing": missing,
        "series_len": {h: len(series[h]) for h in present},
        "alignment": {
            "exact": "same signal_date",
            "month": "mean capital_ret per YYYY-MM (grids differ by a few days across families)",
            "val": "month alignment, months >= 2021-08",
        },
        "summary_exact": s_exact,
        "summary_month": s_month,
        "summary_month_validation": s_val,
        "clusters_month_gt_0_8": cluster_list,
        "h11_cluster_month_gt_0_8": h11_cluster,
        "n_of_13_in_h11_cluster": n13_with_h11,
        "shadow_verdict": shadow,
        "matrix_month_full": month_full,
        "matrix_exact_full": exact_full,
        "matrix_month_validation": month_val,
    }
    outp = os.path.join(AD, "BEAT_EW_CLUSTER.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", outp)
    print("missing", missing)
    print("exact vs H11", {k: None if v is None else round(v, 3) for k, v in s_exact["vs_H11"].items()})
    print("month vs H11", {k: None if v is None else round(v, 3) for k, v in s_month["vs_H11"].items()})
    print("month vs X1", {k: None if v is None else round(v, 3) for k, v in s_month["vs_X1"].items()})
    print("gt0.9", s_month["n_vs_H11_gt_0_9"], "gt0.8", s_month["n_vs_H11_gt_0_8"], "gt0.7", s_month["n_vs_H11_gt_0_7"])
    print("within13 median", s_month["within13_pair_median"], "min", s_month["within13_pair_min"], "max", s_month["within13_pair_max"])
    print("val vs H11", {k: None if v is None else round(v, 3) for k, v in s_val["vs_H11"].items()})
    print("clusters", cluster_list)
    print("verdict", shadow)


if __name__ == "__main__":
    main()
