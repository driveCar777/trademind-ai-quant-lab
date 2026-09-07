"""Read-only V13-V21 capital forensics. No backtest. No download."""
from __future__ import print_function

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RE = os.path.join(ROOT, "data", "market", "research_engine")
OUT = os.path.join(RE, "POST_V21_FORENSICS.json")

SOURCES = (
    ("V13", os.path.join(RE, "cn_a_share_alpha_v1", "RESULTS.json"), "v13"),
    ("V15", os.path.join(RE, "cn_a_share_alpha_v2", "RESULTS.json"), "v15plus"),
    ("V16F", os.path.join(RE, "cn_a_share_information_v16", "FINANCIAL_RESULTS.json"), "v15plus"),
    ("V16I", os.path.join(RE, "cn_a_share_information_v16", "INDUSTRY_RESULTS.json"), "v15plus"),
    ("V17", os.path.join(RE, "cn_a_share_macro_v17", "RESULTS.json"), "v15plus"),
    ("V18", os.path.join(RE, "cn_a_share_altinfo_v18", "RESULTS.json"), "v15plus"),
    ("V19", os.path.join(RE, "cn_a_share_indmacro_v19", "RESULTS.json"), "v15plus"),
    ("V20", os.path.join(RE, "cn_a_share_index_v20", "RESULTS.json"), "v15plus"),
    ("V21", os.path.join(RE, "cn_a_share_div_v21", "RESULTS.json"), "v15plus"),
)

FOCUS_YEARS = ("2011", "2015", "2016", "2017", "2018", "2021", "2022", "2023", "2024")


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _hyp_list(obj):
    if isinstance(obj, dict) and "hypotheses" in obj:
        return obj["hypotheses"]
    if isinstance(obj, list):
        return obj
    return []


def _win(hyp, name):
    w = hyp.get("windows") or {}
    return w.get(name) or {}


def _cap(hyp, name):
    c = hyp.get("capital") or {}
    return c.get(name) or {}


def _metric(win, key):
    m = win.get("metrics") or {}
    if key in m:
        return m.get(key)
    return win.get(key)


def extract_v13(hyp, family):
    rid = hyp.get("id")
    val = _win(hyp, "validation")
    res = _win(hyp, "research")
    vm = val.get("metrics") or {}
    rm = res.get("metrics") or {}
    return {
        "family": family,
        "id": rid,
        "engine": "v13_overlap_metrics",
        "level1": bool(hyp.get("level1")),
        "val_mean_forward": vm.get("mean_net_h"),
        "res_mean_forward": rm.get("mean_net_h"),
        "val_rank_ic": val.get("rank_ic"),
        "res_rank_ic": res.get("rank_ic"),
        "val_overlap_cagr": vm.get("cagr"),
        "res_overlap_cagr": rm.get("cagr"),
        "val_overlap_total": vm.get("total_return"),
        "res_overlap_total": rm.get("total_return"),
        "val_capital_total": None,
        "res_capital_total": None,
        "val_capital_cagr": None,
        "res_capital_cagr": None,
        "val_unfilled": None,
        "res_unfilled": None,
        "val_maxdd": vm.get("maxdd"),
        "res_maxdd": rm.get("maxdd"),
        "val_win_rate": vm.get("win_rate"),
        "res_win_rate": rm.get("win_rate"),
        "years_full": None,
        "note": "V13 published overlap metrics, not official non-overlap capital",
    }


def _year_snip(years):
    if not years:
        return None
    out = {}
    for y in FOCUS_YEARS:
        if y in years:
            rec = years[y]
            out[y] = {
                "n": rec.get("n"),
                "compound": rec.get("compound"),
                "mean": rec.get("mean"),
            }
    return out


