"""Re-apply the locked Level-1 gate to stored RESULTS. No new ranking."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import dump_json, load_json, write_csv
from research_engine.cn_a_share_alpha.evaluate import fdr_from_pvals, is_level1, onesided_p
from research_engine.cn_a_share_alpha.paths import ALPHA_ROOT
from research_protocol.hashing import canonical_hash


def apply_gate(results=None):
    path = os.path.join(ALPHA_ROOT, "RESULTS.json")
    results = results or load_json(path)
    hyps = results["hypotheses"]
    pvals = [
        onesided_p(r["windows"]["validation"].get("excess_t"), r["windows"]["validation"].get("excess_p"))
        for r in hyps
    ]
    fdr = fdr_from_pvals(pvals)
    for i, r in enumerate(hyps):
        res = r["windows"]["research"]
        val = r["windows"]["validation"]
        r_net = (res.get("metrics") or {}).get("mean_net_h")
        v_net = (val.get("metrics") or {}).get("mean_net_h")
        ev_res = int(bool(res.get("excess_vs_b0_mean") and res["excess_vs_b0_mean"] > 0)) + int(
            bool(res.get("rank_ic") and res["rank_ic"] > 0)
        )
        ev_val = int(bool(val.get("excess_vs_b0_mean") and val["excess_vs_b0_mean"] > 0)) + int(
            bool(val.get("rank_ic") and val["rank_ic"] > 0)
        )
        r["onesided_p"] = pvals[i]
        r["fdr_adj_p"] = fdr["adjusted_p"][i]
        r["fdr_discovery"] = i in (fdr.get("discoveries") or [])
        r["evidence_research"] = ev_res
        r["evidence_validation"] = ev_val
        r["research_positive"] = bool(r_net and r_net > 0 and ev_res >= 2)
        r["validation_positive"] = bool(v_net and v_net > 0 and ev_val >= 2)
        r["level1"] = is_level1(res, val, r["fdr_discovery"])
    n_l1 = sum(1 for r in hyps if r.get("level1"))
    results["n_level1"] = n_l1
    results["decision"] = "LEVEL_1_CANDIDATE" if n_l1 else "A_SHARE_PRICE_ALPHA_EXHAUSTED_V1"
    results["fdr"] = {"q": 0.05, "discoveries": fdr.get("discoveries"), "adjusted_p": fdr.get("adjusted_p")}
    results["gate_note"] = "cost-adjusted mean_net_h must be >0 on research AND validation. Two-sided p is not a Candidate."
    results.pop("results_hash", None)
    results["results_hash"] = canonical_hash(results)
    dump_json(path, results)
    dump_json(os.path.join(ALPHA_ROOT, "FDR.json"), results["fdr"])
    dump_json(
        os.path.join(ALPHA_ROOT, "FAILED.json"),
        {
            "n": sum(1 for r in hyps if not r.get("level1")),
            "ids": [r["id"] for r in hyps if not r.get("level1")],
            "level1_ids": [r["id"] for r in hyps if r.get("level1")],
            "note": "Not Candidate. Do not flip sign. Reopen only with a new contract.",
        },
    )
    master = []
    for r in hyps:
        val = r["windows"]["validation"]["metrics"]
        master.append(
            {
                "id": r["id"],
                "family": r["family"],
                "lookback": r["lookback"],
                "val_excess": r["windows"]["validation"]["excess_vs_b0_mean"],
                "val_rank_ic": r["windows"]["validation"]["rank_ic"],
                "val_cagr": val.get("cagr"),
                "val_net_h": val.get("mean_net_h"),
                "val_maxdd": val.get("maxdd"),
                "fdr_discovery": r["fdr_discovery"],
                "level1": r["level1"],
            }
        )
    write_csv(
        os.path.join(ALPHA_ROOT, "MASTER_BACKTEST.csv"),
        ("id", "family", "lookback", "val_excess", "val_rank_ic", "val_cagr", "val_net_h", "val_maxdd", "fdr_discovery", "level1"),
        master,
    )
    print("DECISION", results["decision"], "level1", n_l1, flush=True)
    return results
