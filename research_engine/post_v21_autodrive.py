"""Read-only Q1/Q2/Q4. No download. No BaoStock. No resim."""
from __future__ import print_function

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RE = os.path.join(ROOT, "data", "market", "research_engine")
AD = os.path.join(RE, "POST_V21_AUTODRIVE")
FOCUS = ("2011", "2015", "2016", "2017", "2018", "2021", "2022", "2023", "2024")

SOURCES = (
    ("V15", os.path.join(RE, "cn_a_share_alpha_v2", "RESULTS.json")),
    ("V16F", os.path.join(RE, "cn_a_share_information_v16", "FINANCIAL_RESULTS.json")),
    ("V16I", os.path.join(RE, "cn_a_share_information_v16", "INDUSTRY_RESULTS.json")),
    ("V17", os.path.join(RE, "cn_a_share_macro_v17", "RESULTS.json")),
    ("V18", os.path.join(RE, "cn_a_share_altinfo_v18", "RESULTS.json")),
    ("V19", os.path.join(RE, "cn_a_share_indmacro_v19", "RESULTS.json")),
    ("V20", os.path.join(RE, "cn_a_share_index_v20", "RESULTS.json")),
    ("V21", os.path.join(RE, "cn_a_share_div_v21", "RESULTS.json")),
)


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _hyps(obj):
    if isinstance(obj, dict):
        return obj.get("hypotheses") or []
    return obj if isinstance(obj, list) else []


