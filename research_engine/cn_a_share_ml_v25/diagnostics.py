"""Post-run read-only diagnostics for V25 (never gates, never changes RESULTS/DECISION).

1. Independence on EXCESS series: corr(ML1 excess-vs-EW, H11 excess-vs-EW) — the contract's cluster test compared raw
   MEAN_FORWARD_RETURN series, which any two long books share through the market; this strips it.
2. Size exposure: regress HN20 period returns on (EW eligible basket - HS300) over the same windows.
3. Cost stress on the gated candidate: LO20 validation at 1x / 1.5x / 2x stock costs.
4. Selection footprint: median amount-rank of selected names, breadth per period.
Writes DIAGNOSTICS_POST.json.
"""
from __future__ import print_function

import os

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.cn_a_share_alpha_v2.books import capital_book, ew_overlapping, overlapping_predictive
from research_engine.cn_a_share_alpha_v2.run import _load_legacy_cluster, _window_rows
from research_engine.cn_a_share_ml_v25 import HEDGE_INDEX, HOLD_DAYS, OUT, RESEARCH, VALIDATION
from research_engine.cn_a_share_ml_v25.features import load_features
from research_engine.cn_a_share_ml_v25.index_daily import load_open_series
from research_engine.cn_a_share_ml_v25.run import hedged_book
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix, pick_lexsort


def _corr(a, b):
    keys = sorted(set(a) & set(b))
    if len(keys) < 8:
        return None, len(keys)
    x = np.array([a[k] for k in keys])
    y = np.array([b[k] for k in keys])
    return float(np.corrcoef(x, y)[0, 1]), len(keys)


