"""W3: failure atlas V8-V21. Read-only from existing JSON."""
from __future__ import print_function

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RE = os.path.join(ROOT, "data", "market", "research_engine")
AD = os.path.join(RE, "POST_V21_AUTODRIVE")

FOR = os.path.join(RE, "POST_V21_FORENSICS.json")
Q12 = os.path.join(AD, "Q1_Q2.json")
CLU = os.path.join(AD, "BEAT_EW_CLUSTER.json")

RESULT_FILES = {
    "V15": os.path.join(RE, "cn_a_share_alpha_v2", "RESULTS.json"),
    "V16F": os.path.join(RE, "cn_a_share_information_v16", "FINANCIAL_RESULTS.json"),
    "V16I": os.path.join(RE, "cn_a_share_information_v16", "INDUSTRY_RESULTS.json"),
    "V17": os.path.join(RE, "cn_a_share_macro_v17", "RESULTS.json"),
    "V18": os.path.join(RE, "cn_a_share_altinfo_v18", "RESULTS.json"),
    "V19": os.path.join(RE, "cn_a_share_indmacro_v19", "RESULTS.json"),
    "V20": os.path.join(RE, "cn_a_share_index_v20", "RESULTS.json"),
    "V21": os.path.join(RE, "cn_a_share_div_v21", "RESULTS.json"),
    "V13": os.path.join(RE, "cn_a_share_alpha_v1", "RESULTS.json"),
}

PRE_A_SHARE = [
    {"id": "V8_FUSION_TOP5", "version": "V8", "universe": "MT5 4-name CFD + Databento Pack E + public", "mechanism": "Existing-information fusion (OI / volume / DTE / gap / steepening / yield)", "val_capital_sign": "NEG_OR_NONE", "beat_ew": None, "frozen": True, "decision": "STOP C, FDR 0/15", "why_not_next": "All fusion cells failed FDR; options unpaid; do not retune gap/steepening/OI/wow/yield."},
    {"id": "V9_MASTER_REPLAY", "version": "V9", "universe": "MT5 + public + futures (A-J)", "mechanism": "Replay all legal strategy mechanisms on owned data", "val_capital_sign": "NO_REPRODUCIBLE", "beat_ew": None, "frozen": True, "decision": "STOP B", "why_not_next": "Research-positive but no Positive Reproducible Strategy; $31.82 Databento added 0 Candidates."},
    {"id": "V10_MODEL_REPRESENTATION", "version": "V10", "universe": "MT5 GOLD/OIL", "mechanism": "Nonlinear models (FOREST etc.) on owned features", "val_capital_sign": "NEG_OR_NONE", "beat_ew": None, "frozen": True, "decision": "STOP B, FDR 0/62", "why_not_next": "Model did not recover killed rules; OIL-heavy; cost stress flipped greens."},
    {"id": "V11_ALLOCATION_REVIEW", "version": "V11", "universe": "review", "mechanism": "Pick next universe", "val_capital_sign": None, "beat_ew": None, "frozen": True, "decision": "NEXT=CHINA_A_SHARE", "why_not_next": "Executed: V12-V21 followed. MT5 alpha frozen."},
    {"id": "V12_PANEL", "version": "V12/V12.1/V12.2", "universe": "A-share", "mechanism": "PIT daily panel freeze (BaoStock)", "val_capital_sign": None, "beat_ew": None, "frozen": True, "decision": "PRICE_ALPHA_READY", "why_not_next": "Infrastructure, not alpha."},
    {"id": "H11_H12_OFFICIAL_BOOK", "version": "V14/V14.1", "universe": "A-share", "mechanism": "Long low realized vol (60/120d), quintile, 20d non-overlap capital", "val_capital_sign": "NEG (full −15.61%, val cont. −0.06%, val fresh +0.31%)", "beat_ew": "overlap yes; book no", "frozen": True, "decision": "STRATEGY_WEAK / METHODOLOGY_GAP_CONFIRMED", "why_not_next": "MaxDD −66%; AM-GM; one cluster (corr 0.996); KEEP_LOW_PRIORITY; no retune."},
]


