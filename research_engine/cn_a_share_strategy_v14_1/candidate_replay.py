"""Path A: original V13 overlapping_series. That is the Level 1 statistic."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_alpha.evaluate import cagr_from_h
from research_engine.cn_a_share_alpha.replay import overlapping_series
from research_engine.cn_a_share_strategy_v14_1 import HOLD_DAYS, RESEARCH, V13_PUBLISHED, VALIDATION


def replay_path_a(pack, family, lookback, start, end, scores, elig):
    return overlapping_series(pack, family, lookback, start, end, scores=scores, elig=elig)


def summarize_overlap(rows):
    if not rows:
        return {}
    nets = np.array([r["net"] for r in rows], dtype=np.float64)
    raws = np.array([r["raw"] for r in rows], dtype=np.float64)
    mean_net = float(np.mean(nets))
    return {
        "n": int(nets.size),
        "mean_raw": float(np.mean(raws)),
        "mean_net": mean_net,
        "mean_cost": float(np.mean(raws - nets)),
        "cagr_from_h": cagr_from_h(mean_net, 1.0),
        "definition": (
            "Each date t: equal-weight mean of filled open(t+1)->open(t+1+20) "
            "minus one round-trip cost. Reported CAGR is (1+mean_net_h)^(242/20)-1. "
            "The years argument is unused. This is not a compounded capital path."
        ),
    }


def vs_published(hyp_id, window, rec):
    pub = (V13_PUBLISHED.get(hyp_id) or {}).get(window) or {}
    got = rec.get("mean_net")
    exp = pub.get("mean_net_h")
    if got is None or exp is None:
        return {"ok": False, "abs_err": None}
    err = abs(got - exp)
    return {"ok": err < 1e-8, "abs_err": err, "got": got, "published": exp}


def phase_grids(rows, n_phase=HOLD_DAYS, key="net"):
    """Compound the chosen field on each 20-day offset. Diagnostic only."""
    out = []
    for off in range(n_phase):
        sub = rows[off::n_phase]
        eq = 1.0
        rets = []
        for r in sub:
            v = float(r[key])
            eq *= 1.0 + v
            rets.append(v)
        out.append(
            {
                "offset": off,
                "n": len(sub),
                "end": eq,
                "total": eq - 1.0,
                "mean": float(np.mean(rets)) if rets else None,
            }
        )
    ends = [g["end"] for g in out]
    return {
        "grids": out,
        "n_negative_grids": int(sum(1 for e in ends if e < 1.0)),
        "mean_grid_end": float(np.mean(ends)) if ends else None,
        "min_grid_end": float(np.min(ends)) if ends else None,
        "max_grid_end": float(np.max(ends)) if ends else None,
        "offset0_end": out[0]["end"] if out else None,
    }


def windows_path_a(pack, family, lookback, scores, elig):
    res = replay_path_a(pack, family, lookback, RESEARCH[0], RESEARCH[1], scores, elig)
    val = replay_path_a(pack, family, lookback, VALIDATION[0], VALIDATION[1], scores, elig)
    both = replay_path_a(pack, family, lookback, RESEARCH[0], VALIDATION[1], scores, elig)
    return {
        "research": {"rows": res, "summary": summarize_overlap(res)},
        "validation": {"rows": val, "summary": summarize_overlap(val)},
        "both": {"rows": both, "summary": summarize_overlap(both)},
        "grids_both": phase_grids(both),
    }
