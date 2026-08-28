"""Locked candidate list. Changing this is a new search-space version."""
from __future__ import print_function

from research_engine.discovery import DISCOVERY_BOOT, DISCOVERY_FDR_Q, DISCOVERY_ID, DISCOVERY_PERM, DISCOVERY_SEED
from research_protocol.hashing import canonical_hash


def _c(family, name, kind, params, side, target="future_return", horizon=1, timeframes=None, volume_type=None, combo=False):
    row = {
        "family_id": family,
        "name": name,
        "kind": kind,
        "params": params,
        "side": side,
        "target": target,
        "horizon": horizon,
        "timeframes": timeframes or ["M15", "H1", "H4", "D1"],
        "causal": True,
        "combo": combo,
    }
    if volume_type:
        row["volume_type"] = volume_type
    row["candidate_id"] = "FD-V01-%s-%s-H%s-%s" % (family.split("-")[-1], name, horizon, target)
    return row


def build_candidates():
    out = []
    # A Momentum
    for n in (1, 3, 5, 8, 10, 20):
        out.append(_c("FAM-FD-MOMENTUM-0001", "RET_%s_HIGH" % n, "ret", {"n": n}, "high"))
    for n in (3, 5, 8):
        out.append(_c("FAM-FD-MOMENTUM-0001", "SIGNCONS_%s" % n, "sign_cons", {"n": n}, "high"))
    out.append(_c("FAM-FD-MOMENTUM-0001", "ACCEL_5_20", "accel", {"short": 5, "long": 20}, "high"))
    out.append(_c("FAM-FD-MOMENTUM-0001", "RET_5_HIGH_H3", "ret", {"n": 5}, "high", horizon=3))
    # B Reversal
    for n in (10, 20, 40):
        out.append(_c("FAM-FD-REVERSAL-0001", "DISTMEAN_%s_HIGH" % n, "dist_mean", {"n": n}, "high"))
        out.append(_c("FAM-FD-REVERSAL-0001", "RANGEPOS_%s_HIGH" % n, "range_pos", {"n": n}, "high"))
        out.append(_c("FAM-FD-REVERSAL-0001", "RANGEPOS_%s_LOW" % n, "range_pos", {"n": n}, "low"))
    out.append(_c("FAM-FD-REVERSAL-0001", "ZDIST_20_HIGH", "z_dist", {"n": 20}, "high"))
    out.append(_c("FAM-FD-REVERSAL-0001", "CLOSELOC_20_HIGH", "close_loc", {"n": 20}, "high"))
    out.append(_c("FAM-FD-REVERSAL-0001", "EXTREME_ABSRET", "abs_ret", {"n": 1}, "high"))
    out.append(_c("FAM-FD-REVERSAL-0001", "DISTMEAN_20_HIGH_H3", "dist_mean", {"n": 20}, "high", horizon=3))
    # C Volatility
    for n in (10, 20):
        out.append(_c("FAM-FD-VOL-0001", "RANGE_%s_HIGH_RET" % n, "roll_range", {"n": n}, "high", "future_return"))
        out.append(_c("FAM-FD-VOL-0001", "RANGE_%s_HIGH_ABS" % n, "roll_range", {"n": n}, "high", "future_abs_return"))
        out.append(_c("FAM-FD-VOL-0001", "RANGE_%s_LOW_ABS" % n, "roll_range", {"n": n}, "low", "future_abs_return"))
    out.append(_c("FAM-FD-VOL-0001", "TR_14_HIGH_ABS", "tr_like", {"n": 14}, "high", "future_abs_return"))
    out.append(_c("FAM-FD-VOL-0001", "VOLRATIO_5_20_HIGH", "vol_ratio", {"short": 5, "long": 20}, "high", "future_abs_return"))
    out.append(_c("FAM-FD-VOL-0001", "VOLRATIO_5_20_LOW", "vol_ratio", {"short": 5, "long": 20}, "low", "future_abs_return"))
    # D Breakout / range
    for n in (20, 40):
        out.append(_c("FAM-FD-BREAKOUT-0001", "DISTHIGH_%s" % n, "dist_high", {"n": n}, "high"))
        out.append(_c("FAM-FD-BREAKOUT-0001", "DISTLOW_%s" % n, "dist_low", {"n": n}, "high"))
    out.append(_c("FAM-FD-BREAKOUT-0001", "NEARHIGH_20", "dist_high", {"n": 20}, "low"))
    out.append(_c("FAM-FD-BREAKOUT-0001", "NEARLOW_20", "dist_low", {"n": 20}, "low"))
    # E Efficiency
    for n in (10, 20, 40):
        out.append(_c("FAM-FD-EFFICIENCY-0001", "EFF_%s_HIGH" % n, "efficiency", {"n": n}, "high"))
        out.append(_c("FAM-FD-EFFICIENCY-0001", "EFF_%s_LOW" % n, "efficiency", {"n": n}, "low"))
    # F tick volume
    out.append(_c("FAM-FD-VOLUME-0001", "TVZ_20_HIGH", "tickvol_z", {"n": 20}, "high", volume_type="tick_volume"))
    out.append(_c("FAM-FD-VOLUME-0001", "TVZ_20_LOW", "tickvol_z", {"n": 20}, "low", volume_type="tick_volume"))
    out.append(_c("FAM-FD-VOLUME-0001", "TVRATIO_5_20_HIGH", "tickvol_ratio", {"short": 5, "long": 20}, "high", volume_type="tick_volume"))
    out.append(_c("FAM-FD-VOLUME-0001", "PV_ALIGN", "pv_align", {"n": 5}, "high", volume_type="tick_volume"))
    # G spread
    out.append(_c("FAM-FD-SPREAD-0001", "SPREADZ_HIGH", "spread_z", {"n": 20}, "high"))
    out.append(_c("FAM-FD-SPREAD-0001", "SPREADZ_LOW", "spread_z", {"n": 20}, "low"))
    out.append(_c("FAM-FD-SPREAD-0001", "RET5_HIGH_IN_LOW_SPREAD", "combo_ret_spread", {"n": 5, "spread_n": 20}, "high", combo=True))
    # H MTF (M15 only; HTF from already-closed M15 groups of 4)
    out.append(_c("FAM-FD-MTF-0001", "HTF_RET_HIGH", "htf_ret", {"group": 4}, "high", timeframes=["M15"]))
    out.append(_c("FAM-FD-MTF-0001", "M15RET5_AND_HTF", "combo_m15_htf", {"n": 5, "group": 4}, "high", timeframes=["M15"], combo=True))
    out.append(_c("FAM-FD-MTF-0001", "M15REV_IN_HTF", "combo_m15rev_htf", {"n": 5, "group": 4}, "high", timeframes=["M15"], combo=True))
    # limited combos
    out.append(_c("FAM-FD-COMBO-0001", "MOM5_AND_VOLHIGH", "combo_ret_range", {"n": 5, "range_n": 20}, "high", combo=True))
    out.append(_c("FAM-FD-COMBO-0001", "EFF20_AND_NEARHIGH", "combo_eff_nearhigh", {"eff_n": 20, "high_n": 20}, "high", combo=True))
    seen = {}
    uniq = []
    for row in out:
        if row["candidate_id"] in seen:
            raise ValueError("duplicate %s" % row["candidate_id"])
        seen[row["candidate_id"]] = True
        uniq.append(row)
    return uniq


