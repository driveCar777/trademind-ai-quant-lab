"""V28 — ML1 single Final OOS read on the denied window (2024-03-01 .. 2026-08-28).

Protocol: docs/research_engine/V28_ML1_FINAL_OOS_PROTOCOL.md (written before this ran). Runs once: refuses if FINAL_OOS_READ.json exists.

Gate scores  = V26 operating policy: expanding walk-forward, refit every 240 sessions from FIRST_PRED through the denied end
               (the REFIT_240 nuisance variant of V25.1), embargo 21, stride 5. No lookahead: each refit trains on labels
               fully known before the refit date.
Diag scores  = the official V25 frozen model (last refit 2021-05-25) scoring the denied window unchanged.
Books        = LO20 legacy (A_SHARE_STRATEGY_COST_MODEL_V1), eligible EW, overlapping predictive excess. Nothing tuned.
"""
from __future__ import print_function

import json
import os
import sys
import time

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha.pack import load_pack
from research_engine.cn_a_share_alpha_v2.books import capital_book, ew_overlapping, overlapping_predictive
from research_engine.cn_a_share_alpha_v2.evaluate import excess_mean, summarize_capital, summarize_predictive
from research_engine.cn_a_share_alpha_v2.run import _window_rows
from research_engine.cn_a_share_macro_v17.evaluate import _finite, _json_safe
from research_engine.cn_a_share_ml_v25 import DENIED, EMBARGO, FEAT_CACHE, FIRST_PRED, HOLD_DAYS, LGBM_PARAMS, OUT, RESEARCH, ROOT, TRAIN_STRIDE, VALIDATION
from research_engine.cn_a_share_ml_v25.features import NAMES, build_features, ranked_row
from research_engine.cn_a_share_ml_v25.model import _first_at_or_after, _label_row, _last_at_or_before, forward_open_matrix
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix
from research_protocol.hashing import canonical_hash

TAG = "V28_FINAL_OOS"
LIVE_REFIT = 240
FROZEN_CACHE = os.path.join(ROOT, "data", "market", "cn_a_share", "alpha_cache", "v25_features")
READ_PATH = os.path.join(OUT, "FINAL_OOS_READ.json")
PROTO_PATH = os.path.join(OUT, "FINAL_OOS_PROTOCOL.json")
RETIRE_CONSECUTIVE = 24


def protocol():
    p = {
        "id": "V28_ML1_FINAL_OOS_SINGLE_READ",
        "signal": "ML1_LGBM_STACK",
        "features": list(NAMES),
        "gate_scores": {"policy": "V26 live policy", "refit_every_sessions": LIVE_REFIT, "embargo": EMBARGO, "stride": TRAIN_STRIDE,
                        "first_pred": FIRST_PRED, "expanding": True, "walks_through": DENIED[1]},
        "diag_scores": {"policy": "V25 official frozen model (last refit 2021-05-25) applied to the denied window", "gated": False},
        "params": LGBM_PARAMS,
        "book": "LO20 legacy, A_SHARE_STRATEGY_COST_MODEL_V1, hold %d, top 20%% EW" % HOLD_DAYS,
        "benchmark": "eligible EW overlapping",
        "window": list(DENIED),
        "gates": {"G1": "mean predictive excess vs EW > 0", "G2": "LO20 capital total > 0 after cost",
                  "G3": "no %d consecutive periods with LO-EW <= 0 (V26 retire rule)" % RETIRE_CONSECUTIVE},
        "labels": {"G1&G2&G3": "FINAL_OOS_PASS", "G1&!G2": "FINAL_OOS_EXCESS_ONLY", "!G1": "FINAL_OOS_FAIL"},
        "single_read": True, "no_tuning_after": True, "authorised_by": "user 2026-09-04 21:07 (delegated)",
    }
    p["protocol_hash"] = canonical_hash(p)
    return p