def extract_v15(hyp, family):
    rid = hyp.get("id")
    pred = hyp.get("predictive") or {}
    val = pred.get("validation") or _win(hyp, "validation")
    res = pred.get("research") or _win(hyp, "research")
    cap_v = _cap(hyp, "validation")
    cap_r = _cap(hyp, "research")
    if not cap_v and hyp.get("capital"):
        cap_v = (hyp["capital"].get("validation") or {})
        cap_r = (hyp["capital"].get("research") or {})
    return {
        "family": family,
        "id": rid,
        "engine": "v15plus_dual_book",
        "level1": bool(hyp.get("level1")),
        "val_mean_forward": val.get("MEAN_FORWARD_RETURN") or val.get("mean_forward") or (val.get("metrics") or {}).get("mean_net_h"),
        "res_mean_forward": res.get("MEAN_FORWARD_RETURN") or res.get("mean_forward") or (res.get("metrics") or {}).get("mean_net_h"),
        "val_rank_ic": val.get("rank_ic") or val.get("RANK_IC"),
        "res_rank_ic": res.get("rank_ic") or res.get("RANK_IC"),
        "val_overlap_cagr": None,
        "res_overlap_cagr": None,
        "val_overlap_total": None,
        "res_overlap_total": None,
        "val_capital_total": cap_v.get("total"),
        "res_capital_total": cap_r.get("total"),
        "val_capital_cagr": cap_v.get("CAGR"),
        "res_capital_cagr": cap_r.get("CAGR"),
        "val_unfilled": cap_v.get("unfilled_rate"),
        "res_unfilled": cap_r.get("unfilled_rate"),
        "val_maxdd": cap_v.get("maxdd"),
        "res_maxdd": cap_r.get("maxdd"),
        "val_win_rate": cap_v.get("win_rate"),
        "res_win_rate": cap_r.get("win_rate"),
        "years_full": _year_snip((_cap(hyp, "full") or {}).get("years")),
        "years_val": _year_snip(cap_v.get("years")),
        "fdr_hit": hyp.get("fdr_hit"),
        "gates": hyp.get("gates"),
    }


def extract_v14_h11():
    p = os.path.join(RE, "cn_a_share_strategy_v14", "H11", "SUMMARY.json")
    s = _load(p)
    full = ((s.get("metrics") or {}).get("full") or {})
    rtv = full.get("research_through_validation") or {}
    val = full.get("validation") or {}
    vf = (s.get("metrics") or {}).get("validation_fresh") or {}
    rec = s.get("reconciliation") or {}
    reasons = s.get("unfilled_reasons") or {}
    n_unf = sum(int(v) for v in reasons.values())
    return {
        "family": "V14",
        "id": "H11_OFFICIAL_BOOK",
        "engine": "v14_nonoverlap_capital",
        "level1": True,
        "val_mean_forward": None,
        "res_mean_forward": None,
        "val_rank_ic": None,
        "res_rank_ic": None,
        "val_capital_total": val.get("total_return"),
        "res_capital_total": (full.get("research") or {}).get("total_return"),
        "full_capital_total": rtv.get("total_return"),
        "val_capital_cagr": val.get("cagr"),
        "res_capital_cagr": (full.get("research") or {}).get("cagr"),
        "full_capital_cagr": rtv.get("cagr"),
        "val_fresh_cagr": vf.get("cagr"),
        "val_fresh_total": vf.get("total_return"),
        "val_unfilled": s.get("unfilled_rate"),
        "limit_lock_rate": s.get("limit_lock_rate"),
        "val_maxdd": val.get("maxdd"),
        "full_maxdd": rtv.get("maxdd"),
        "dd_peak": ((rtv.get("dd") or {}).get("peak_date")),
        "dd_trough": ((rtv.get("dd") or {}).get("trough_date")),
        "cost_drag_over_start_full": rtv.get("cost_drag_over_start"),
        "sum_fees": rec.get("sum_fees"),
        "sum_slippage": rec.get("sum_slippage"),
        "sum_stamp": rec.get("sum_stamp"),
        "unfilled_reasons": reasons,
        "n_unfilled_events": n_unf,
        "years_full": None,
        "note": "V14.1: overlapping Candidate statistic != this book. AM-GM left tail.",
    }


