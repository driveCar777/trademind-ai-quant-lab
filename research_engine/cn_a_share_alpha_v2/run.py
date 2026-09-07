"""V15 alpha run. Frozen panel. Dual books. No H11/H12 reopen. No H13."""
from __future__ import print_function

import csv
import gc
import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, load_json, write_csv
from research_engine.cn_a_share_alpha.evaluate import block_bootstrap, fdr_from_pvals, iid_bootstrap, onesided_p
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_alpha_v2 import (
    DENIED,
    FINAL_OOS_ACCESS,
    INITIAL,
    NEW_PURCHASE,
    RESEARCH,
    SAME_CLUSTER_CORR,
    SEED,
    VALIDATION,
)
from research_engine.cn_a_share_alpha_v2.books import (
    capital_book,
    ew_overlapping,
    ic_series,
    overlapping_predictive,
    random_overlapping,
)
from research_engine.cn_a_share_alpha_v2.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_alpha_v2.evaluate import (
    corr_maps,
    excess_mean,
    share_of_top,
    summarize_capital,
    summarize_predictive,
)
from research_engine.cn_a_share_alpha_v2.paths import EQUITY, OUT, TRADES, ensure_out
from research_engine.cn_a_share_alpha_v2.signals import cs_breadth, cs_dispersion, residual_pack, score_for, state_mask
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix


def _load_legacy_cluster():
    root = os.path.join(os.path.dirname(OUT), "cn_a_share_strategy_v14_1")
    cap = os.path.join(root, "CAPITAL_REPLAY.csv")
    br11 = os.path.join(root, "CANDIDATE_TO_STRATEGY_BRIDGE_H11.csv")
    br12 = os.path.join(root, "CANDIDATE_TO_STRATEGY_BRIDGE_H12.csv")
    out = {"H11_VOL_60": {"capital": {}, "predictive": {}}, "H12_VOL_120": {"capital": {}, "predictive": {}}}
    if os.path.isfile(cap):
        handle = open(cap, "r", encoding="utf-8")
        try:
            for row in csv.DictReader(handle):
                hid = row.get("candidate_id")
                if hid in out:
                    out[hid]["capital"][row["signal_date"]] = float(row["capital_ret"])
        finally:
            handle.close()
    for hid, path in (("H11_VOL_60", br11), ("H12_VOL_120", br12)):
        if not os.path.isfile(path):
            continue
        handle = open(path, "r", encoding="utf-8")
        try:
            for row in csv.DictReader(handle):
                v = row.get("candidate_forward_return")
                if v not in (None, ""):
                    out[hid]["predictive"][row["date"]] = float(v)
        finally:
            handle.close()
    return out


def _window_rows(rows, start, end):
    return [r for r in rows if start <= r["date"] <= end]


