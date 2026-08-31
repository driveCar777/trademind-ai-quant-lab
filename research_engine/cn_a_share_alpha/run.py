"""Full V13 first wave. Frozen panel only. Stop after 12 or Level-1."""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha import (
    DENIED_END,
    DENIED_START,
    RESEARCH_END,
    RESEARCH_START,
    SEED,
    V13_ID,
    VALID_END,
    VALID_START,
)
from research_engine.cn_a_share_alpha.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_alpha.evaluate import (
    block_bootstrap,
    book_metrics,
    excess_series,
    fdr_from_pvals,
    ic_series,
    iid_bootstrap,
    ttest_p,
    years_between,
)
from research_engine.cn_a_share_alpha.features import eligible_mask, feature_matrix
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_alpha.paths import ALPHA_ROOT, EQUITY_DIR, TRADES_DIR, ensure_alpha_tree
from research_engine.cn_a_share_alpha.replay import (
    ew_market_series,
    naive_1d_series,
    nonoverlap_equity,
    overlapping_series,
    random_quintile_series,
)
from research_protocol.hashing import canonical_hash


WINDOWS = (
    ("research", RESEARCH_START, RESEARCH_END),
    ("validation", VALID_START, VALID_END),
    ("denied", DENIED_START, DENIED_END),
)


def _summarize_hyp(pack, hyp, benches):
    family = hyp["family"]
    lb = hyp["lookback"]
    print("HYP", hyp["id"], flush=True)
    scores = feature_matrix(pack, family, lb)
    elig = eligible_mask(pack, lb)
    out = {"id": hyp["id"], "family": family, "lookback": lb, "sign": hyp["sign"], "windows": {}, "by_year": {}}
    year_nets = {}
    for name, start, end in WINDOWS:
        lo = overlapping_series(pack, family, lb, start, end, top=True, scores=scores, elig=elig)
        sh = overlapping_series(pack, family, lb, start, end, top=False, scores=scores, elig=elig)
        curve, trades = nonoverlap_equity(pack, family, lb, start, end, top=True)
        years = max(0.25, years_between(start, end))
        ics = ic_series(pack, scores, elig, start, end)
        b0 = benches["B0"][name]
        xs = excess_series(lo, b0)
        tstat, pval = ttest_p(xs)
        met = book_metrics(lo, curve, trades, years)
        spread = None
        if lo and sh:
            spread = float(np.mean([a["net"] for a in lo]) - np.mean([b["net"] for b in sh]))
        out["windows"][name] = {
            "metrics": met,
            "ls_spread_net": spread,
            "rank_ic": float(np.mean(ics)) if ics else None,
            "ic_n": len(ics),
            "excess_vs_b0_mean": float(np.mean(xs)) if xs.size else None,
            "excess_t": tstat,
            "excess_p": pval,
            "bootstrap_iid": iid_bootstrap(xs, seed=SEED),
            "bootstrap_block": block_bootstrap(xs, seed=SEED),
        }
        for rec in lo:
            year_nets.setdefault(rec["date"][:4], []).append(rec["net"])
        if name == "validation":
            write_csv(
                os.path.join(EQUITY_DIR, hyp["id"] + ".csv"),
                ("date", "equity"),
                curve,
            )
            write_csv(
                os.path.join(TRADES_DIR, hyp["id"] + ".csv"),
                ("signal_date", "entry", "exit", "n_fill", "n_skip", "raw", "cost", "net", "adv"),
                trades,
            )
    out["by_year"] = dict((y, float(np.mean(v))) for y, v in sorted(year_nets.items()))
    return out


