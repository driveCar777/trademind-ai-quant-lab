"""Industry RS / breadth on PIT monthly membership. Dual books. No H11 mix."""
from __future__ import print_function

import os
from collections import defaultdict

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha.evaluate import fdr_from_pvals, onesided_p
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_alpha_v2.books import capital_book, ew_overlapping, ic_series, overlapping_predictive
from research_engine.cn_a_share_alpha_v2.evaluate import corr_maps, excess_mean, share_of_top, summarize_capital, summarize_predictive
from research_engine.cn_a_share_alpha_v2.run import _load_legacy_cluster, _window_rows
from research_engine.cn_a_share_information_v16 import HOLD_DAYS, RESEARCH, SAME_CLUSTER_CORR, VALIDATION
from research_engine.cn_a_share_information_v16.alpha import _is_level1
from research_engine.cn_a_share_information_v16.contract import IND_HYPOTHESES, build_industry_contract
from research_engine.cn_a_share_information_v16.paths import EQUITY, OUT, TRADES, ensure_v16
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix


def _ind_by_asof(rows):
    by = defaultdict(dict)
    dates = set()
    for r in rows:
        asof = r.get("effective_date")
        if not asof or not r.get("symbol"):
            continue
        by[asof][r["symbol"]] = r.get("industry") or ""
        dates.add(asof)
    return by, sorted(dates)


def _fill_industry_codes(dates, symbols, by_asof, asofs):
    t, n = len(dates), len(symbols)
    # compact id
    all_ind = set()
    for mp in by_asof.values():
        all_ind.update(mp.values())
    ind_id = {name: i + 1 for i, name in enumerate(sorted(all_ind))}
    out = np.zeros((t, n), dtype=np.int16)
    sym_ix = {s: j for j, s in enumerate(symbols)}
    ptr = 0
    for t_i, day in enumerate(dates):
        while ptr + 1 < len(asofs) and asofs[ptr + 1] <= day:
            ptr += 1
        if not asofs or asofs[ptr] > day:
            continue
        mp = by_asof[asofs[ptr]]
        for sym, name in mp.items():
            j = sym_ix.get(sym)
            if j is not None:
                out[t_i, j] = ind_id.get(name, 0)
    return out


def industry_score(pack, ind_codes, lookback, kind):
    close = np.array(pack["close"], dtype=np.float64)
    t, n = close.shape
    ret = np.full((t, n), np.nan, dtype=np.float64)
    if lookback < t:
        a = close[lookback:]
        b = close[:-lookback]
        good = np.isfinite(a) & np.isfinite(b) & (b > 0)
        ret[lookback:] = np.where(good, a / b - 1.0, np.nan)
    scores = np.full((t, n), np.nan, dtype=np.float64)
    for i in range(lookback, t):
        codes = ind_codes[i]
        r = ret[i]
        ok = (codes > 0) & np.isfinite(r)
        if int(np.sum(ok)) < 50:
            continue
        c = codes[ok]
        rr = r[ok]
        uids, inv = np.unique(c, return_inverse=True)
        if kind == "rs":
            num = np.bincount(inv, weights=rr)
            den = np.bincount(inv).astype(np.float64)
            stat = num / np.maximum(den, 1.0)
        else:
            pos = np.bincount(inv, weights=(rr > 0).astype(np.float64))
            den = np.bincount(inv).astype(np.float64)
            stat = pos / np.maximum(den, 1.0)
        lookup = dict(zip(uids.tolist(), stat.tolist()))
        mapped = np.array([lookup.get(int(k), np.nan) if k > 0 else np.nan for k in codes], dtype=np.float64)
        scores[i] = mapped
    return scores


