"""A-Short forensic / observability layer (Phase 3).

A THIN, read-only persistence + derivation layer over the existing baseline outputs. It explains WHY a
result happened (data / model / execution / cost / env) and makes every run reproducible via a
`runs/<RUN_ID>/` bundle. It NEVER changes alpha/baseline/contract/universe/cost, and NEVER raises into
the caller: on any internal failure it returns FORENSIC_STATUS=DEGRADED.
"""
from __future__ import print_function

import json
import os

from research_engine.cn_a_short.forensic import attribution as _attr
from research_engine.cn_a_short.forensic import errors as _errors
from research_engine.cn_a_short.forensic import lifecycle as _lifecycle
from research_engine.cn_a_short.forensic import report as _report
from research_engine.cn_a_short.forensic import run_manifest as _manifest
from research_engine.cn_a_short.forensic import snapshots as _snapshots


def _write(path, obj):
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=2, default=str)


def _trades_from_periods(period_samples):
    trades = []
    for per in (period_samples or []):
        sd = per.get("signal_date")
        for n in per.get("names", []):
            trades.append({"symbol": n.get("symbol"), "net": n.get("net"), "entered": bool(n.get("entered")),
                           "status": n.get("status"), "signal_date": sd,
                           "planned_exit": n.get("planned_exit"), "actual_exit": n.get("actual_exit")})
    return trades


def _ledger_from_periods(period_samples):
    inv = sum((per.get("invested") or 0.0) for per in (period_samples or []))
    cash_out = sum((per.get("cash_out_incl_fees") or 0.0) for per in (period_samples or []))
    pnl = sum((per.get("pnl") or 0.0) for per in (period_samples or []))
    neg = [per.get("signal_date") for per in (period_samples or [])
           if isinstance(per.get("cash_out_incl_fees"), (int, float)) and isinstance(per.get("equity_ref"), (int, float))
           and per["cash_out_incl_fees"] > per["equity_ref"] + 1e-6]
    return {"total_invested": round(inv, 2), "total_cash_out_incl_fees": round(cash_out, 2),
            "total_pnl": round(pnl, 2), "negative_cash_periods": neg,
            "no_negative_cash": len(neg) == 0}


def run_forensic(experiment, config, status, out_root, derived_dataset_hash=None, pack=None, elig=None,
                 asof_index=None, coverage=None, evaluate_result=None, signals=None, period_samples=None,
                 exception=None):
    """Write a runs/<RUN_ID>/ forensic bundle. Returns {forensic_status, run_id, run_dir, manifest_hash}.

    `evaluate_result` = {hold: {k: per_k_summary}} (baseline.evaluate output, optional).
    `period_samples`  = list of top_k_period result dicts (optional, for lifecycle/trades).
    Never raises: internal errors -> FORENSIC_STATUS=DEGRADED.
    """
    try:
        manifest, mhash = _manifest.build_manifest(experiment, config, derived_dataset_hash, status)
        run_dir = os.path.join(out_root, "runs", manifest["run_id"])
        if not os.path.isdir(run_dir):
            os.makedirs(run_dir)

        _write(os.path.join(run_dir, "RUN_MANIFEST.json"), manifest)
        _write(os.path.join(run_dir, "CONFIG.json"), config or {})

        data_status = status if status in ("DATA_BLOCKED", "FROZEN_PRICE_PACK_NOT_MATERIALIZED") else "READY"
        if coverage and coverage.get("degenerate"):
            data_status = "DEGENERATE"
        data_lineage = {"upstream_dataset_id": manifest.get("upstream_dataset_id"),
                        "upstream_hash": manifest.get("upstream_hash"),
                        "derived_dataset_id": manifest.get("derived_dataset_id"),
                        "derived_dataset_hash": derived_dataset_hash,
                        "data_status": data_status, "coverage": coverage}
        _write(os.path.join(run_dir, "DATA_LINEAGE.json"), data_lineage)

        data_snap = _snapshots.data_snapshot(pack, elig, asof_index, data_status)
        _write(os.path.join(run_dir, "DATA_SNAPSHOT.json"), data_snap)

        _write(os.path.join(run_dir, "SIGNALS.json"), {"signals": signals or []})

        # lifecycle / trades
        lc_roll = _lifecycle.rollup(period_samples or [])
        lc_events = [_lifecycle.lifecycle_from_period(per) for per in (period_samples or [])]
        _write(os.path.join(run_dir, "TRADES.json"), {"lifecycle": lc_events})
        _write(os.path.join(run_dir, "LEDGER.json"), _ledger_from_periods(period_samples))

        # metrics (flatten) + attribution
        by_k = {}
        attr_map = {}
        if evaluate_result:
            for hold, per_k in evaluate_result.items():
                for k, summ in per_k.items():
                    label = "T%s_Top%s" % (hold, k)
                    by_k[label] = summ
                    attr_map[label] = _attr.attribution(summ)
        metrics = {"by_k": by_k, "lifecycle": lc_roll}
        _write(os.path.join(run_dir, "METRICS.json"), metrics)

        # errors / conclusion (use a representative evaluate_k = first, if any)
        rep_k = next(iter(by_k.values())) if by_k else None
        err = _errors.classify_run({"data_status": data_status, "coverage": coverage,
                                    "evaluate_k": rep_k, "lifecycle": lc_roll,
                                    "exception": exception, "where": "run_forensic"})
        _write(os.path.join(run_dir, "ERRORS.json"), err)

        report_md = _report.build_report(manifest, config, data_lineage, data_snap, signals,
                                         metrics, attr_map, err)
        with open(os.path.join(run_dir, "REPORT.md"), "w") as fh:
            fh.write(report_md)

        return {"forensic_status": "PASS", "run_id": manifest["run_id"], "run_dir": run_dir,
                "manifest_hash": mhash, "primary_conclusion": err.get("primary_conclusion")}
    except Exception as exc:  # never break the baseline
        return {"forensic_status": "DEGRADED", "error": str(exc)}


__all__ = ["run_forensic"]
