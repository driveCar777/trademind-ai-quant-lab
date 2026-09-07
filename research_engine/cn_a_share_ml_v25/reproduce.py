"""V25.1 reproduction battery (pre-registered, fixed list, nothing is selected from it).

The primary configuration stays the V25 contract regardless of these numbers. Each variant re-fits the walk-forward model
with ONE nuisance parameter changed (seed / training stride / refit cadence) and re-reads the same books. Purpose: show
whether the Level-1 result is a property of the information or of one arbitrary schedule. Also computes the excess-series
independence test vs H11 (corr of excess-vs-EW series), which V25 recorded as a diagnostic.
Writes REPRODUCTION.json.
"""
from __future__ import print_function

import os
import time

import numpy as np

from research_engine.cn_a_share.io_util import dump_json
from research_engine.cn_a_share_alpha.evaluate import ttest_p
from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.cn_a_share_alpha_v2.books import capital_book, ew_overlapping, overlapping_predictive
from research_engine.cn_a_share_alpha_v2.evaluate import excess_mean
from research_engine.cn_a_share_alpha_v2.run import _window_rows
from research_engine.cn_a_share_ml_v25 import HEDGE_INDEX, HOLD_DAYS, OUT, RESEARCH, ROLLING_BLOCKS, VALIDATION
from research_engine.cn_a_share_ml_v25 import model as M
from research_engine.cn_a_share_ml_v25.features import load_features
from research_engine.cn_a_share_ml_v25.index_daily import load_open_series
from research_engine.cn_a_share_ml_v25.run import hedged_book
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix

VARIANTS = (
    {"id": "PRIMARY_AS_CONTRACT", "seed": None, "stride": None, "refit": None},
    {"id": "SEED_1", "seed": 1, "stride": None, "refit": None},
    {"id": "SEED_2", "seed": 2, "stride": None, "refit": None},
    {"id": "STRIDE_3", "seed": None, "stride": 3, "refit": None},
    {"id": "STRIDE_10", "seed": None, "stride": 10, "refit": None},
    {"id": "REFIT_60", "seed": None, "stride": None, "refit": 60},
    {"id": "REFIT_240", "seed": None, "stride": None, "refit": 240},
)


def _excess_series(pred, ewm):
    return dict((r["date"], r["MEAN_FORWARD_RETURN"] - ewm[r["date"]]) for r in pred if r["date"] in ewm)


def _corr(a, b):
    keys = sorted(set(a) & set(b))
    if len(keys) < 8:
        return None
    return float(np.corrcoef([a[k] for k in keys], [b[k] for k in keys])[0, 1])


def read_books(scores, pack, elig, xok, ew, ewm, idx_open, ex_h11):
    R, V, H = RESEARCH, VALIDATION, HOLD_DAYS
    pred = overlapping_predictive(pack, scores, elig, xok, R[0], V[1], H)
    ex_r = excess_mean(_window_rows(pred, R[0], R[1]), ew)
    ex_v = excess_mean(_window_rows(pred, V[0], V[1]), ew)
    lo_r = capital_book(pack, scores, elig, xok, R[0], R[1], H)
    lo_v = capital_book(pack, scores, elig, xok, V[0], V[1], H)
    hn_r = hedged_book(lo_r, pack["dates"], idx_open)
    hn_v = hedged_book(lo_v, pack["dates"], idx_open)
    roll = []
    for bid, b0, b1 in ROLLING_BLOCKS:
        e = excess_mean(_window_rows(pred, b0, b1), ew)
        roll.append({"block": bid, "excess": e[0], "t": e[1]})
    return {
        "excess_research": ex_r[0], "excess_research_t": ex_r[1], "excess_validation": ex_v[0], "excess_validation_t": ex_v[1],
        "LO20_research_total": lo_r["total"], "LO20_validation_total": lo_v["total"],
        "HN20_research_total": hn_r["total"], "HN20_validation_total": hn_v["total"],
        "rolling_positive": sum(1 for r in roll if r["excess"] is not None and r["excess"] > 0), "rolling": roll,
        "excess_corr_vs_H11": _corr(_excess_series(pred, ewm), ex_h11),
        "level1_shape": bool(ex_r[0] > 0 and ex_v[0] > 0 and hn_r["total"] > 0 and hn_v["total"] > 0 and lo_r["total"] > 0 and lo_v["total"] > 0),
    }