def _assert_frozen_identical(feats, dates):
    """Extended features must equal the frozen V25 cache bit-for-bit up to VALIDATION[1] (PIT sanity)."""
    i1 = _last_at_or_before(dates, VALIDATION[1])
    report = {}
    for n in NAMES:
        a = np.load(os.path.join(FROZEN_CACHE, n + ".npy"))[: i1 + 1]
        b = np.array(feats[n])[: i1 + 1]
        same = np.array_equal(np.isfinite(a), np.isfinite(b)) and np.allclose(np.nan_to_num(a), np.nan_to_num(b), rtol=0, atol=1e-6)
        report[n] = bool(same)
        if not same:
            diff = np.nanmax(np.abs(np.nan_to_num(a) - np.nan_to_num(b)))
            print(TAG, "FEATURE_DIFF", n, "max abs diff %.3g" % diff, flush=True)
    return report


def gate_scores(pack, feats, elig, xok, i_end):
    import lightgbm as lgb

    dates = pack["dates"]
    T, N = len(dates), len(pack["symbols"])
    i_first = _first_at_or_after(dates, FIRST_PRED)
    i_res_start = _first_at_or_after(dates, RESEARCH[0])
    fwd = forward_open_matrix(pack, HOLD_DAYS, i_end)
    grid = [t for t in range(i_res_start, i_end - EMBARGO + 1) if (t - i_res_start) % TRAIN_STRIDE == 0]
    Xs, ys = {}, {}
    for t in grid:
        mask = elig[t] & np.isfinite(fwd[t]) & xok[t + 1]
        if int(mask.sum()) < 100:
            continue
        X = ranked_row(feats, t, mask)
        y = _label_row(fwd[t], mask)
        keep = mask & np.isfinite(y)
        Xs[t], ys[t] = X[keep], y[keep]
    refits = list(range(i_first, i_end + 1, LIVE_REFIT))
    out = np.full((T, N), np.nan, dtype=np.float32)
    meta = []
    np.seterr(invalid="ignore")
    for k, s in enumerate(refits):
        t0 = time.time()
        cutoff = s - EMBARGO
        tr = [t for t in grid if t <= cutoff and t in Xs]
        X = np.concatenate([Xs[t] for t in tr], axis=0)
        y = np.concatenate([ys[t] for t in tr], axis=0)
        model = lgb.LGBMRegressor(**LGBM_PARAMS)
        model.fit(X, y)
        s_end = refits[k + 1] - 1 if k + 1 < len(refits) else i_end
        for t in range(s, s_end + 1):
            mask = elig[t]
            if int(mask.sum()) < 100:
                continue
            Xt = ranked_row(feats, t, mask)
            rows = np.where(mask)[0]
            out[t, rows] = model.predict(Xt[rows]).astype(np.float32)
        meta.append({"fit_at": dates[s], "train_rows": int(X.shape[0]), "train_last_label_session": dates[cutoff], "scores_until": dates[s_end],
                     "sec": round(time.time() - t0, 1)})
        print(TAG, "gate refit", k + 1, "/", len(refits), dates[s], "rows", X.shape[0], "->", dates[s_end], flush=True)
    return out, meta