def run_one(pack, xok, cache, hyp, benches):
    hid = hyp["id"]
    hold = hyp["hold_days"]
    L = hyp["lookback"]
    print("V15", hid, "SCORE", flush=True)
    elig = cache["elig20"] if L == 20 else cache["elig60"]
    scores = score_for(hyp, cache)
    st = None
    if hyp.get("state"):
        st = state_mask(hyp["state"], cache["disp"], cache["breadth"], hyp.get("state_lookback") or 60)
    pred = overlapping_predictive(pack, scores, elig, xok, RESEARCH[0], VALIDATION[1], hold, state=st)
    pred_r = _window_rows(pred, RESEARCH[0], RESEARCH[1])
    pred_v = _window_rows(pred, VALIDATION[0], VALIDATION[1])
    bench = benches[hold]
    ic_r = ic_series(pack, scores, elig, RESEARCH[0], RESEARCH[1], hold, state=st)
    ic_v = ic_series(pack, scores, elig, VALIDATION[0], VALIDATION[1], hold, state=st)
    ex_r, et_r, ep_r = excess_mean(pred_r, bench["ew"])
    ex_v, et_v, ep_v = excess_mean(pred_v, bench["ew"])
    print("V15", hid, "CAPITAL", flush=True)
    cap_r = capital_book(pack, scores, elig, xok, RESEARCH[0], RESEARCH[1], hold, state=st)
    cap_v = capital_book(pack, scores, elig, xok, VALIDATION[0], VALIDATION[1], hold, state=st)
    cap_f = capital_book(pack, scores, elig, xok, RESEARCH[0], VALIDATION[1], hold, state=st)
    sm_r = summarize_predictive(pred_r)
    sm_v = summarize_predictive(pred_v)
    capm_r = summarize_capital(cap_r, RESEARCH[0], hold)
    capm_v = summarize_capital(cap_v, VALIDATION[0], hold)
    capm_f = summarize_capital(cap_f, RESEARCH[0], hold)
    by_sym = {}
    for r in cap_f["ledger"]:
        if r.get("filled"):
            by_sym[r["symbol"]] = by_sym.get(r["symbol"], 0.0) + float(r.get("net") or 0.0)
    rec = {
        "id": hid,
        "family": hyp["family"],
        "lookback": L,
        "hold_days": hold,
        "state": hyp.get("state"),
        "signal": hyp["signal"],
        "mechanism": hyp["mechanism"],
        "predictive": {
            "research": dict(sm_r, excess_vs_b0=ex_r, excess_t=et_r, excess_p=ep_r, rank_ic=float(np.mean(ic_r)) if ic_r else None),
            "validation": dict(sm_v, excess_vs_b0=ex_v, excess_t=et_v, excess_p=ep_v, rank_ic=float(np.mean(ic_v)) if ic_v else None),
        },
        "capital": {"research": capm_r, "validation": capm_v, "full": capm_f},
        "concentration": {
            "stock": share_of_top(list(by_sym.values())),
            "rebalance": share_of_top([tr["net_yuan"] for tr in cap_f["trades"]]),
        },
        "n_state_on": None if st is None else int(np.sum(st)),
        "period_rets": dict((tr["signal_date"], tr["capital_ret"]) for tr in cap_f["trades"]),
        "pred_rets": dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in pred),
    }
    write_csv(
        os.path.join(EQUITY, "%s.csv" % hid),
        ("signal_date", "exit", "capital_ret", "equity"),
        [{"signal_date": tr["signal_date"], "exit": tr["exit"], "capital_ret": tr["capital_ret"], "equity": tr["equity"]} for tr in cap_f["trades"]],
    )
    write_csv(
        os.path.join(TRADES, "%s.csv" % hid),
        ("signal_date", "entry", "exit", "n_sel", "n_fill", "capital_ret", "net_yuan"),
        cap_f["trades"],
    )
    del scores
    gc.collect()
    print(
        "V15",
        hid,
        "PRED",
        sm_v.get("MEAN_FORWARD_RETURN"),
        "CAP_R",
        capm_r.get("total"),
        "CAP_V",
        capm_v.get("total"),
        flush=True,
    )
    return rec


def _is_level1(rec, fdr_hit):
    pr = rec["predictive"]["research"]
    pv = rec["predictive"]["validation"]
    cr = rec["capital"]["research"]
    cv = rec["capital"]["validation"]
    checks = {
        "pre_registered": True,
        "research_mean_forward_net": (pr.get("MEAN_FORWARD_RETURN") or 0) > 0,
        "validation_mean_forward_net": (pv.get("MEAN_FORWARD_RETURN") or 0) > 0,
        "research_excess": (pr.get("excess_vs_b0") or 0) > 0,
        "validation_excess": (pv.get("excess_vs_b0") or 0) > 0,
        "research_rank_ic": (pr.get("rank_ic") or 0) > 0,
        "validation_rank_ic": (pv.get("rank_ic") or 0) > 0,
        "fdr": bool(fdr_hit),
        "research_capital": (cr.get("total") or 0) > 0,
        "validation_capital": (cv.get("total") or 0) > 0,
        "capital_recon": bool(cr.get("recon_ok") and cv.get("recon_ok")),
    }
    ev_r = int(checks["research_excess"]) + int(checks["research_rank_ic"])
    ev_v = int(checks["validation_excess"]) + int(checks["validation_rank_ic"])
    checks["evidence_research"] = ev_r
    checks["evidence_validation"] = ev_v
    ok = (
        checks["research_mean_forward_net"]
        and checks["validation_mean_forward_net"]
        and checks["fdr"]
        and ev_r >= 2
        and ev_v >= 2
        and checks["research_capital"]
        and checks["validation_capital"]
    )
    return ok, checks