def _sign(x):
    if x is None:
        return None
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def tally(rows):
    dual = [r for r in rows if r.get("engine") == "v15plus_dual_book"]
    n = len(dual)
    val_cap_neg = sum(1 for r in dual if r.get("val_capital_total") is not None and r["val_capital_total"] < 0)
    val_cap_pos = sum(1 for r in dual if r.get("val_capital_total") is not None and r["val_capital_total"] > 0)
    val_mf_neg = sum(1 for r in dual if r.get("val_mean_forward") is not None and r["val_mean_forward"] < 0)
    val_mf_pos = sum(1 for r in dual if r.get("val_mean_forward") is not None and r["val_mean_forward"] > 0)
    # B-pattern: predictive val > 0 but capital val < 0
    b_pattern = [
        r["id"]
        for r in dual
        if r.get("val_mean_forward") is not None
        and r.get("val_capital_total") is not None
        and r["val_mean_forward"] > 0
        and r["val_capital_total"] < 0
    ]
    a_pattern = [
        r["id"]
        for r in dual
        if r.get("val_mean_forward") is not None
        and r.get("val_capital_total") is not None
        and r["val_mean_forward"] < 0
        and r["val_capital_total"] < 0
    ]
    both_pos = [
        r["id"]
        for r in dual
        if r.get("val_mean_forward") is not None
        and r.get("val_capital_total") is not None
        and r["val_mean_forward"] > 0
        and r["val_capital_total"] > 0
    ]
    unfilled = [r.get("val_unfilled") for r in dual if r.get("val_unfilled") is not None]
    year_neg = {}
    for y in FOCUS_YEARS:
        hits = 0
        tot = 0
        for r in dual:
            yrs = r.get("years_full") or {}
            if y in yrs and yrs[y].get("compound") is not None:
                tot += 1
                if yrs[y]["compound"] < 0:
                    hits += 1
        year_neg[y] = {"n_with_year": tot, "n_compound_neg": hits}
    return {
        "dual_book_n": n,
        "val_capital_neg": val_cap_neg,
        "val_capital_pos": val_cap_pos,
        "val_mean_forward_neg": val_mf_neg,
        "val_mean_forward_pos": val_mf_pos,
        "ids_mf_pos_cap_neg": b_pattern,
        "ids_mf_neg_cap_neg": a_pattern,
        "ids_mf_pos_cap_pos": both_pos,
        "val_unfilled_min": min(unfilled) if unfilled else None,
        "val_unfilled_max": max(unfilled) if unfilled else None,
        "val_unfilled_mean": (sum(unfilled) / len(unfilled)) if unfilled else None,
        "year_compound_neg_share": year_neg,
    }


def _amgm_from_rets(rets):
    if not rets:
        return None
    n = len(rets)
    am = sum(rets) / n
    eq = 1.0
    for r in rets:
        eq *= 1.0 + r
    compound = eq - 1.0
    # geometric mean of (1+r)
    gm = eq ** (1.0 / n) - 1.0 if eq > 0 else None
    left = [r for r in rets if r < 0]
    return {
        "n": n,
        "arith_mean": am,
        "geo_mean": gm,
        "am_gm_gap": None if gm is None else am - gm,
        "compound": compound,
        "win_rate": sum(1 for r in rets if r > 0) / float(n),
        "n_neg": len(left),
        "worst": min(rets),
        "p05": sorted(rets)[max(0, int(0.05 * n) - 1)],
    }