def diag_scores_frozen(pack, feats, elig, xok, i_start, i_end):
    """Re-fit the V25 official final model exactly (same training set: research grid, refit 120 schedule's last fit at 2021-05-25)
    then score the denied window. Equivalent to loading the frozen model; V25 did not pickle it, so we rebuild deterministically."""
    import lightgbm as lgb

    from research_engine.cn_a_share_ml_v25 import REFIT_EVERY

    dates = pack["dates"]
    T, N = len(dates), len(pack["symbols"])
    i_first = _first_at_or_after(dates, FIRST_PRED)
    i_res_start = _first_at_or_after(dates, RESEARCH[0])
    i_res_end = _last_at_or_before(dates, RESEARCH[1])
    fwd = forward_open_matrix(pack, HOLD_DAYS, i_res_end)
    grid = [t for t in range(i_res_start, i_res_end - EMBARGO + 1) if (t - i_res_start) % TRAIN_STRIDE == 0]
    last_fit = list(range(i_first, i_res_end + 1, REFIT_EVERY))[-1]
    cutoff = last_fit - EMBARGO
    Xs, ys = [], []
    for t in grid:
        if t > cutoff:
            break
        mask = elig[t] & np.isfinite(fwd[t]) & xok[t + 1]  # identical to V25 build_scores
        if int(mask.sum()) < 100:
            continue
        X = ranked_row(feats, t, mask)
        y = _label_row(fwd[t], mask)
        keep = mask & np.isfinite(y)
        Xs.append(X[keep])
        ys.append(y[keep])
    model = lgb.LGBMRegressor(**LGBM_PARAMS)
    model.fit(np.concatenate(Xs), np.concatenate(ys))
    out = np.full((T, N), np.nan, dtype=np.float32)
    for t in range(i_start, i_end + 1):
        mask = elig[t]
        if int(mask.sum()) < 100:
            continue
        Xt = ranked_row(feats, t, mask)
        rows = np.where(mask)[0]
        out[t, rows] = model.predict(Xt[rows]).astype(np.float32)
    return out, {"fit_at": dates[last_fit], "train_last_label_session": dates[cutoff], "train_rows": int(sum(len(y) for y in ys))}


def read_window(tag, scores, pack, elig, xok, ew, ewm):
    pred = overlapping_predictive(pack, scores, elig, xok, DENIED[0], DENIED[1], HOLD_DAYS)
    ex, et, ep = excess_mean(pred, ew)
    lo = capital_book(pack, scores, elig, xok, DENIED[0], DENIED[1], HOLD_DAYS)
    exs = [(r["date"], r["MEAN_FORWARD_RETURN"] - ewm[r["date"]]) for r in pred if r["date"] in ewm]
    # V26 retire rule on non-overlapping LO periods vs EW over the same period
    per = []
    for tr in lo["trades"]:
        d = tr["signal_date"]
        per.append({"signal_date": d, "capital_ret": tr["capital_ret"], "ew_20d": ewm.get(d), "lo_minus_ew": (tr["capital_ret"] - ewm[d]) if d in ewm else None})
    worst_run, run = 0, 0
    for p in per:
        if p["lo_minus_ew"] is not None and p["lo_minus_ew"] <= 0:
            run += 1
            worst_run = max(worst_run, run)
        else:
            run = 0
    yearly = {}
    for tr in lo["trades"]:
        y = tr["signal_date"][:4]
        yearly[y] = yearly.get(y, 1.0) * (1.0 + tr["capital_ret"])
    yearly = dict((k, round(v - 1.0, 4)) for k, v in yearly.items())
    write_csv(os.path.join(OUT, "EQUITY", "FINAL_OOS_%s_LO20.csv" % tag), ("signal_date", "exit", "capital_ret", "equity"),
              [{"signal_date": t["signal_date"], "exit": t["exit"], "capital_ret": t["capital_ret"], "equity": t["equity"]} for t in lo["trades"]])
    write_csv(os.path.join(OUT, "TRADES", "FINAL_OOS_%s_LO20.csv" % tag), ("signal_date", "entry", "exit", "n_sel", "n_fill", "capital_ret", "net_yuan", "equity"), lo["trades"])
    cap = summarize_capital(lo, DENIED[0], HOLD_DAYS)
    rec = {"predictive": dict(summarize_predictive(pred), excess_vs_b0=_finite(ex), excess_t=_finite(et), excess_p=_finite(ep), n=len(pred)),
           "capital_LO20": cap, "yearly_LO20": yearly, "periods": per, "n_periods": len(per),
           "n_periods_lo_minus_ew_positive": sum(1 for p in per if (p["lo_minus_ew"] or 0) > 0),
           "worst_consecutive_lo_le_ew": worst_run, "excess_series_n": len(exs)}
    print(TAG, tag, "EXC %.5f t %.2f | LO20 total %.4f maxdd %s | periods %d pos-vs-EW %d worst-run %d" % (
        ex or 0, et or 0, cap.get("total") or 0, cap.get("maxdd"), len(per), rec["n_periods_lo_minus_ew_positive"], worst_run), flush=True)
    return rec