def decide(rows, legacy):
    pvals = []
    for r in rows:
        pv = r["predictive"]["validation"]
        pvals.append(onesided_p(pv.get("excess_t"), pv.get("excess_p")))
    fdr = fdr_from_pvals(pvals)
    candidates = []
    for i, r in enumerate(rows):
        r["onesided_p"] = pvals[i]
        r["fdr_adj_p"] = fdr["adjusted_p"][i]
        r["fdr_discovery"] = i in (fdr.get("discoveries") or [])
        ok, checks = _is_level1(r, r["fdr_discovery"])
        r["gate"] = checks
        r["level1"] = ok
        cluster = {}
        for hid in ("H11_VOL_60", "H12_VOL_120"):
            cluster[hid] = {
                "capital": corr_maps(r["period_rets"], legacy[hid]["capital"]),
                "predictive": corr_maps(r["pred_rets"], legacy[hid]["predictive"]),
            }
        r["corr_vs_low_vol"] = cluster
        mx = max([abs(v) for pair in cluster.values() for v in pair.values() if v is not None] or [0.0])
        if ok and mx > SAME_CLUSTER_CORR:
            r["cluster_tag"] = "SAME_CLUSTER"
        elif ok:
            r["cluster_tag"] = "POTENTIALLY_INDEPENDENT"
        else:
            r["cluster_tag"] = None
        if ok:
            candidates.append(r)
    n = len(candidates)
    if n == 0:
        overall = "NO_NEW_CANDIDATE"
        nxt = "A_SHARE_PRICE_ALPHA_REVIEW_V2"
    elif any(c.get("cluster_tag") == "POTENTIALLY_INDEPENDENT" for c in candidates):
        overall = "NEW_INDEPENDENT_CANDIDATE"
        nxt = "CANDIDATE_REPRODUCTION"
    else:
        overall = "WEAK_CANDIDATE_SAME_CLUSTER"
        nxt = "KEEP_LOW_VOL_CLUSTER_NO_NEW_SLEEVE"
    return {
        "LEVEL": 1,
        "EXISTING_CANDIDATE": 2,
        "NEW_CANDIDATE": n,
        "CANDIDATE": 2 + n,
        "STRATEGY": 2,
        "PORTFOLIO": 0,
        "PAPER": 0,
        "LIVE": 0,
        "OVERALL": overall,
        "NEXT": nxt,
        "candidate_ids": [c["id"] for c in candidates],
        "cluster_tags": dict((c["id"], c.get("cluster_tag")) for c in candidates),
        "fdr": {"q": 0.05, "discoveries": fdr.get("discoveries"), "adjusted_p": fdr["adjusted_p"]},
        "new_purchase": NEW_PURCHASE,
        "final_oos": FINAL_OOS_ACCESS,
        "denied": list(DENIED),
        "h11_h12": "KEEP_LOW_PRIORITY",
        "retune": False,
        "make_10pct": False,
    }, fdr


