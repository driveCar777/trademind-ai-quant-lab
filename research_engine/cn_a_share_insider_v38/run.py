"""V38-L1 runner: insider/holder trades layer, one pre-registered model, LO20 gate book, A4 independence vs ML1 (and V27 ML2F)."""
from __future__ import print_function

import json
import os
import sys
import warnings

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.evaluate import fdr_from_pvals, onesided_p
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_alpha_v2.books import ew_overlapping, overlapping_predictive
from research_engine.cn_a_share_findeep_v27 import OUT as V27_OUT
from research_engine.cn_a_share_information_v16.alpha import _is_level1
from research_engine.cn_a_share_macro_v17.evaluate import _json_safe
from research_engine.cn_a_share_ml_v25 import HEDGE_INDEX, ROLLING_BLOCKS, ROLLING_MIN_POSITIVE
from research_engine.cn_a_share_ml_v25 import OUT as V25_OUT
from research_engine.cn_a_share_ml_v25.index_daily import load_open_series
from research_engine.cn_a_share_ml_v25.model import build_scores
from research_engine.cn_a_share_ml_v25.run import evaluate_signal, slim
from research_engine.cn_a_share_insider_v38 import EQUITY, FDR_Q, HOLD_DAYS, NORM, OUT, RESEARCH, SAME_CLUSTER_CORR, TRADES, V38L4_ID, VALIDATION, ensure_v38l4
from research_engine.cn_a_share_insider_v38.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_insider_v38.features import NAMES, INS_FEATURES, build_features
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix

warnings.filterwarnings("ignore")
TAG = "V38L4"


def progress(stage, **extra):
    d = {"stage": stage, "id": V38L4_ID}
    d.update(extra)
    dump_json(os.path.join(OUT, "PROGRESS.json"), _json_safe(d))
    print(TAG, "PROGRESS", stage, flush=True)


def _corr(a, b):
    keys = sorted(set(a) & set(b))
    if len(keys) < 8:
        return None, len(keys)
    x = np.array([a[k] for k in keys])
    y = np.array([b[k] for k in keys])
    return float(np.corrcoef(x, y)[0, 1]), len(keys)