def _row(family, hyp):
    pred = hyp.get("predictive") or {}
    val = pred.get("validation") or {}
    res = pred.get("research") or {}
    cap = hyp.get("capital") or {}
    cap_v = cap.get("validation") or {}
    cap_f = cap.get("full") or {}
    years = (cap_f.get("years") or {})
    y = {}
    for k in FOCUS:
        rec = years.get(k) or {}
        y[k] = rec.get("compound")
    return {
        "family": family,
        "id": hyp.get("id"),
        "val_mf": val.get("MEAN_FORWARD_RETURN"),
        "val_excess_vs_b0": val.get("excess_vs_b0"),
        "res_excess_vs_b0": res.get("excess_vs_b0"),
        "val_capital": cap_v.get("total"),
        "val_cagr": cap_v.get("CAGR"),
        "years": y,
    }


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    dy = math.sqrt(sum((b - my) ** 2 for b in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def q1_q4():
    rows = []
    x1 = None
    for family, path in SOURCES:
        if not os.path.isfile(path):
            continue
        for hyp in _hyps(_load(path)):
            r = _row(family, hyp)
            rows.append(r)
            if r["id"] == "X1_HS300_SET":
                x1 = r
    n = len(rows)
    ex = [r["val_excess_vs_b0"] for r in rows if r["val_excess_vs_b0"] is not None]
    ex_pos = [r["id"] for r in rows if r.get("val_excess_vs_b0") is not None and r["val_excess_vs_b0"] > 0]
    ex_neg = [r["id"] for r in rows if r.get("val_excess_vs_b0") is not None and r["val_excess_vs_b0"] < 0]
    # selection worse than EW AND lost money
    worse = [r["id"] for r in rows if (r.get("val_excess_vs_b0") or 0) < 0 and (r.get("val_capital") or 0) < 0]
    beat_ew_lost = [r["id"] for r in rows if (r.get("val_excess_vs_b0") or 0) > 0 and (r.get("val_capital") or 0) < 0]
    year_sign = {}
    x1y = (x1 or {}).get("years") or {}
    for y in FOCUS:
        n_neg = sum(1 for r in rows if r["years"].get(y) is not None and r["years"][y] < 0)
        n_has = sum(1 for r in rows if r["years"].get(y) is not None)
        agree_x1 = None
        if x1y.get(y) is not None:
            sign = 1 if x1y[y] > 0 else (-1 if x1y[y] < 0 else 0)
            agree = 0
            tot = 0
            for r in rows:
                v = r["years"].get(y)
                if v is None:
                    continue
                tot += 1
                s = 1 if v > 0 else (-1 if v < 0 else 0)
                if s == sign:
                    agree += 1
            agree_x1 = {"n": tot, "same_sign_as_x1": agree, "x1_compound": x1y[y]}
        year_sign[y] = {"n": n_has, "n_neg": n_neg, "x1": agree_x1}
    corrs = []
    if x1:
        for r in rows:
            if r["id"] == "X1_HS300_SET":
                continue
            xs, ys = [], []
            for y in FOCUS:
                a, b = r["years"].get(y), x1y.get(y)
                if a is not None and b is not None:
                    xs.append(a)
                    ys.append(b)
            c = _pearson(xs, ys)
            if c is not None:
                corrs.append({"id": r["id"], "corr_vs_x1_years": c})
    corrs_s = sorted(corrs, key=lambda d: d["corr_vs_x1_years"])
    median_corr = None
    if corrs_s:
        mid = len(corrs_s) // 2
        median_corr = corrs_s[mid]["corr_vs_x1_years"] if len(corrs_s) % 2 else (
            corrs_s[mid - 1]["corr_vs_x1_years"] + corrs_s[mid]["corr_vs_x1_years"]
        ) / 2.0
    mean_ex = sum(ex) / len(ex) if ex else None
    q1_rel_ew = "NEGATIVE" if (len(ex_neg) > len(ex_pos)) else "POSITIVE"
    return {
        "n": n,
        "val_excess_pos": len(ex_pos),
        "val_excess_neg": len(ex_neg),
        "val_excess_pos_ids": ex_pos,
        "val_excess_neg_ids": ex_neg,
        "mean_val_excess_vs_b0": mean_ex,
        "beat_ew_but_lost_capital": beat_ew_lost,
        "worse_than_ew_and_lost": worse,
        "q1_relative_ew": q1_rel_ew,
        "x1": {
            "id": "X1_HS300_SET",
            "val_mf": (x1 or {}).get("val_mf"),
            "val_excess_vs_b0": (x1 or {}).get("val_excess_vs_b0"),
            "val_capital": (x1 or {}).get("val_capital"),
            "years": x1y,
        },
        "year_vs_x1": year_sign,
        "year_corr_vs_x1": {
            "n": len(corrs_s),
            "median": median_corr,
            "min": corrs_s[0] if corrs_s else None,
            "max": corrs_s[-1] if corrs_s else None,
            "n_corr_gt_0_7": sum(1 for c in corrs_s if c["corr_vs_x1_years"] > 0.7),
            "n_corr_gt_0_5": sum(1 for c in corrs_s if c["corr_vs_x1_years"] > 0.5),
        },
        "rows": rows,
    }


def q2_inventory():
    base = os.path.join(ROOT, "data", "market", "cn_a_share")
    items = [
        {
            "object": "EQUITY_D1_PANEL",
            "path": "normalized/ + manifests/tm-ashare-EQUITY-D1-20260830-000002",
            "mechanism": "Daily OHLCV / amount. Knowledge = bar date.",
            "pit": "YES (panel freeze V12.2)",
            "v13_v21_wrapper": "YES — every CS family ranks on this book",
            "status": "ALREADY_TESTED",
        },
        {
            "object": "UNIVERSE_HISTORY / BASIC / CALENDAR",
            "path": "reference/",
            "mechanism": "Listing, ST, trade status, session calendar.",
            "pit": "YES (as-of listing)",
            "v13_v21_wrapper": "YES — V18 altinfo + eligibility mask",
            "status": "ALREADY_TESTED",
        },
        {
            "object": "FINANCIAL_ANNUAL_PIT",
            "path": "financial/",
            "mechanism": "Annual statements visible after announce_date.",
            "pit": "YES V16 (RESTATEMENT_RISK)",
            "v13_v21_wrapper": "YES — V16 F1–F6",
            "status": "ALREADY_TESTED",
        },
        {
            "object": "INDUSTRY_MONTHLY_ASOF",
            "path": "industry/",
            "mechanism": "Industry membership as-of month.",
            "pit": "YES V16/V19",
            "v13_v21_wrapper": "YES — I1–I3 and IM1–IM6",
            "status": "ALREADY_TESTED",
        },
        {
            "object": "INDEX_MEMBERSHIP_HS300_ZZ500",
            "path": "index/",
            "mechanism": "Monthly as-of members / add-drop.",
            "pit": "YES V20",
            "v13_v21_wrapper": "YES — X1–X4",
            "status": "ALREADY_TESTED",
        },
        {
            "object": "DIVIDEND_EVENTS",
            "path": "dividend/",
            "mechanism": "Cash/stock plan. Knowledge = announce_date.",
            "pit": "YES V21",
            "v13_v21_wrapper": "YES — D1/D2",
            "status": "ALREADY_TESTED",
        },
        {
            "object": "ANNOUNCEMENTS_FORECAST_EXPRESS",
            "path": "announcements/ (.gitkeep empty)",
            "mechanism": "Filing then 20d long — same object as V21.",
            "pit": "WOULD BE, if downloaded",
            "v13_v21_wrapper": "YES — same announcement window",
            "status": "LOW_VALUE",
        },
        {
            "object": "CORPORATE_ACTIONS_SAMPLE",
            "path": "corporate_actions/",
            "mechanism": "Split/dividend representation. Not a signal class.",
            "pit": "SAMPLE ONLY",
            "v13_v21_wrapper": "Used as limitation (DIVIDEND_EXCLUSION), not alpha",
            "status": "LOW_VALUE",
        },
        {
            "object": "QUARTERLY_RATIOS / LEVERAGE",
            "path": "financial/ (same API, quarterly)",
            "mechanism": "Slow accounting characteristic, sibling of V16 annual.",
            "pit": "Possible",
            "v13_v21_wrapper": "YES — V16 family twin. Locked: do not open.",
            "status": "LOW_VALUE",
        },
        {
            "object": "DIVIDEND_YIELD_LEVEL",
            "path": "dividend/ + price",
            "mechanism": "Yield quintile ≈ quality/size neighborhood of V16+V20.",
            "pit": "YES",
            "v13_v21_wrapper": "YES — classified LOW_VALUE after V16+V20",
            "status": "LOW_VALUE",
        },
        {
            "object": "MACRO_FROZEN_EURUSD_US500_GVZ",
            "path": "not under cn_a_share; frozen MT5 series",
            "mechanism": "External driver × A-share CS or industry.",
            "pit": "YES as published print",
            "v13_v21_wrapper": "YES — V17/V19",
            "status": "ALREADY_TESTED",
        },
        {
            "object": "TUSHARE_WIND_CHOICE_CSMAR",
            "path": "not on disk",
            "mechanism": "Vendor fundamentals / news / holders.",
            "pit": "unknown until paid",
            "v13_v21_wrapper": "PAYMENT",
            "status": "PAYMENT_REQUIRED",
        },
        {
            "object": "OPTIONS_LO_OG_MVD",
            "path": "not on disk",
            "mechanism": "IV/skew/term on 4-name CFD book.",
            "pit": "vendor",
            "v13_v21_wrapper": "Different universe; V9/V10 already dead on those names",
            "status": "PAYMENT_REQUIRED",
        },
    ]
    present = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            present.append(name)
    new_legal = [x for x in items if x["status"] == "AVAILABLE"]
    return {
        "disk_top": present,
        "source_matrix": "data/market/cn_a_share/A_SHARE_SOURCE_MATRIX_V12.json",
        "canonical": "BAOSTOCK",
        "items": items,
        "new_legal_objects": new_legal,
        "new_information_class": "NONE" if not new_legal else "SEE_ITEMS",
    }


def main():
    if not os.path.isdir(AD):
        os.makedirs(AD)
    q1 = q1_q4()
    q2 = q2_inventory()
    # confidence: Q1+Q2 complete with hard counts
    if q1["val_excess_neg"] >= 30 and q2["new_information_class"] == "NONE":
        conf = 0.91
        path = "Q4_THEN_Q5_S1_LIKELY"
    elif q1["val_excess_pos"] >= 20 and q2["new_information_class"] == "NONE":
        conf = 0.88
        path = "Q4_Q5_DIAGNOSTIC_THEN_CLOSE"
    else:
        conf = 0.86
        path = "Q4_THEN_Q5"
    # H24 offsets
    trades = os.path.join(RE, "cn_a_share_alpha_v2", "TRADES")
    offsets = []
    if os.path.isdir(trades):
        offsets = [n for n in os.listdir(trades) if "OFFSET" in n.upper() or "offset" in n]
    payload = {
        "q1": q1,
        "q2": {
            "disk_top": q2["disk_top"],
            "canonical": q2["canonical"],
            "new_information_class": q2["new_information_class"],
            "n_items": len(q2["items"]),
            "n_available": len(q2["new_legal_objects"]),
        },
        "q2_full": q2,
        "h24_offset_files": offsets,
        "h24_offset_status": "MISSING_DO_NOT_RERUN",
        "confidence": conf,
        "next_item": "Q4",
        "skip_q3": True,
        "skip_q3_reason": "NONE after inventory",
    }
    outp = os.path.join(AD, "Q1_Q2.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    prog = {
        "stage": "Q1_Q2_DONE",
        "last_decision": (
            "Q1 relative EW is %s (%d pos / %d neg val excess_vs_b0). "
            "Q2 new class NONE. Skip Q3. Next Q4."
            % (q1["q1_relative_ew"], q1["val_excess_pos"], q1["val_excess_neg"])
        ),
        "next_item": "Q4",
        "confidence": conf,
        "hours_note": "read-only JSON + disk listing, no download",
        "blocked_only_if_human_gate": False,
        "q1_relative_ew": q1["q1_relative_ew"],
        "new_information_class": "NONE",
    }
    with open(os.path.join(AD, "PROGRESS.json"), "w", encoding="utf-8") as f:
        json.dump(prog, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", outp)
    print("rel_ew", q1["q1_relative_ew"], "ex+", q1["val_excess_pos"], "ex-", q1["val_excess_neg"])
    print("mean_ex", q1["mean_val_excess_vs_b0"])
    print("beat_ew_lost", len(q1["beat_ew_but_lost_capital"]), q1["beat_ew_but_lost_capital"])
    print("corr_median", q1["year_corr_vs_x1"]["median"], "gt0.7", q1["year_corr_vs_x1"]["n_corr_gt_0_7"])
    print("x1 years", {k: x1y for k, x1y in q1["x1"]["years"].items() if k in ("2011", "2015", "2018", "2023")})
    print("conf", conf)


if __name__ == "__main__":
    main()