def main():
    pack = load_pack()
    dates = pack["dates"]
    dix = dict((d, i) for i, d in enumerate(dates))
    xok = exec_ok_matrix(pack)
    elig = eligible(pack, 20)
    ml1 = np.load(os.path.join(OUT, "SCORES_ML1_LGBM.npy"))
    feats = load_features()
    ew = ew_overlapping(pack, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
    out = {}

    # 1. excess-series independence
    pred_ml1 = overlapping_predictive(pack, ml1, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    ex_ml1 = dict((r["date"], r["MEAN_FORWARD_RETURN"] - ewm[r["date"]]) for r in pred_ml1 if r["date"] in ewm)
    legacy = _load_legacy_cluster()
    h11 = np.array(feats["NEG_VOL_60"], dtype=np.float64)
    pred_h11 = overlapping_predictive(pack, h11, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    ex_h11 = dict((r["date"], r["MEAN_FORWARD_RETURN"] - ewm[r["date"]]) for r in pred_h11 if r["date"] in ewm)
    raw_ml1 = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in pred_ml1)
    raw_h11 = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in pred_h11)
    c_raw, n_raw = _corr(raw_ml1, raw_h11)
    c_ex, n_ex = _corr(ex_ml1, ex_h11)
    c_raw_leg, n_leg = _corr(raw_ml1, legacy["H11_VOL_60"]["predictive"])
    c_ew_h11, _ = _corr(raw_h11, ewm)
    c_ew_ml1, _ = _corr(raw_ml1, ewm)
    out["independence"] = {
        "contract_test_raw_MF_corr_vs_H11_recomputed": c_raw, "n": n_raw,
        "contract_test_raw_MF_corr_vs_H11_legacy_file": c_raw_leg, "n_legacy": n_leg,
        "raw_MF_corr_H11_vs_EW": c_ew_h11, "raw_MF_corr_ML1_vs_EW": c_ew_ml1,
        "EXCESS_series_corr_ML1_vs_H11": c_ex, "n_excess": n_ex,
        "reading": "raw MF series of any long quintile co-move with the market; the excess-series correlation is the informative one",
    }

    # 2. size exposure of HN20 and contribution of EW-vs-HS300 spread
    idx_open = load_open_series(HEDGE_INDEX, dates)
    lo_f = capital_book(pack, ml1, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    hn_f = hedged_book(lo_f, dates, idx_open)
    xs, ys, ys_lo, spread_only = [], [], [], []
    for tr in hn_f["trades"]:
        i0, i1 = dix[tr["entry"]], dix[tr["exit"]]
        js = np.where(elig[dix[tr["signal_date"]]])[0]
        a = np.array(pack["open"][i0, js], dtype=np.float64)
        b = np.array(pack["open"][i1, js], dtype=np.float64)
        g = np.isfinite(a) & np.isfinite(b) & (a > 0)
        ew_ret = float(np.mean(b[g] / a[g] - 1.0))
        spread = ew_ret - tr["idx_ret"]
        xs.append(spread)
        ys.append(tr["capital_ret"])
        ys_lo.append(tr["lo_ret"] - ew_ret)
    xs, ys, ys_lo = np.array(xs), np.array(ys), np.array(ys_lo)
    beta = float(np.polyfit(xs, ys, 1)[0])
    alpha_p = float(np.mean(ys) - beta * np.mean(xs))
    r2 = float(np.corrcoef(xs, ys)[0, 1] ** 2)
    out["size_exposure_HN20"] = {
        "n_periods": int(xs.size), "beta_to_EW_minus_HS300": beta, "r2": r2,
        "mean_period_ret_HN20": float(np.mean(ys)), "alpha_per_period_after_spread": alpha_p,
        "mean_EW_minus_HS300_spread_per_period": float(np.mean(xs)),
        "LO20_minus_EW_basket_per_period_mean": float(np.mean(ys_lo)), "LO20_minus_EW_basket_t": float(np.mean(ys_lo) / (np.std(ys_lo, ddof=1) / np.sqrt(ys_lo.size))),
        "LO20_minus_EW_basket_share_positive": float(np.mean(ys_lo > 0)),
        "reading": "HN20 hedges HS300, so it carries the small-vs-large spread; LO20 minus the eligible EW basket is the stock-selection-only read",
    }
    yearly = {}
    for tr, s in zip(hn_f["trades"], ys_lo):
        y = tr["signal_date"][:4]
        yearly.setdefault(y, []).append(s)
    out["LO20_minus_EW_by_year"] = dict((y, {"n": len(v), "compound": float(np.prod(1 + np.array(v)) - 1), "mean": float(np.mean(v))}) for y, v in sorted(yearly.items()))

    # 3. cost stress LO20 validation
    stress = {}
    for label, ck, sk in (("1x", 1.0, 1.0), ("1.5x", 1.5, 1.5), ("2x", 2.0, 2.0)):
        sim = capital_book(pack, ml1, elig, xok, VALIDATION[0], VALIDATION[1], HOLD_DAYS, cost_k=ck, slip_k=sk)
        simr = capital_book(pack, ml1, elig, xok, RESEARCH[0], RESEARCH[1], HOLD_DAYS, cost_k=ck, slip_k=sk)
        stress[label] = {"validation_total": sim["total"], "research_total": simr["total"]}
    out["cost_stress_LO20"] = stress

    # 4. selection footprint
    amt = feats["NEG_LOG_AMT_20"]
    ranks, breadth = [], []
    for tr in lo_f["trades"][::3]:
        t = dix[tr["signal_date"]]
        js = pick_lexsort(np.array(ml1[t], dtype=np.float64), elig[t])
        if js is None:
            continue
        x = np.array(amt[t], dtype=np.float64)
        m = elig[t] & np.isfinite(x)
        order = np.argsort(np.argsort(x[m]))
        pos = dict(zip(np.where(m)[0], order / float(max(1, m.sum() - 1))))
        ranks.append(float(np.median([pos.get(int(j), np.nan) for j in js])))
        breadth.append(int(js.size))
    out["selection_footprint"] = {"median_NEG_LOG_AMT_rank_of_selected(1=smallest_amount)": float(np.nanmedian(ranks)),
                                  "median_names_per_period": float(np.median(breadth)),
                                  "reading": "close to 1 means the model is mostly buying the lowest-turnover-value names (size/illiquidity tilt)"}
    dump_json(os.path.join(OUT, "DIAGNOSTICS_POST.json"), out)
    print("V25_DIAG", out["independence"], flush=True)
    print("V25_DIAG size", out["size_exposure_HN20"], flush=True)
    print("V25_DIAG stress", stress, flush=True)
    print("V25_DIAG footprint", out["selection_footprint"], flush=True)
    return out


if __name__ == "__main__":
    main()