def excess_series(pack, scores, elig, xok, ewm):
    pred = overlapping_predictive(pack, scores, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    return dict((r["date"], r["MEAN_FORWARD_RETURN"] - ewm[r["date"]]) for r in pred if r["date"] in ewm)


def main():
    ensure_v38l4()
    if os.path.isfile(os.path.join(OUT, "DECISION.json")):
        raise RuntimeError("V38L4_ALREADY_RUN: one run only; a second configuration is a new contract")
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    dates = pack["dates"]
    xok = exec_ok_matrix(pack)
    elig = eligible(pack, 20)
    feats = build_features(pack)
    pit = json.load(open(os.path.join(NORM, "INSIDER_PIT.json"), encoding="utf-8"))
    contract = build_contract(pit["content_hash"])
    dump_json(os.path.join(OUT, "CONTRACT.json"), contract)
    progress("CONTRACT", contract_hash=contract["contract_hash"], insider_hash=pit["content_hash"])
    cover = {}
    for n in NAMES:
        a = feats[n]
        cover[n] = {"last_session": float(np.isfinite(a[-1]).mean()),
                    "mean_over_research": float(np.nanmean([np.isfinite(a[t]).mean() for t in range(0, len(dates), 250)]))}
    dump_json(os.path.join(OUT, "FEATURE_COVERAGE.json"), {"features": cover, "pit": pit})
    progress("FEATURES", n=len(NAMES))
    idx_open = load_open_series(HEDGE_INDEX, dates)
    ew = ew_overlapping(pack, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)

    progress("MODEL_START", signal="ML5I_LGBM")
    sc, meta = build_scores(pack, feats, elig, xok, features=INS_FEATURES, tag="V38L4_ML5I")
    scores = sc["ML1_LGBM"]
    np.save(os.path.join(OUT, "SCORES_ML5I_LGBM.npy"), scores)
    dump_json(os.path.join(OUT, "MODEL_ML5I_LGBM.json"), meta)
    progress("MODEL_DONE")

    recs = []
    for hyp in HYPOTHESES:
        rec = evaluate_signal(hyp["id"], scores, pack, elig, xok, ew, idx_open, gate_book="LO20",
                              equity_dir=EQUITY, trades_dir=TRADES, tag=TAG)
        rec.update({"family": hyp["family"], "signal": hyp["signal"], "mechanism": hyp["mechanism"]})
        recs.append(rec)
        progress("HYP_DONE", id=hyp["id"])

    refs = {"ML1_LGBM_STACK": excess_series(pack, np.load(os.path.join(V25_OUT, "SCORES_ML1_LGBM.npy")), elig, xok, ewm)}
    p27 = os.path.join(V27_OUT, "SCORES_ML2F_LGBM.npy")
    if os.path.isfile(p27):
        refs["ML2F_LGBM_FINDEEP_ONLY"] = excess_series(pack, np.load(p27), elig, xok, ewm)
    pvals = [onesided_p(r["predictive"]["validation"].get("excess_t"), r["predictive"]["validation"].get("excess_p")) for r in recs]
    fdr = fdr_from_pvals(pvals)
    candidates, failures = [], []
    for i, r in enumerate(recs):
        r["onesided_p"], r["fdr_adj_p"], r["fdr_discovery"] = pvals[i], fdr["adjusted_p"][i], i in (fdr.get("discoveries") or [])
        ok, checks = _is_level1(r, r["fdr_discovery"])
        checks["rolling_%d_of_%d" % (ROLLING_MIN_POSITIVE, len(ROLLING_BLOCKS))] = r["rolling"]["pass"]
        ok = bool(ok and r["rolling"]["pass"])
        r["gate"], r["level1"] = checks, ok
        mine = dict((d, v - ewm[d]) for d, v in r["pred_rets"].items() if d in ewm)
        ex_corr = {}
        for k, ref in refs.items():
            c, n = _corr(mine, ref)
            ex_corr[k] = {"excess_corr": c, "n": n}
        r["excess_corr"] = ex_corr
        c_ml1 = ex_corr["ML1_LGBM_STACK"]["excess_corr"]
        r["cluster_tag"] = ("SAME_CLUSTER" if (c_ml1 is not None and abs(c_ml1) > SAME_CLUSTER_CORR) else "POTENTIALLY_INDEPENDENT") if ok else None
        (candidates if ok else failures).append(r if ok else {"id": r["id"], "why_failed": [k for k, v in checks.items() if v is False],
                                                              "excess_corr": ex_corr, "reopen": "New contract only. No feature/param search."})
    dump_json(os.path.join(OUT, "FDR.json"), {"q": FDR_Q, "m_layer": len(recs), "adjusted_p": fdr["adjusted_p"], "discoveries": fdr.get("discoveries") or []})
    dump_json(os.path.join(OUT, "FAILURES.json"), {"n": len(failures), "rows": failures})
    dump_json(os.path.join(OUT, "CANDIDATES.json"), {"n": len(candidates), "ids": [c["id"] for c in candidates],
                                                     "independent": [c["id"] for c in candidates if c["cluster_tag"] == "POTENTIALLY_INDEPENDENT"]})
    out_rows = []
    for r in recs:
        s = slim(r)
        s["excess_corr"] = r["excess_corr"]
        s["gain_share_last_refit"] = meta["refits"][-1]["gain_share"] if meta["refits"] else None
        out_rows.append(s)
    dump_json(os.path.join(OUT, "RESULTS.json"), {"hypotheses": out_rows})
    independent = [c for c in candidates if c["cluster_tag"] == "POTENTIALLY_INDEPENDENT"]
    same = [c for c in candidates if c["cluster_tag"] == "SAME_CLUSTER"]
    labels = contract["verdict_labels"]
    if independent:
        overall, nxt, stop = labels["pass"], "CANDIDATE_REPRODUCTION", "STOP_A"
    elif same:
        overall, nxt, stop = labels["same_cluster"], "KEEP_ML1_NO_NEW_SLEEVE", "STOP_A_SAME_CLUSTER_NOT_NEW_SLEEVE"
    else:
        overall, nxt, stop = labels["fail"], "NEXT_LAYER", "STOP_B_LAYER"
    decision = {"LEVEL": 1, "EXISTING_INDEPENDENT_CANDIDATE": 1, "NEW_CANDIDATE": len(candidates), "NEW_INDEPENDENT_CANDIDATE": len(independent),
                "STRATEGY": "ML1 unchanged", "PORTFOLIO": 1 if independent else 0, "PAPER": 0, "LIVE": 0,
                "OVERALL": overall, "NEXT": nxt, "STOP": stop, "candidate_ids": [c["id"] for c in candidates],
                "independent_ids": [c["id"] for c in independent], "new_purchase": False, "cost_usd": 0.0, "final_oos": "DENIED",
                "gate_book": "LO20", "amendment": "RESEARCH_RULES_AMENDMENT_V1", "contract_hash": contract["contract_hash"]}
    dump_json(os.path.join(OUT, "DECISION.json"), _json_safe(decision))
    progress("COMPLETE", overall=overall, stop=stop)
    print(TAG, "DECISION", overall, stop, "L1", len(candidates), "IND", len(independent), flush=True)
    return decision


if __name__ == "__main__":
    main()