def run_all():
    ensure_alpha_tree()
    contract = build_contract()
    dump_json(os.path.join(ALPHA_ROOT, "CONTRACT.json"), contract)
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    print("PACK_READY", pack["meta"], flush=True)
    benches = {"B0": {}, "B1": {}, "B2": {}}
    for name, start, end in WINDOWS:
        print("BENCH", name, flush=True)
        benches["B0"][name] = ew_market_series(pack, start, end)
        benches["B1"][name] = random_quintile_series(pack, start, end)
        benches["B2"][name] = naive_1d_series(pack, start, end)
    results = []
    for hyp in HYPOTHESES:
        results.append(_summarize_hyp(pack, hyp, benches))
    pvals = [r["windows"]["validation"]["excess_p"] for r in results]
    fdr = fdr_from_pvals(pvals)
    for i, r in enumerate(results):
        r["fdr_q"] = 0.05
        r["fdr_adj_p"] = fdr["adjusted_p"][i] if i < len(fdr.get("adjusted_p") or []) else None
        r["fdr_discovery"] = i in (fdr.get("discoveries") or [])
        res = r["windows"]["research"]
        val = r["windows"]["validation"]
        ev_res = int(bool(res.get("excess_vs_b0_mean") and res["excess_vs_b0_mean"] > 0)) + int(
            bool(res.get("rank_ic") and res["rank_ic"] > 0)
        )
        ev_val = int(bool(val.get("excess_vs_b0_mean") and val["excess_vs_b0_mean"] > 0)) + int(
            bool(val.get("rank_ic") and val["rank_ic"] > 0)
        )
        r["evidence_research"] = ev_res
        r["evidence_validation"] = ev_val
        r["research_positive"] = ev_res >= 2 and (res.get("excess_vs_b0_mean") or 0) > 0
        r["validation_positive"] = ev_val >= 2 and (val.get("excess_vs_b0_mean") or 0) > 0
        r["level1"] = bool(
            r["research_positive"]
            and r["validation_positive"]
            and r["fdr_discovery"]
            and ev_res >= 2
            and ev_val >= 2
        )
    n_l1 = sum(1 for r in results if r.get("level1"))
    decision = "LEVEL_1_CANDIDATE" if n_l1 else "A_SHARE_PRICE_ALPHA_EXHAUSTED_V1"
    payload = {
        "id": V13_ID,
        "contract_hash": contract["contract_hash"],
        "dataset_id": contract["dataset_id"],
        "decision": decision,
        "n_level1": n_l1,
        "fdr": {"q": 0.05, "discoveries": fdr.get("discoveries"), "adjusted_p": fdr.get("adjusted_p")},
        "hypotheses": results,
        "benchmarks": {
            key: {
                name: {
                    "n": len(rows),
                    "mean_net": float(np.mean([x["net"] for x in rows])) if rows else None,
                }
                for name, rows in windows.items()
            }
            for key, windows in benches.items()
        },
        "NEW_PURCHASE": False,
        "FINAL_OOS": "DENIED",
        "LIVE": False,
    }
    payload["results_hash"] = canonical_hash(payload)
    dump_json(os.path.join(ALPHA_ROOT, "RESULTS.json"), payload)
    dump_json(os.path.join(ALPHA_ROOT, "FDR.json"), payload["fdr"])
    dump_json(
        os.path.join(ALPHA_ROOT, "BOOTSTRAP.json"),
        dict((r["id"], {"val_iid": r["windows"]["validation"]["bootstrap_iid"], "val_block": r["windows"]["validation"]["bootstrap_block"]}) for r in results),
    )
    failed = [r for r in results if not r.get("level1")]
    dump_json(
        os.path.join(ALPHA_ROOT, "FAILED.json"),
        {
            "n": len(failed),
            "ids": [r["id"] for r in failed],
            "note": "Not Candidate. Do not flip sign. Reopen only with a new contract.",
        },
    )
    master = []
    for r in results:
        val = r["windows"]["validation"]["metrics"]
        master.append(
            {
                "id": r["id"],
                "family": r["family"],
                "lookback": r["lookback"],
                "val_excess": r["windows"]["validation"]["excess_vs_b0_mean"],
                "val_rank_ic": r["windows"]["validation"]["rank_ic"],
                "val_cagr": val.get("cagr"),
                "val_maxdd": val.get("maxdd"),
                "fdr_discovery": r["fdr_discovery"],
                "level1": r["level1"],
            }
        )
    write_csv(
        os.path.join(ALPHA_ROOT, "MASTER_BACKTEST.csv"),
        ("id", "family", "lookback", "val_excess", "val_rank_ic", "val_cagr", "val_maxdd", "fdr_discovery", "level1"),
        master,
    )
    print("DECISION", decision, "level1", n_l1, flush=True)
    return payload