def run_industry_alpha(ind_rows):
    ensure_v16()
    contract = build_industry_contract(False)
    dump_json(os.path.join(OUT, "INDUSTRY_ALPHA_CONTRACT.json"), contract)
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    print("V16_IND_ALPHA_MAP", flush=True)
    by_asof, asofs = _ind_by_asof(ind_rows)
    ind_codes = _fill_industry_codes(pack["dates"], pack["symbols"], by_asof, asofs)
    xok = exec_ok_matrix(pack)
    elig = eligible(pack, 20)
    ew = ew_overlapping(pack, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    recs = []
    for hyp in IND_HYPOTHESES:
        print("V16_IND_ALPHA", hyp["id"], flush=True)
        kind = "rs" if hyp["signal"].startswith("INDUSTRY_RS") else "breadth"
        scores = industry_score(pack, ind_codes, hyp["lookback"], kind)
        pred = overlapping_predictive(pack, scores, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
        pred_r = _window_rows(pred, RESEARCH[0], RESEARCH[1])
        pred_v = _window_rows(pred, VALIDATION[0], VALIDATION[1])
        ic_r = ic_series(pack, scores, elig, RESEARCH[0], RESEARCH[1], HOLD_DAYS)
        ic_v = ic_series(pack, scores, elig, VALIDATION[0], VALIDATION[1], HOLD_DAYS)
        ex_r, et_r, ep_r = excess_mean(pred_r, ew)
        ex_v, et_v, ep_v = excess_mean(pred_v, ew)
        cap_r = capital_book(pack, scores, elig, xok, RESEARCH[0], RESEARCH[1], HOLD_DAYS)
        cap_v = capital_book(pack, scores, elig, xok, VALIDATION[0], VALIDATION[1], HOLD_DAYS)
        cap_f = capital_book(pack, scores, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
        rec = {
            "id": hyp["id"],
            "family": hyp["family"],
            "signal": hyp["signal"],
            "mechanism": hyp["mechanism"],
            "predictive": {
                "research": dict(summarize_predictive(pred_r), excess_vs_b0=ex_r, excess_t=et_r, excess_p=ep_r, rank_ic=float(np.mean(ic_r)) if ic_r else None),
                "validation": dict(summarize_predictive(pred_v), excess_vs_b0=ex_v, excess_t=et_v, excess_p=ep_v, rank_ic=float(np.mean(ic_v)) if ic_v else None),
            },
            "capital": {
                "research": summarize_capital(cap_r, RESEARCH[0], HOLD_DAYS),
                "validation": summarize_capital(cap_v, VALIDATION[0], HOLD_DAYS),
                "full": summarize_capital(cap_f, RESEARCH[0], HOLD_DAYS),
            },
            "concentration": {"rebalance": share_of_top([tr["net_yuan"] for tr in cap_f["trades"]])},
            "period_rets": dict((tr["signal_date"], tr["capital_ret"]) for tr in cap_f["trades"]),
            "pred_rets": dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in pred),
        }
        write_csv(
            os.path.join(EQUITY, "%s.csv" % hyp["id"]),
            ("signal_date", "exit", "capital_ret", "equity"),
            [{"signal_date": tr["signal_date"], "exit": tr["exit"], "capital_ret": tr["capital_ret"], "equity": tr["equity"]} for tr in cap_f["trades"]],
        )
        write_csv(os.path.join(TRADES, "%s.csv" % hyp["id"]), ("signal_date", "entry", "exit", "n_sel", "n_fill", "capital_ret", "net_yuan"), cap_f["trades"])
        print("V16_IND_ALPHA", hyp["id"], "PRED", rec["predictive"]["validation"].get("MEAN_FORWARD_RETURN"), "CAP_V", rec["capital"]["validation"].get("total"), flush=True)
        del scores
        recs.append(rec)
    legacy = _load_legacy_cluster()
    pvals = [onesided_p(r["predictive"]["validation"].get("excess_t"), r["predictive"]["validation"].get("excess_p")) for r in recs]
    fdr = fdr_from_pvals(pvals)
    candidates = []
    failures = []
    slim = []
    for i, r in enumerate(recs):
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
        r["cluster_tag"] = "SAME_CLUSTER" if ok and mx > SAME_CLUSTER_CORR else ("POTENTIALLY_INDEPENDENT" if ok else None)
        if ok:
            candidates.append(r)
        else:
            failures.append({"id": r["id"], "family": r["family"], "mechanism": r["mechanism"], "why_failed": [k for k, v in checks.items() if v is False], "reopen": "New contract only. Do not mix with H11/H12."})
        slim.append({k: r[k] for k in ("id", "family", "predictive", "capital", "concentration", "gate", "level1", "cluster_tag", "corr_vs_low_vol", "fdr_discovery", "fdr_adj_p", "onesided_p") if k in r})
    dump_json(os.path.join(OUT, "INDUSTRY_RESULTS.json"), {"hypotheses": slim})
    dump_json(os.path.join(OUT, "INDUSTRY_FDR.json"), {"q": 0.05, "adjusted_p": fdr["adjusted_p"], "discoveries": fdr.get("discoveries")})
    return recs, candidates, failures