def main():
    if os.path.isfile(READ_PATH):
        print(TAG, "REFUSED: FINAL_OOS_READ.json exists. Single read already consumed.", flush=True)
        return 2
    if os.path.abspath(FEAT_CACHE) == os.path.abspath(FROZEN_CACHE):
        raise RuntimeError("SET TRADEMIND_V25_FEAT_CACHE to a separate directory; the frozen V25 cache must not be overwritten")
    proto = protocol()
    dump_json(PROTO_PATH, proto)
    print(TAG, "protocol", proto["protocol_hash"][:12], flush=True)
    pack = load_pack()
    dates = pack["dates"]
    i_end = _last_at_or_before(dates, DENIED[1]) - HOLD_DAYS - 1  # last signal whose exit is inside the pack
    i_start = _first_at_or_after(dates, DENIED[0])
    feats = build_features(pack, force=True)
    frozen_ok = _assert_frozen_identical(feats, dates)
    cover = dict((n, float(np.isfinite(feats[n][i_end]).mean())) for n in NAMES)
    print(TAG, "features identical to frozen cache up to validation end:", all(frozen_ok.values()), flush=True)
    xok = exec_ok_matrix(pack)
    elig = eligible(pack, 20)
    ew = ew_overlapping(pack, elig, xok, DENIED[0], DENIED[1], HOLD_DAYS)
    ewm = dict((r["date"], r["MEAN_FORWARD_RETURN"]) for r in ew)
    ew_mean = float(np.mean([r["MEAN_FORWARD_RETURN"] for r in ew])) if ew else None

    g_scores, g_meta = gate_scores(pack, feats, elig, xok, i_end)
    np.save(os.path.join(OUT, "SCORES_FINAL_OOS_GATE_REFIT240.npy"), g_scores)
    gate = read_window("GATE_REFIT240", g_scores, pack, elig, xok, ew, ewm)
    d_scores, d_meta = diag_scores_frozen(pack, feats, elig, xok, i_start, i_end)
    np.save(os.path.join(OUT, "SCORES_FINAL_OOS_DIAG_FROZEN2021.npy"), d_scores)
    diag = read_window("DIAG_FROZEN2021", d_scores, pack, elig, xok, ew, ewm)

    g1 = bool((gate["predictive"]["excess_vs_b0"] or 0) > 0)
    g2 = bool((gate["capital_LO20"].get("total") or 0) > 0)
    g3 = bool(gate["worst_consecutive_lo_le_ew"] < RETIRE_CONSECUTIVE)
    label = "FINAL_OOS_PASS" if (g1 and g2 and g3) else ("FINAL_OOS_EXCESS_ONLY" if g1 else "FINAL_OOS_FAIL")
    if g1 and g2 and not g3:
        label = "FINAL_OOS_EXCESS_ONLY_RETIRE_RULE_HIT"
    read = {
        "id": proto["id"], "protocol_hash": proto["protocol_hash"], "read_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "window": {"first_signal": dates[i_start], "last_signal": dates[i_end], "pack_end": dates[-1]},
        "features_identical_to_frozen_cache_until_validation_end": frozen_ok, "feature_coverage_last_signal": cover,
        "ew_mean_forward_20d": ew_mean, "gates": {"G1_excess_positive": g1, "G2_capital_positive": g2, "G3_no_retire_trigger": g3},
        "label": label, "gate_book": gate, "diag_frozen2021": diag, "gate_refits": g_meta, "diag_fit": d_meta,
        "single_read_consumed": True, "next_read_allowed": False,
        "post_read_rules": "no feature/param/hold/cost/refit change; no variant selection on this window; Paper is a separate human gate",
    }
    for k in ("gate_book", "diag_frozen2021"):
        read[k] = dict(read[k])
    dump_json(READ_PATH, _json_safe(read))
    print(TAG, "LABEL", label, "G1", g1, "G2", g2, "G3", g3, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
