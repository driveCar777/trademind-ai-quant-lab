"""Append V22+ decisions to the failure atlas (JSON + MD). Idempotent by id."""
from __future__ import print_function

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ATLAS = os.path.join(ROOT, "data", "market", "research_engine", "POST_V21_AUTODRIVE", "FAILURE_ATLAS.json")
MD = os.path.join(ROOT, "docs", "research_engine", "POST_V21_FAILURE_ATLAS.md")
RE = os.path.join(ROOT, "data", "market", "research_engine")


def _load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def rows_v22():
    r = _load(os.path.join(RE, "futures_xs_v22", "RESULTS.json"))
    out = []
    for h in r["hypotheses"]:
        out.append({
            "id": h["id"], "version": "V22", "universe": "CME futures 30 roots", "mechanism": h["id"].split("_", 1)[1],
            "family": "FUTURES_XS", "val_mean_forward": None, "val_capital": h["validation"]["capital"].get("total"),
            "val_capital_sign": "POS" if (h["validation"]["capital"].get("total") or 0) > 0 else "NEG",
            "beat_ew": None, "corr_vs_h11_month": h.get("corr_vs_h11_month"), "fdr_discovery": h["fdr_discovery"],
            "level1": h["level1"], "frozen": True, "decision": "FUTURES_XS_V1_NO_CANDIDATE",
            "research_capital": h["research"]["capital"].get("total"),
            "why_not_next": "Research 2010-2021 flat before cost (gross CAGR ~1%); no FDR discovery; validation tail not promoted. Do not retune / buy OI.",
        })
    return out


def rows_family(sub, version, universe, family, decision, corr_month, why):
    r = _load(os.path.join(RE, sub, "RESULTS.json"))
    out = []
    for h in r["hypotheses"]:
        pv = h["predictive"]["validation"]
        cv = h["capital"]["validation"]
        out.append({
            "id": h["id"], "version": version, "universe": universe, "mechanism": h.get("mechanism", "")[:90],
            "family": h.get("family", family), "val_mean_forward": pv.get("MEAN_FORWARD_RETURN"), "val_capital": cv.get("total"),
            "val_capital_sign": "POS" if (cv.get("total") or 0) > 0 else "NEG",
            "beat_ew": (pv.get("excess_vs_b0") or 0) > 0, "corr_vs_h11_month": corr_month.get(h["id"]),
            "fdr_discovery": h.get("fdr_discovery"), "level1": h.get("level1"), "frozen": True, "decision": decision,
            "research_capital": h["capital"]["research"].get("total"),
            "why_not_next": why.get(h["id"], why.get("*", "")),
        })
    return out