def main():
    pack = load_pack()
    feats = load_features()
    xok = exec_ok_matrix(pack)
    elig = eligible(pack, 20)
    ew = ew_overlapping(pack, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
    idx_open = load_open_series(HEDGE_INDEX, pack["dates"])
    h11 = np.array(feats["NEG_VOL_60"], dtype=np.float64)
    ex_h11 = _excess_series(overlapping_predictive(pack, h11, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS), ewm)
    base = {"seed": M.LGBM_PARAMS["random_state"], "stride": M.TRAIN_STRIDE, "refit": M.REFIT_EVERY}
    out = {"variants": [], "primary_stays": "V25 contract configuration; this battery selects nothing"}
    prev = os.path.join(OUT, "REPRODUCTION.json")
    done = {}
    if os.path.isfile(prev):
        import json
        with open(prev, "r", encoding="utf-8") as fh:
            done = dict((r["id"], r) for r in json.load(fh).get("variants", []))
    for v in VARIANTS:
        if v["id"] in done:
            out["variants"].append(done[v["id"]])
            continue
        t0 = time.time()
        M.LGBM_PARAMS["random_state"] = v["seed"] if v["seed"] is not None else base["seed"]
        M.TRAIN_STRIDE = v["stride"] if v["stride"] is not None else base["stride"]
        M.REFIT_EVERY = v["refit"] if v["refit"] is not None else base["refit"]
        if v["id"] == "PRIMARY_AS_CONTRACT" and os.path.isfile(os.path.join(OUT, "SCORES_ML1_LGBM.npy")):
            scores = np.load(os.path.join(OUT, "SCORES_ML1_LGBM.npy"))
        else:
            scores = M.build_scores(pack, feats, elig, xok)[0]["ML1_LGBM"]
        rec = dict(v)
        rec.update(read_books(scores, pack, elig, xok, ew, ewm, idx_open, ex_h11))
        rec["sec"] = round(time.time() - t0)
        out["variants"].append(rec)
        dump_json(os.path.join(OUT, "REPRODUCTION.json"), out)
        print("V25_REPRO", v["id"], "exc_r %.4f exc_v %.4f LO %.2f/%.2f HN %.2f/%.2f roll %d corrH11 %.3f L1 %s" % (
            rec["excess_research"], rec["excess_validation"], rec["LO20_research_total"], rec["LO20_validation_total"],
            rec["HN20_research_total"], rec["HN20_validation_total"], rec["rolling_positive"], rec["excess_corr_vs_H11"] or 0, rec["level1_shape"]), flush=True)
    M.LGBM_PARAMS["random_state"], M.TRAIN_STRIDE, M.REFIT_EVERY = base["seed"], base["stride"], base["refit"]
    # placebo: labels permuted within each session -> any remaining OOS excess would indicate a pipeline leak
    rng = np.random.RandomState(7)
    real_label = M._label_row

    def _shuffled(fwd_t, mask):
        y = real_label(fwd_t, mask)
        idx = np.where(np.isfinite(y))[0]
        y[idx] = y[rng.permutation(idx)]
        return y

    M._label_row = _shuffled
    t0 = time.time()
    scores = M.build_scores(pack, feats, elig, xok)[0]["ML1_LGBM"]
    M._label_row = real_label
    rec = {"id": "PLACEBO_SHUFFLED_LABELS", "seed": None, "stride": None, "refit": None}
    rec.update(read_books(scores, pack, elig, xok, ew, ewm, idx_open, ex_h11))
    rec["sec"] = round(time.time() - t0)
    out["placebo"] = rec
    print("V25_REPRO PLACEBO exc_r %.4f (t %.1f) exc_v %.4f (t %.1f) LO %.2f/%.2f roll %d" % (
        rec["excess_research"], rec["excess_research_t"] or 0, rec["excess_validation"], rec["excess_validation_t"] or 0,
        rec["LO20_research_total"], rec["LO20_validation_total"], rec["rolling_positive"]), flush=True)
    shapes = [r["level1_shape"] for r in out["variants"]]
    out["summary"] = {"n_variants": len(shapes), "n_level1_shape": int(sum(shapes)),
                      "validation_excess_min": min(r["excess_validation"] for r in out["variants"]),
                      "validation_excess_max": max(r["excess_validation"] for r in out["variants"]),
                      "HN20_validation_min": min(r["HN20_validation_total"] for r in out["variants"]),
                      "LO20_research_min": min(r["LO20_research_total"] for r in out["variants"]),
                      "excess_corr_vs_H11_max": max(abs(r["excess_corr_vs_H11"] or 0) for r in out["variants"])}
    dump_json(os.path.join(OUT, "REPRODUCTION.json"), out)
    print("V25_REPRO SUMMARY", out["summary"], flush=True)


if __name__ == "__main__":
    main()