def _load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    if not os.path.isdir(AD):
        os.makedirs(AD)
    q12 = _load(Q12)
    clu = _load(CLU)
    ex_pos = set(q12["q1"]["val_excess_pos_ids"])
    vs_h11 = clu["summary_month"]["vs_H11"]
    rows = list(PRE_A_SHARE)
    for ver, path in RESULT_FILES.items():
        if not os.path.isfile(path):
            continue
        obj = _load(path)
        hyps = obj.get("hypotheses") if isinstance(obj, dict) else obj
        for h in hyps or []:
            hid = h.get("id")
            cap = (h.get("capital") or {}).get("validation") or {}
            pred = (h.get("predictive") or {}).get("validation") or {}
            if ver == "V13":
                vm = ((h.get("windows") or {}).get("validation") or {}).get("metrics") or {}
                val_mf = vm.get("mean_net_h")
                val_cap = None
                sign = "V13_OVERLAP_ONLY (%s)" % ("mf>0" if (val_mf or 0) > 0 else "mf<0")
                beat = None
            else:
                val_mf = pred.get("MEAN_FORWARD_RETURN")
                val_cap = cap.get("total")
                sign = "NEG" if (val_cap or 0) < 0 else ("POS" if (val_cap or 0) > 0 else None)
                beat = hid in ex_pos
            level1 = bool(h.get("level1"))
            corr = vs_h11.get(hid)
            why = []
            if level1:
                why.append("Level-1 but one low-vol cluster; official book negative")
            if sign == "NEG":
                why.append("validation capital negative")
            if beat:
                why.append("beat EW on overlap only; still lost")
            if corr is not None and corr > 0.9:
                why.append("corr vs H11 %.2f = same sleeve" % corr)
            if h.get("fdr_discovery") and not level1:
                why.append("FDR hit without capital = not Candidate")
            rows.append({
                "id": hid, "version": ver,
                "universe": "A-share",
                "mechanism": h.get("mechanism") or h.get("family") or h.get("signal"),
                "family": h.get("family"),
                "val_mean_forward": val_mf,
                "val_capital": val_cap,
                "val_capital_sign": sign,
                "beat_ew": beat,
                "corr_vs_h11_month": corr,
                "fdr_discovery": h.get("fdr_discovery"),
                "level1": level1,
                "frozen": True,
                "decision": (obj.get("decision") if isinstance(obj, dict) else None) or "STOP_B_FAMILY",
                "why_not_next": "; ".join(why) or "frozen family; no val edge",
            })
    n = len(rows)
    n_neg = sum(1 for r in rows if r.get("val_capital_sign") == "NEG")
    n_beat = sum(1 for r in rows if r.get("beat_ew") is True)
    payload = {
        "id": "POST_V21_FAILURE_ATLAS",
        "read_only": True,
        "span": "V8-V21",
        "n_rows": n,
        "n_val_capital_neg": n_neg,
        "n_beat_ew_overlap": n_beat,
        "n_level1": sum(1 for r in rows if r.get("level1")),
        "new_independent": 0,
        "rows": rows,
    }
    outp = os.path.join(AD, "FAILURE_ATLAS.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", outp, "rows", n, "neg", n_neg, "beat", n_beat)
    # markdown table
    lines = [
        "# Post-V21 Failure Atlas — W3",
        "",
        "**Date:** 2026-09-04  ",
        "**Machine:** `data/market/research_engine/POST_V21_AUTODRIVE/FAILURE_ATLAS.json`  ",
        "**Script:** `research_engine/post_v21_w3_atlas.py`",
        "",
        "Span V8–V21. %d rows. Validation capital negative: %d. Beat EW on overlap: %d. Level-1: %d (H11/H12, one cluster). NEW_INDEPENDENT: 0." % (n, n_neg, n_beat, payload["n_level1"]),
        "",
        "| id | ver | mechanism | val MF | val cap | sign | beat EW | corr H11 | frozen | why not next |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    def pct(x):
        return "—" if x is None else "%.2f%%" % (100 * x)

    def cr(x):
        return "—" if x is None else "%.2f" % x

    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["id"], r["version"], (r.get("mechanism") or "")[:70].replace("|", "/"),
            pct(r.get("val_mean_forward")), pct(r.get("val_capital")), r.get("val_capital_sign") or "—",
            {True: "Y", False: "N", None: "—"}.get(r.get("beat_ew"), "—"), cr(r.get("corr_vs_h11_month")),
            "Y" if r.get("frozen") else "N", r["why_not_next"].replace("|", "/")))
    lines += [
        "",
        "## Use",
        "",
        "Before opening any new family, find its mechanism here. If it is a row (or a ratio / membership / filing-window sibling of a row), it is not the next unit. Next: W4 strategy bind.",
        "",
    ]
    md = os.path.join(ROOT, "docs", "research_engine", "POST_V21_FAILURE_ATLAS.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("wrote", md)


if __name__ == "__main__":
    main()