def run_v15():
    ensure_out()
    contract = build_contract()
    dump_json(os.path.join(OUT, "CONTRACT.json"), contract)
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    print("V15 EXEC", flush=True)
    xok = exec_ok_matrix(pack)
    print("V15 RESIDUAL", flush=True)
    rp = residual_pack(pack, 20)
    cache = {
        "ret": rp["ret"],
        "resid": rp["resid"],
        "market": rp["market"],
        "elig20": rp["elig"],
        "elig60": eligible(pack, 60),
        "amount": pack["amount"],
        "disp": cs_dispersion(rp["resid"], rp["elig"]),
        "breadth": cs_breadth(rp["ret"], rp["elig"]),
    }
    print("V15 BENCH", flush=True)
    benches = {}
    for hold in (5, 20):
        ew = ew_overlapping(pack, cache["elig20"], xok, RESEARCH[0], VALIDATION[1], hold)
        rnd = random_overlapping(pack, cache["elig20"], xok, RESEARCH[0], VALIDATION[1], hold)
        benches[hold] = {
            "ew": ew,
            "random": rnd,
            "ew_summary": {
                "research": summarize_predictive(_window_rows(ew, RESEARCH[0], RESEARCH[1])),
                "validation": summarize_predictive(_window_rows(ew, VALIDATION[0], VALIDATION[1])),
            },
            "random_summary": {
                "research": summarize_predictive(_window_rows(rnd, RESEARCH[0], RESEARCH[1])),
                "validation": summarize_predictive(_window_rows(rnd, VALIDATION[0], VALIDATION[1])),
            },
        }
    rows = []
    done = {}
    partial_path = os.path.join(OUT, "RESULTS_PARTIAL.json")
    if os.path.isfile(partial_path):
        prev = load_json(partial_path)
        if prev.get("contract_hash") == contract["contract_hash"]:
            for rec in prev.get("rows") or []:
                done[rec["id"]] = rec
            print("V15 RESUME", len(done), flush=True)
    for hyp in HYPOTHESES:
        if hyp["id"] in done:
            print("V15 SKIP", hyp["id"], flush=True)
            rows.append(done[hyp["id"]])
            continue
        rec = run_one(pack, xok, cache, hyp, benches)
        rows.append(rec)
        dump_json(
            partial_path,
            {
                "contract_hash": contract["contract_hash"],
                "rows": [
                    {
                        "id": r["id"],
                        "family": r["family"],
                        "lookback": r["lookback"],
                        "hold_days": r["hold_days"],
                        "state": r.get("state"),
                        "signal": r.get("signal"),
                        "mechanism": r.get("mechanism"),
                        "predictive": r["predictive"],
                        "capital": r["capital"],
                        "concentration": r["concentration"],
                        "n_state_on": r.get("n_state_on"),
                        "period_rets": r.get("period_rets"),
                        "pred_rets": r.get("pred_rets"),
                    }
                    for r in rows
                ],
            },
        )
        gc.collect()
    legacy = _load_legacy_cluster()
    decision, fdr = decide(rows, legacy)
    boot = {}
    for r in rows:
        if not r.get("level1"):
            continue
        nets = [v for d, v in sorted(r["pred_rets"].items()) if VALIDATION[0] <= d <= VALIDATION[1]]
        boot[r["id"]] = {
            "iid": iid_bootstrap(nets, n=1000, seed=SEED),
            "block": block_bootstrap(nets, block=r["hold_days"], n=1000, seed=SEED),
        }
        # cost stress on validation capital
        elig = cache["elig20"] if r["lookback"] == 20 else cache["elig60"]
        scores = score_for(next(h for h in HYPOTHESES if h["id"] == r["id"]), cache)
        st = None
        if r.get("state"):
            st = state_mask(r["state"], cache["disp"], cache["breadth"], 60 if r["state"] != "DISP_RISING_20" else 20)
        stress = {}
        for label, ck, sk in (("1x", 1.0, 1.0), ("1.5x", 1.5, 1.5), ("2x", 2.0, 2.0)):
            sim = capital_book(
                pack, scores, elig, xok, VALIDATION[0], VALIDATION[1], r["hold_days"], state=st, cost_k=ck, slip_k=sk
            )
            stress[label] = {"end": sim["end"], "total": sim["total"]}
        r["cost_stress"] = stress
        del scores
    perm = {}
    pos_fams = set(r["family"] for r in rows if r.get("level1"))
    rng = np.random.RandomState(SEED)
    for fam in pos_fams:
        hyp = next(h for h in HYPOTHESES if h["family"] == fam)
        elig = cache["elig20"] if hyp["lookback"] == 20 else cache["elig60"]
        base = score_for(hyp, cache)
        means = []
        for k in range(100):
            shuf = base.copy()
            for i in range(0, shuf.shape[0], 17):
                row = shuf[i]
                ok = np.isfinite(row)
                vals = row[ok]
                rng.shuffle(vals)
                row = row.copy()
                row[ok] = vals
                shuf[i] = row
            pred = overlapping_predictive(
                pack, shuf, elig, xok, VALIDATION[0], VALIDATION[1], hyp["hold_days"]
            )
            if pred:
                means.append(float(np.mean([p["MEAN_FORWARD_RETURN"] for p in pred])))
        live = next(r for r in rows if r["id"] == hyp["id"])["predictive"]["validation"].get("MEAN_FORWARD_RETURN")
        perm[fam] = {
            "n": len(means),
            "null_mean": float(np.mean(means)) if means else None,
            "p_ge_live": float(np.mean(np.array(means) >= live)) if means and live is not None else None,
        }
    failures = []
    for r in rows:
        if r.get("level1"):
            continue
        g = r["gate"]
        why = [k for k, v in g.items() if v is False]
        failures.append(
            {
                "id": r["id"],
                "family": r["family"],
                "mechanism": r["mechanism"],
                "why_failed": why,
                "reopen": "New contract only. Do not flip sign. Do not retune lookback/hold/quantile.",
            }
        )
    slim = []
    for r in rows:
        slim.append(
            {
                "id": r["id"],
                "family": r["family"],
                "lookback": r["lookback"],
                "hold_days": r["hold_days"],
                "predictive": r["predictive"],
                "capital": r["capital"],
                "concentration": r["concentration"],
                "gate": r["gate"],
                "level1": r["level1"],
                "cluster_tag": r.get("cluster_tag"),
                "corr_vs_low_vol": r.get("corr_vs_low_vol"),
                "fdr_discovery": r.get("fdr_discovery"),
                "fdr_adj_p": r.get("fdr_adj_p"),
                "onesided_p": r.get("onesided_p"),
                "cost_stress": r.get("cost_stress"),
            }
        )
    dump_json(os.path.join(OUT, "RESULTS.json"), {"hypotheses": slim, "decision": decision["OVERALL"]})
    dump_json(os.path.join(OUT, "PREDICTIVE_RESULTS.json"), dict((r["id"], r["predictive"]) for r in rows))
    dump_json(os.path.join(OUT, "CAPITAL_RESULTS.json"), dict((r["id"], r["capital"]) for r in rows))
    dump_json(os.path.join(OUT, "FDR.json"), decision["fdr"])
    dump_json(os.path.join(OUT, "BOOTSTRAP.json"), boot)
    dump_json(
        os.path.join(OUT, "CLUSTER.json"),
        {
            "existing": "LOW_VOL_CANDIDATE_CLUSTER",
            "same_cluster_cut": SAME_CLUSTER_CORR,
            "by_hyp": dict((r["id"], r.get("corr_vs_low_vol")) for r in rows),
            "tags": dict((r["id"], r.get("cluster_tag")) for r in rows),
            "permutation": perm,
        },
    )
    dump_json(os.path.join(OUT, "FAILURES.json"), {"n": len(failures), "rows": failures})
    dump_json(os.path.join(OUT, "DECISION.json"), decision)
    dump_json(os.path.join(OUT, "BENCHMARKS.json"), dict((str(h), benches[h]["ew_summary"]) for h in benches))
    print("V15_DONE", decision["OVERALL"], "NEW", decision["NEW_CANDIDATE"], flush=True)
    return decision


if __name__ == "__main__":
    run_v15()
