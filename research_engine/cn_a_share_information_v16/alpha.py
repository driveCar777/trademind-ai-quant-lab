"""Financial alpha on PIT join. Dual books. No H11/H12 reopen."""
from __future__ import print_function

import csv
import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha.evaluate import fdr_from_pvals, onesided_p
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_alpha_v2.books import capital_book, ic_series, overlapping_predictive
from research_engine.cn_a_share_alpha_v2.evaluate import corr_maps, excess_mean, share_of_top, summarize_capital, summarize_predictive
from research_engine.cn_a_share_alpha_v2.run import _load_legacy_cluster, _window_rows
from research_engine.cn_a_share_information_v16 import DENIED, FDR_Q, HOLD_DAYS, INITIAL, RESEARCH, SAME_CLUSTER_CORR, SEED, VALIDATION
from research_engine.cn_a_share_information_v16.contract import FIN_HYPOTHESES, build_financial_contract
from research_engine.cn_a_share_information_v16.paths import EQUITY, OUT, TRADES, ensure_v16
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix


def _date_start(dates, day):
    for i, d in enumerate(dates):
        if d >= day:
            return i
    return None


def _yoy(vis, field):
    annuals = [r for r in vis if int(r.get("quarter") or 0) == 4 and r.get(field) is not None]
    if not annuals:
        return None
    latest = annuals[-1]
    prev = None
    for r in reversed(annuals[:-1]):
        if int(r["year"]) == int(latest["year"]) - 1:
            prev = r
            break
    if prev is None:
        return None
    den = abs(float(prev[field]))
    if den < 1e-12:
        return None
    return (float(latest[field]) - float(prev[field])) / den


def _latest_field(vis, field):
    annuals = [r for r in vis if int(r.get("quarter") or 0) == 4 and r.get(field) is not None]
    if not annuals:
        return None
    return float(annuals[-1][field])


def _roe_delta(vis):
    annuals = [r for r in vis if int(r.get("quarter") or 0) == 4 and r.get("roe") is not None]
    if not annuals:
        return None
    latest = annuals[-1]
    prev = None
    for r in reversed(annuals[:-1]):
        if int(r["year"]) == int(latest["year"]) - 1:
            prev = r
            break
    if prev is None:
        return None
    return float(latest["roe"]) - float(prev["roe"])


VALUE_FN = {
    "YOY_NET_PROFIT_ANNUAL": lambda vis: _yoy(vis, "net_profit"),
    "YOY_REVENUE_ANNUAL": lambda vis: _yoy(vis, "revenue"),
    "ROE_ANNUAL": lambda vis: _latest_field(vis, "roe"),
    "GPM_ANNUAL": lambda vis: _latest_field(vis, "gross_margin"),
    "NPM_ANNUAL": lambda vis: _latest_field(vis, "np_margin"),
    "ROE_DELTA_ANNUAL": _roe_delta,
}


def _by_symbol(rows):
    out = {}
    for r in rows:
        out.setdefault(r["symbol"], []).append(r)
    for sym in out:
        out[sym].sort(key=lambda r: (r.get("announcement_date") or "", r.get("report_period") or ""))
    return out


def fill_symbol_score(dates, recs, value_fn):
    t = len(dates)
    out = np.full(t, np.nan, dtype=np.float64)
    if not recs:
        return out
    events = sorted(set(r["announcement_date"] for r in recs if r.get("announcement_date")))
    for i, ad in enumerate(events):
        vis = [r for r in recs if r.get("announcement_date") <= ad]
        val = value_fn(vis)
        start = _date_start(dates, ad)
        if start is None or val is None:
            continue
        if i + 1 < len(events):
            end = _date_start(dates, events[i + 1])
            if end is None:
                end = t
        else:
            end = t
        out[start:end] = float(val)
    return out


def score_matrix(pack, rows, signal):
    fn = VALUE_FN[signal]
    dates = pack["dates"]
    symbols = pack["symbols"]
    by = _by_symbol(rows)
    scores = np.full((len(dates), len(symbols)), np.nan, dtype=np.float64)
    for j, sym in enumerate(symbols):
        scores[:, j] = fill_symbol_score(dates, by.get(sym) or [], fn)
    return scores


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
    }
    ev_r = int(checks["research_excess"]) + int(checks["research_rank_ic"])
    ev_v = int(checks["validation_excess"]) + int(checks["validation_rank_ic"])
    ok = (
        checks["research_mean_forward_net"]
        and checks["validation_mean_forward_net"]
        and checks["fdr"]
        and ev_r >= 2
        and ev_v >= 2
        and checks["research_capital"]
        and checks["validation_capital"]
    )
    checks["evidence_research"] = ev_r
    checks["evidence_validation"] = ev_v
    return ok, checks