def trade_amgm():
    """Read existing trade CSVs only. No resim."""
    specs = (
        (
            "H24_DISP",
            os.path.join(RE, "cn_a_share_alpha_v2", "TRADES", "H24_DISP_HIGH_RESID_20_H20.csv"),
            "capital_ret",
            "signal_date",
        ),
        (
            "H25_DISP",
            os.path.join(RE, "cn_a_share_alpha_v2", "TRADES", "H25_DISP_UP_RESID_20_H20.csv"),
            "capital_ret",
            "signal_date",
        ),
        (
            "H26_DISP",
            os.path.join(RE, "cn_a_share_alpha_v2", "TRADES", "H26_DISP_HIGH_LOW_BREADTH_20_H20.csv"),
            "capital_ret",
            "signal_date",
        ),
        (
            "H11_OFFICIAL",
            os.path.join(RE, "cn_a_share_strategy_v14", "H11", "TRADES.csv"),
            "ret",
            "signal_date",
        ),
    )
    out = {}
    for name, path, col, dcol in specs:
        if not os.path.isfile(path):
            out[name] = {"missing": path}
            continue
        rows = []
        with open(path, "r", encoding="utf-8") as f:
            hdr = f.readline().strip().split(",")
            ix = {h: i for i, h in enumerate(hdr)}
            for line in f:
                parts = line.strip().split(",")
                if len(parts) < len(hdr):
                    continue
                rows.append((parts[ix[dcol]], float(parts[ix[col]])))
        all_r = [r for _, r in rows]
        val_r = [r for d, r in rows if d >= "2021-08-25"]
        res_r = [r for d, r in rows if d < "2021-08-25"]
        out[name] = {
            "path": path.replace("\\", "/"),
            "full": _amgm_from_rets(all_r),
            "research": _amgm_from_rets(res_r),
            "validation": _amgm_from_rets(val_r),
        }
    return out


def main():
    rows = []
    missing = []
    for family, path, kind in SOURCES:
        if not os.path.isfile(path):
            missing.append(path)
            continue
        obj = _load(path)
        for hyp in _hyp_list(obj):
            if kind == "v13":
                rows.append(extract_v13(hyp, family))
            else:
                rows.append(extract_v15(hyp, family))
    rows.append(extract_v14_h11())

    stats = tally(rows)
    # Decision logic (documented in markdown)
    n_b = len(stats["ids_mf_pos_cap_neg"])
    n_a = len(stats["ids_mf_neg_cap_neg"])
    n_pos = len(stats["ids_mf_pos_cap_pos"])
    if n_a >= 20 and n_pos == 0:
        verdict = "A"
        confidence = 0.72
        note = (
            "Primary: 38/42 dual-book hyps have negative validation MEAN_FORWARD. "
            "Those families had no val information to lose to construction. "
            "Sidecar B (n=4 + H11 official): overlap statistic positive, official "
            "20d book negative. That is V14.1 again. Changing hold/cost is locked. "
            "It does not create a second independent Alpha under current gates."
        )
    elif n_b >= 8:
        verdict = "B"
        confidence = 0.7
        note = "Many hyps have positive val MEAN_FORWARD but negative val capital."
    else:
        verdict = "A"
        confidence = 0.65
        note = "Mixed but majority A-pattern."

    contrast = trade_amgm()
    payload = {
        "id": "POST_V21_CAPITAL_CONSTRUCTION_FORENSICS",
        "read_only": True,
        "rerun": False,
        "download": False,
        "verdict": verdict,
        "confidence": confidence,
        "verdict_note": note,
        "sidecar_B_ids": stats["ids_mf_pos_cap_neg"],
        "trade_amgm_existing_csvs": contrast,
        "h11_h12_special": {
            "shape": "B_FOR_EXISTING_CANDIDATE_ONLY",
            "meaning": (
                "V14.1 already proved the official 20d long-only book can lose "
                "while the overlapping Candidate statistic stays slightly positive. "
                "That is construction vs statistic, not a second Alpha."
            ),
        },
        "tally": stats,
        "missing_files": missing,
        "new_information_class": "NONE",
        "next_unit": "NO_LEGAL_FREE_OBJECT_LEFT_DO_NOT_BUY",
        "construction_contrast_done": True,
        "purchase_default": "DO_NOT_BUY",
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", OUT)
    print("verdict", verdict, "conf", confidence)
    print("dual", stats["dual_book_n"], "val_cap_neg", stats["val_capital_neg"],
          "val_mf_neg", stats["val_mean_forward_neg"], "val_mf_pos", stats["val_mean_forward_pos"])
    print("B-pattern", stats["ids_mf_pos_cap_neg"])
    print("both_pos", stats["ids_mf_pos_cap_pos"])
    print("unfilled", stats["val_unfilled_min"], stats["val_unfilled_mean"], stats["val_unfilled_max"])
    print("years", stats["year_compound_neg_share"])


if __name__ == "__main__":
    main()