def build_search_space():
    candidates = build_candidates()
    families = []
    for row in candidates:
        if row["family_id"] not in families:
            families.append(row["family_id"])
    body = {
        "discovery_id": DISCOVERY_ID,
        "version": "0.1",
        "seed": DISCOVERY_SEED,
        "bootstrap_iterations": DISCOVERY_BOOT,
        "permutation_iterations": DISCOVERY_PERM,
        "fdr_q": DISCOVERY_FDR_Q,
        "cost_model": "RAW_SPREAD_OVER_CLOSE_SCREEN_ONLY",
        "execution_model": "NONE_PREDICTIVE_NOT_TRADE",
        "FINAL_OOS_ACCESS": "DENIED",
        "families": families,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "reserved_not_computed": [
            {"family_id": "FAM-FD-XASSET-0001", "status": "DRAFT", "reason": "needs aligned cross-file timestamps"},
            {"family_id": "FAM-FD-NEWS-0001", "status": "DRAFT", "reason": "no live news API this version"},
        ],
        "note": "Screening contract. Not HYP-0001. Not a strategy.",
    }
    body["search_space_hash"] = canonical_hash(_hash_body(body))
    return body


def _hash_body(payload):
    body = dict(payload)
    body.pop("search_space_hash", None)
    return body


def applicable_candidates(space, timeframe):
    rows = []
    for row in space.get("candidates") or []:
        allowed = row.get("timeframes") or []
        if timeframe in allowed:
            rows.append(row)
    return rows