def run_financial_alpha(rows, benches_ew=None):
    ensure_v16()
    contract = build_financial_contract()
    dump_json(os.path.join(OUT, "FINANCIAL_ALPHA_CONTRACT.json"), contract)
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    print("V16_ALPHA_EXEC", flush=True)
    xok = exec_ok_matrix(pack)
    elig = eligible(pack, 20)
    # EW bench for hold 20
    from research_engine.cn_a_share_alpha_v2.books import ew_overlapping

    ew = ew_overlapping(pack, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    recs = []
    for hyp in FIN_HYPOTHESES:
        print("V16_ALPHA", hyp["id"], "SCORE", flush=True)
        scores = score_matrix(pack, rows, hyp["signal"])
        pred = overlapping_predictive(pack, scores, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
        pred_r = _window_rows(pred, RESEARCH[0], RESEARCH[1])
        pred_v = _window_rows(pred, VALIDATION[0], VALIDATION[1])
        ic_r = ic_series(pack, scores, elig, RESEARCH[0], RESEARCH[1], HOLD_DAYS)
        ic_v = ic_series(pack, scores, elig, VALIDATION[0], VALIDATION[1], HOLD_DAYS)
        ex_r, et_r, ep_r = excess_mean(pred_r, ew)
        ex_v, et_v, ep_v = excess_mean(pred_v, ew)
        print("V16_ALPHA", hyp["id"], "CAPITAL", flush=True)
        cap_r = capital_book(pack, scores, elig, xok, RESEARCH[0], RESEARCH[1], HOLD_DAYS)
        cap_v = capital_book(pack, scores, elig, xok, VALIDATION[0], VALIDATION[1], HOLD_DAYS)
        cap_f = capital_book(pack, scores, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
        rec = {
            "id": hyp["id"],
            "family": hyp["family"],
            "signal": hyp["signal"],
            "mechanism": hyp["mechanism"],
            "predictive": {
                "research": dict(
                    summarize_predictive(pred_r),
                    excess_vs_b0=ex_r,
                    excess_t=et_r,
                    excess_p=ep_r,
                    rank_ic=float(np.mean(ic_r)) if ic_r else None,
                ),
                "validation": dict(
                    summarize_predictive(pred_v),
                    excess_vs_b0=ex_v,
                    excess_t=et_v,
                    excess_p=ep_v,
                    rank_ic=float(np.mean(ic_v)) if ic_v else None,
                ),
            },
            "capital": {
                "research": summarize_capital(cap_r, RESEARCH[0], HOLD_DAYS),
                "validation": summarize_capital(cap_v, VALIDATION[0], HOLD_DAYS),
                "full": summarize_capital(cap_f, RESEARCH[0], HOLD_DAYS),
            },
            "concentration": {
                "rebalance": share_of_top([tr["net_yuan"] for tr in cap_f["trades"]]),
            },
            "period_rets": dict((tr["signal_date"], tr["capital_ret"]) for tr in cap_f["trades"]),
            "pred_rets": dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in pred),
        }
        write_csv(
            os.path.join(EQUITY, "%s.csv" % hyp["id"]),
            ("signal_date", "exit", "capital_ret", "equity"),
            [{"signal_date": tr["signal_date"], "exit": tr["exit"], "capital_ret": tr["capital_ret"], "equity": tr["equity"]} for tr in cap_f["trades"]],
        )
        write_csv(os.path.join(TRADES, "%s.csv" % hyp["id"]), ("signal_date", "entry", "exit", "n_sel", "n_fill", "capital_ret", "net_yuan"), cap_f["trades"])
        print(
            "V16_ALPHA",
            hyp["id"],
            "PRED",
            rec["predictive"]["validation"].get("MEAN_FORWARD_RETURN"),
            "CAP_R",
            rec["capital"]["research"].get("total"),
            "CAP_V",
            rec["capital"]["validation"].get("total"),
            flush=True,
        )
        del scores
        recs.append(rec)
    legacy = _load_legacy_cluster()
    pvals = [onesided_p(r["predictive"]["validation"].get("excess_t"), r["predictive"]["validation"].get("excess_p")) for r in recs]
    fdr = fdr_from_pvals(pvals)
    candidates = []
    failures = []
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
        if ok and mx > SAME_CLUSTER_CORR:
            r["cluster_tag"] = "SAME_CLUSTER"
        elif ok:
            r["cluster_tag"] = "POTENTIALLY_INDEPENDENT"
        else:
            r["cluster_tag"] = None
        if ok:
            candidates.append(r)
        else:
            failures.append(
                {
                    "id": r["id"],
                    "family": r["family"],
                    "mechanism": r["mechanism"],
                    "why_failed": [k for k, v in checks.items() if v is False],
                    "reopen": "New contract only. Do not retune. Do not mix with H11/H12.",
                }
            )
        # cost stress only if level1
        if ok:
            print("V16_STRESS", r["id"], flush=True)
            scores = score_matrix(pack, rows, r["signal"])
            stress = {}
            for label, ck, sk in (("1x", 1.0, 1.0), ("1.5x", 1.5, 1.5), ("2x", 2.0, 2.0)):
                sim = capital_book(pack, scores, elig, xok, VALIDATION[0], VALIDATION[1], HOLD_DAYS, cost_k=ck, slip_k=sk)
                stress[label] = {"end": sim["end"], "total": sim["total"]}
            r["cost_stress"] = stress
            del scores
    slim = []
    for r in recs:
        slim.append(
            {
                "id": r["id"],
                "family": r["family"],
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
    dump_json(os.path.join(OUT, "FINANCIAL_RESULTS.json"), {"hypotheses": slim})
    dump_json(os.path.join(OUT, "FDR.json"), {"q": FDR_Q, "adjusted_p": fdr["adjusted_p"], "discoveries": fdr.get("discoveries")})
    dump_json(os.path.join(OUT, "FAILURES.json"), {"n": len(failures), "rows": failures})
    dump_json(
        os.path.join(OUT, "CANDIDATES.json"),
        {
            "n": len(candidates),
            "ids": [c["id"] for c in candidates],
            "tags": dict((c["id"], c.get("cluster_tag")) for c in candidates),
        },
    )
    return recs, candidates