def main():
    atlas = _load(ATLAS)
    new = rows_v22()
    new += rows_family("cn_a_share_margin_v23", "V23", "A-share marginable", "MARGIN", "A_SHARE_MARGIN_POSITIONING_V1_NO_CANDIDATE",
                       {"M1_LOW_NET_MARGIN_INFLOW_20": 0.781, "M2_LOW_MARGIN_BALANCE_RATIO": 0.346, "M3_MARGIN_DELEVERAGED_60": 0.33},
                       {"M1_LOW_NET_MARGIN_INFLOW_20": "Research excess t=4.85 and capital +37%, but validation capital -19% and excess t=0.92; no FDR. Different failure shape (research-real, validation-flat). Do not retune or filter.",
                        "*": "Validation capital negative; validation excess <= 0."})
    v24 = os.path.join(RE, "cn_a_share_holders_v24", "RESULTS.json")
    if os.path.isfile(v24):
        corr = {}
        cpath = os.path.join(RE, "cn_a_share_holders_v24", "CORR_MONTH.json")
        if os.path.isfile(cpath):
            corr = _load(cpath)
        new += rows_family("cn_a_share_holders_v24", "V24", "A-share", "HOLDER_CONCENTRATION", _load(os.path.join(RE, "cn_a_share_holders_v24", "DECISION.json"))["OVERALL"],
                           corr, {"*": "See V24_HOLDERS_DECISION.md"})
    v25 = os.path.join(RE, "cn_a_share_ml_v25", "RESULTS.json")
    if os.path.isfile(v25):
        r25 = _load(v25)
        d25 = _load(os.path.join(RE, "cn_a_share_ml_v25", "V25_1_DECISION.json")) if os.path.isfile(os.path.join(RE, "cn_a_share_ml_v25", "V25_1_DECISION.json")) else {}
        why25 = {"ML1_LGBM_STACK": "LEVEL-1 PASS; 7/7 reproduction; excess-corr vs H11 0.06 -> INDEPENDENT under A4. Frozen. Next = strategy spec + human Final OOS decision. Not a failure row.",
                 "ML0_RANK_AVERAGE": "Beats EW (t 7.6 validation) but research HN20 capital negative; no-fit baseline; shows combination alone is not enough, fitted nonlinearity is."}
        for h in r25["hypotheses"]:
            pv, cv = h["predictive"]["validation"], h["capital_LO20"]["validation"]
            new.append({
                "id": h["id"], "version": "V25", "universe": "A-share eligible", "mechanism": h.get("mechanism", "")[:90], "family": h.get("family"),
                "val_mean_forward": pv.get("MEAN_FORWARD_RETURN"), "val_capital": cv.get("total"),
                "val_capital_sign": "POS" if (cv.get("total") or 0) > 0 else "NEG",
                "beat_ew": (pv.get("excess_vs_b0") or 0) > 0, "corr_vs_h11_month": None,
                "excess_corr_vs_h11": 0.063 if h["id"] == "ML1_LGBM_STACK" else None,
                "fdr_discovery": h.get("fdr_discovery"), "level1": h.get("level1"), "frozen": True,
                "decision": d25.get("OVERALL", "A_SHARE_MULTILAYER_MODEL_V1") if h["id"] == "ML1_LGBM_STACK" else "V25_BASELINE_NOT_LEVEL1",
                "research_capital": h["capital_LO20"]["research"].get("total"), "why_not_next": why25.get(h["id"], ""),
            })
    v27 = os.path.join(RE, "cn_a_share_findeep_v27", "RESULTS.json")
    if os.path.isfile(v27):
        r27 = _load(v27)
        d27 = _load(os.path.join(RE, "cn_a_share_findeep_v27", "DECISION.json"))
        why27 = {"ML2F_LGBM_FINDEEP_ONLY": "Quarterly-filings-only model: excess vs EW +0.65%/20d research, +0.52% validation (t 5.6), rolling 5/5, FDR Y, excess-corr vs ML1 0.06 (independent) -- but LO20 validation capital -0.3% (flat, bear market) -> NOT Level-1. Weak independent predictive edge with no positive book. HN20 val +12% already SEEN: no post-hoc HN20 contract for this signal. Frozen.",
                 "ML2_LGBM_FULL_STACK": "ML1 14 + 10 quarterly features: Level-1 but excess-corr vs ML1 0.96 = SAME_CLUSTER (pre-declared). Validation excess 1.42% vs ML1 1.47%, LO20 +28.0% vs +30.9%: quarterly layer adds nothing on top of ML1. ML1 unchanged."}
        for h in r27["hypotheses"]:
            pv, cv = h["predictive"]["validation"], h["capital_LO20"]["validation"]
            new.append({
                "id": h["id"], "version": "V27", "universe": "A-share eligible", "mechanism": h.get("mechanism", "")[:90], "family": h.get("family"),
                "val_mean_forward": pv.get("MEAN_FORWARD_RETURN"), "val_capital": cv.get("total"),
                "val_capital_sign": "POS" if (cv.get("total") or 0) > 0 else "NEG",
                "beat_ew": (pv.get("excess_vs_b0") or 0) > 0, "corr_vs_h11_month": None,
                "excess_corr_vs_h11": (h.get("excess_corr") or {}).get("H11_VOL_60", {}).get("excess_corr"),
                "excess_corr_vs_ml1": (h.get("excess_corr") or {}).get("ML1_LGBM_STACK", {}).get("excess_corr"),
                "fdr_discovery": h.get("fdr_discovery"), "level1": h.get("level1"), "frozen": True,
                "decision": d27.get("OVERALL"), "research_capital": h["capital_LO20"]["research"].get("total"), "why_not_next": why27.get(h["id"], ""),
            })
    ids = set(r["id"] for r in atlas["rows"])
    added = [r for r in new if r["id"] not in ids]
    atlas["rows"] = [r for r in atlas["rows"] if r["id"] not in set(x["id"] for x in new)] + new
    atlas["span"] = "V8-V27"
    atlas["n_rows"] = len(atlas["rows"])
    atlas["n_val_capital_neg"] = sum(1 for r in atlas["rows"] if str(r.get("val_capital_sign", "")).startswith("NEG"))
    with open(ATLAS, "w", encoding="utf-8") as f:
        json.dump(atlas, f, indent=1, ensure_ascii=False)
    # MD append
    with open(MD, "r", encoding="utf-8") as f:
        md = f.read()
    marker = "## Use"
    block = ["\n### Appended after S1 (V22-V27; V25 ML1 is the first Level-1 row — not a failure)\n", "| id | ver | universe | val MF | val cap | beat EW | corr H11 (month) | FDR | why not next |", "|---|---|---|---|---|---|---|---|---|"]
    for r in new:
        mf = "—" if r["val_mean_forward"] is None else "%.2f%%" % (100 * r["val_mean_forward"])
        cap = "—" if r["val_capital"] is None else "%.1f%%" % (100 * r["val_capital"])
        be = "—" if r["beat_ew"] is None else ("Y" if r["beat_ew"] else "N")
        c = "—" if r["corr_vs_h11_month"] is None else "%.2f" % r["corr_vs_h11_month"]
        block.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (r["id"], r["version"], r["universe"], mf, cap, be, c, "Y" if r["fdr_discovery"] else "N", r["why_not_next"]))
    block.append("")
    if "### Appended after S1" in md:
        head = md[:md.index("### Appended after S1")].rstrip("\n") + "\n"
        tail = md[md.index(marker):] if marker in md[md.index("### Appended after S1"):] else ""
        md = head + "\n".join(block) + "\n" + tail
    else:
        md = md.replace(marker, "\n".join(block) + "\n" + marker)
    with open(MD, "w", encoding="utf-8") as f:
        f.write(md)
    print("atlas rows", atlas["n_rows"], "added", [r["id"] for r in added])


if __name__ == "__main__":
    sys.exit(main() or 0)
