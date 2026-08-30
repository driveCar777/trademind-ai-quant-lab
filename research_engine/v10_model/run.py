"""V10 locked search. Local sklearn. No Final OOS. No purchase."""
from __future__ import print_function

import os

from research_engine.statistics import benjamini_hochberg
from research_engine.v10_model import (
    FDR_Q,
    FINAL_OOS_ACCESS,
    NEW_DATA_PURCHASE,
    PRIMARY_THRESHOLD,
    RISK_FRACS,
    START_EQUITY,
    THRESHOLDS,
    V10_ID,
    V10_SEED,
)
from research_engine.v10_model.contract import ABLATIONS, ASSETS, MODELS, REPRESENTATIONS, TARGETS, assert_contract, build_contract
from research_engine.v10_model.features import build_matrix
from research_engine.v10_model.inventory import write_universe
from research_engine.v10_model.metrics import predictive_advantage, permutation_auc_p, split_metrics
from research_engine.v10_model.models import fit_predict
from research_engine.v10_model.panel import assign_roles, build_panel
from research_engine.v10_model.persist import dump_json, out_path, persist_book, tmp_path, write_csv
from research_engine.v10_model.trade import buyhold_sides, hold_for, momentum_sides, replay_sides, sides_from_proba
from research_engine.v9_master.cost_overlay import CostOverlay
from research_engine.v9_master.metrics_v9 import economic_status


PURGE = 5
EMBARGO = 1
WARMUP = 120
PERM_ITERS = 199


def _ykey(target_id):
    return "y_" + target_id


def _mask(rows, role, target_id):
    n = len(rows)
    r_end = int(n * 0.70)
    v_end = int(n * 0.85)
    key = _ykey(target_id)
    out = []
    i = 0
    while i < n:
        if i < WARMUP or rows[i].get(key) is None:
            i += 1
            continue
        if role == "research" and rows[i].get("role") == "research" and i < (r_end - PURGE):
            out.append(i)
        elif role == "validation" and rows[i].get("role") == "validation" and i >= (r_end + EMBARGO) and i < v_end:
            out.append(i)
        i += 1
    return out


def _take(mat, idx):
    return [mat[i] for i in idx]


def _take_y(rows, idx, target_id):
    key = _ykey(target_id)
    return [int(rows[i][key]) for i in idx]


def _pred_at(pred, idx):
    return [pred[i] for i in idx]


def _cell_id(model_id, rep_id, target_id, asset, ablation="ALL"):
    if ablation == "ALL":
        return "V10-%s-%s-%s-%s" % (model_id, rep_id, target_id, asset)
    return "V10-%s-%s-%s-%s-%s" % (model_id, rep_id, target_id, asset, ablation)


def _trade_pack(rows, sides, target_id, risk, role):
    return replay_sides(rows, sides, hold_for(target_id), risk, role, START_EQUITY)


def run_v10():
    if FINAL_OOS_ACCESS != "DENIED":
        raise ValueError("FINAL_OOS")
    if NEW_DATA_PURCHASE is not False:
        raise ValueError("PURCHASE")
    contract = build_contract()
    assert_contract(contract)
    dump_json(out_path("MODEL_CONTRACT_V10.json"), contract)
    uni_path, universe = write_universe()

    panels = {}
    for asset in ASSETS:
        rows = assign_roles(build_panel(asset))
        panels[asset] = rows
        dump_json(tmp_path("panel_%s.json" % asset), {"n": len(rows), "first": rows[0]["date"], "last": rows[-1]["date"]})

    naive = {}
    registry = []
    results = []
    predictions = {}
    importance = []
    pvals = []
    p_index = []
    traded = []

    def record_naive(asset, target_id, rows, y_tr, idx_tr, idx_va):
        n = len(y_tr)
        pos = sum(y_tr)
        p = pos / float(n) if n else 0.5
        maj = 1 if pos >= (n - pos) else 0
        proba = [p] * len(rows)
        pred = [maj] * len(rows)
        m_tr = split_metrics(y_tr, _pred_at(proba, idx_tr), _pred_at(pred, idx_tr))
        y_va = _take_y(rows, idx_va, target_id)
        m_va = split_metrics(y_va, _pred_at(proba, idx_va), _pred_at(pred, idx_va))
        naive[(asset, target_id)] = {
            "proba": proba,
            "pred": pred,
            "research": m_tr,
            "validation": m_va,
            "base_rate": p,
            "majority": maj,
        }
        return m_tr, m_va

    jobs = []
    for asset in ASSETS:
        for tgt in TARGETS:
            for model in MODELS:
                for rep in REPRESENTATIONS:
                    if model["model_id"] == "M0" and rep["rep_id"] != "REP_RAW":
                        continue
                    jobs.append((asset, tgt["target_id"], model["model_id"], rep["rep_id"], "ALL"))
    for asset in ASSETS:
        for ablation in ABLATIONS:
            jobs.append((asset, "T1_DIR1", "M1", "REP_Z60", ablation))

    seen = set()
    unique_jobs = []
    for job in jobs:
        if job in seen:
            continue
        seen.add(job)
        unique_jobs.append(job)

    for asset, target_id, model_id, rep_id, ablation in unique_jobs:
        rows = panels[asset]
        idx_tr = _mask(rows, "research", target_id)
        idx_va = _mask(rows, "validation", target_id)
        if (asset, target_id) not in naive:
            record_naive(asset, target_id, rows, _take_y(rows, idx_tr, target_id), idx_tr, idx_va)
        exp_id = _cell_id(model_id, rep_id, target_id, asset, ablation)
        status = "FIT"
        note = ""
        y_tr = _take_y(rows, idx_tr, target_id)
        try:
            x_all, names = build_matrix(rows, "REP_RAW" if model_id == "M0" else rep_id, ablation)
            if len(set(y_tr)) < 2 and model_id != "M0":
                raise ValueError("ONE_CLASS")
            fitted = fit_predict(model_id, _take(x_all, idx_tr), y_tr, x_all)
        except Exception as exc:
            status = "FIT_FAILED"
            note = str(exc)
            fitted = {"proba": [0.5] * len(rows), "pred": [0] * len(rows), "importance": {}}
        proba = fitted["proba"]
        pred = fitted["pred"]
        m_tr = split_metrics(y_tr if status == "FIT" else [], _pred_at(proba, idx_tr), _pred_at(pred, idx_tr)) if status == "FIT" else {"n": 0}
        y_va = _take_y(rows, idx_va, target_id)
        m_va = split_metrics(y_va, _pred_at(proba, idx_va), _pred_at(pred, idx_va)) if status == "FIT" else {"n": 0}
        perm = permutation_auc_p(y_va, _pred_at(proba, idx_va), PERM_ITERS, V10_SEED) if status == "FIT" else {"p_value": 1.0, "statistic": 0.5}
        nav = naive[(asset, target_id)]
        adv = status == "FIT" and model_id != "M0" and predictive_advantage(m_va, nav["validation"])
        pvals.append(perm.get("p_value"))
        p_index.append(exp_id)
        imp = fitted.get("importance") or {}
        mapped = []
        if imp.get("values"):
            vals = imp["values"]
            i = 0
            while i < min(len(names), len(vals)):
                mapped.append({"feature": names[i], "value": vals[i]})
                i += 1
            mapped.sort(key=lambda r: r["value"], reverse=True)
        importance.append({"experiment_id": exp_id, "kind": imp.get("kind"), "top": mapped[:12]})
        pred_rows = []
        for i in idx_tr + idx_va:
            pred_rows.append(
                {
                    "date": rows[i]["date"],
                    "role": rows[i]["role"],
                    "y": rows[i][_ykey(target_id)],
                    "p": proba[i],
                }
            )
        predictions[exp_id] = pred_rows
        books = []
        conversion = "MODEL_ONLY"
        if adv:
            conversion = "STRATEGY_REPLAY"
            for role in ("research", "validation"):
                for thr in THRESHOLDS:
                    for risk in RISK_FRACS:
                        sides = sides_from_proba(proba, thr, rows, role)
                        book = _trade_pack(rows, sides, target_id, risk, role)
                        persist_book(exp_id, asset, role, risk, thr, book["equity_curve"], book["trades"], book["metrics"], rows)
                        books.append(
                            {
                                "role": role,
                                "threshold": thr,
                                "risk": risk,
                                "metrics": book["metrics"],
                                "n_trades": len(book["trades"]),
                            }
                        )
            with CostOverlay(2.0, 20.0):
                sides = sides_from_proba(proba, PRIMARY_THRESHOLD, rows, "validation")
                stress = _trade_pack(rows, sides, target_id, 0.01, "validation")
            books.append({"role": "validation_stress_costx2_slipx2", "threshold": PRIMARY_THRESHOLD, "risk": 0.01, "metrics": stress["metrics"], "stress": True})
        mom_r = _trade_pack(rows, momentum_sides(rows, "research"), target_id, 0.01, "research")
        mom_v = _trade_pack(rows, momentum_sides(rows, "validation"), target_id, 0.01, "validation")
        bh_v = _trade_pack(rows, buyhold_sides(rows, "validation"), target_id, 0.01, "validation")
        model_val_net = None
        for b in books:
            if b.get("role") == "validation" and b.get("threshold") == PRIMARY_THRESHOLD and b.get("risk") == 0.01:
                model_val_net = b["metrics"].get("net_return")
        adds = None
        if model_val_net is not None:
            adds = "MODEL_ADDS_VALUE" if model_val_net > (mom_v["metrics"].get("net_return") or 0) else "MODEL_ADDS_NO_VALUE"
        row = {
            "experiment_id": exp_id,
            "model_id": model_id,
            "family": [m["family"] for m in MODELS if m["model_id"] == model_id][0],
            "rep_id": rep_id,
            "target_id": target_id,
            "asset": asset,
            "ablation": ablation,
            "seed": V10_SEED,
            "split": "TIME_ORDER_70_15_15",
            "status": status,
            "note": note,
            "research": m_tr,
            "validation": m_va,
            "naive_validation": nav["validation"],
            "predictive_advantage": adv,
            "conversion": conversion,
            "auc_perm": perm,
            "p_value": perm.get("p_value"),
            "books": books,
            "momentum_rule": {"research": mom_r["metrics"], "validation": mom_v["metrics"]},
            "buyhold_validation": bh_v["metrics"],
            "model_vs_rule": adds,
            "reopen_condition": "NEW_EXPERIMENT_ONLY",
        }
        results.append(row)
        registry.append(
            {
                "model_id": exp_id,
                "family": row["family"],
                "features": ablation,
                "representation": rep_id,
                "target": target_id,
                "asset": asset,
                "seed": V10_SEED,
                "split": "TIME_ORDER_70_15_15",
                "result": {
                    "val_auc": (m_va or {}).get("auc"),
                    "val_logloss": (m_va or {}).get("logloss"),
                    "predictive_advantage": adv,
                    "conversion": conversion,
                },
                "status": status if status != "FIT" else ("PREDICTIVE_ADVANTAGE" if adv else "NO_ADVANTAGE"),
                "reopen_condition": "NEW_EXPERIMENT_ONLY",
            }
        )
        if conversion == "STRATEGY_REPLAY":
            traded.append(row)
        print("V10_CELL", exp_id, status, "ADV" if adv else "NOADV", (m_va or {}).get("auc"))

    fdr = benjamini_hochberg(pvals, q=FDR_Q)
    discoveries = set()
    for idx in fdr.get("discoveries") or []:
        if 0 <= idx < len(p_index):
            discoveries.add(p_index[idx])
    for i, row in enumerate(results):
        row["fdr_q"] = FDR_Q
        row["fdr_adjusted_p"] = (fdr.get("adjusted_p") or [None])[i] if i < len(fdr.get("adjusted_p") or []) else None
        row["fdr_discovery"] = row["experiment_id"] in discoveries

    # Candidate: same model/rep/target on >=2 assets, both windows costed+, FDR pass
    by_key = {}
    for row in results:
        if row.get("ablation") != "ALL" or row.get("model_id") == "M0":
            continue
        key = (row["model_id"], row["rep_id"], row["target_id"])
        by_key.setdefault(key, []).append(row)

    candidates = []
    for key, rows in by_key.items():
        asset_ok = []
        for row in rows:
            rbook = None
            vbook = None
            for b in row.get("books") or []:
                if b.get("threshold") != PRIMARY_THRESHOLD or b.get("risk") != 0.01 or b.get("stress"):
                    continue
                if b.get("role") == "research":
                    rbook = b["metrics"]
                if b.get("role") == "validation":
                    vbook = b["metrics"]
            econ = economic_status(rbook or {}, vbook or {})
            row["economic_status"] = econ
            if (
                row.get("predictive_advantage")
                and row.get("fdr_discovery")
                and econ == "POSITIVE_REPRODUCIBLE"
            ):
                asset_ok.append(row["asset"])
        if len(set(asset_ok)) >= 2:
            candidates.append({"key": list(key), "assets": sorted(set(asset_ok))})

    stop = "STOP_A_LEVEL1_CANDIDATE" if candidates else "STOP_B_MODEL_REPRESENTATION_EXHAUSTED"
    decision = "LEVEL1_CANDIDATE" if candidates else "NO_CANDIDATE"
    program = {
        "discovery_id": V10_ID,
        "LEVEL": 1 if candidates else 0,
        "CANDIDATE": 1 if candidates else 0,
        "STRATEGY": 0,
        "PORTFOLIO": 0,
        "PAPER": 0,
        "LIVE": 0,
        "NEW_DATA_PURCHASE": False,
        "FINAL_OOS_ACCESS": "DENIED",
        "stop": stop,
        "decision": decision,
        "n_experiments": len(results),
        "n_fdr": fdr.get("m"),
        "n_fdr_discoveries": len(fdr.get("discoveries") or []),
        "n_predictive_advantage": sum(1 for r in results if r.get("predictive_advantage")),
        "n_traded": len(traded),
        "candidates": candidates,
        "xavier": "NOT_USED_LOCAL_SKLEARN",
        "databento_incremental_research_value": 0,
        "unused_research_reserve_note": "remaining credits UNUSED_RESEARCH_RESERVE",
    }

    dump_json(out_path("MODEL_REGISTRY_V10.json"), {"n": len(registry), "models": registry})
    dump_json(out_path("MODEL_RESULTS_V10.json"), {"program": program, "fdr": {"q": FDR_Q, "m": fdr.get("m"), "discoveries": list(discoveries)}, "rows": results})
    dump_json(out_path("MODEL_PREDICTIONS_V10.json"), {"n": len(predictions), "predictions": predictions})
    dump_json(out_path("MODEL_FEATURE_IMPORTANCE_V10.json"), {"note": "Interpret only. Do not invent features from importance.", "rows": importance})

    eq_rows = []
    metrics_out = []
    for row in results:
        for b in row.get("books") or []:
            if b.get("stress"):
                continue
            metrics_out.append(
                {
                    "experiment_id": row["experiment_id"],
                    "asset": row["asset"],
                    "role": b.get("role"),
                    "threshold": b.get("threshold"),
                    "risk": b.get("risk"),
                    "net_return": (b.get("metrics") or {}).get("net_return"),
                    "cagr": (b.get("metrics") or {}).get("cagr"),
                    "max_drawdown": (b.get("metrics") or {}).get("max_drawdown"),
                    "sharpe": (b.get("metrics") or {}).get("sharpe"),
                    "sortino": (b.get("metrics") or {}).get("sortino"),
                    "calmar": (b.get("metrics") or {}).get("calmar"),
                    "turnover": (b.get("metrics") or {}).get("turnover"),
                    "average_holding": (b.get("metrics") or {}).get("average_holding"),
                    "cost_contribution": (b.get("metrics") or {}).get("cost_contribution"),
                    "trade_count": (b.get("metrics") or {}).get("trade_count"),
                }
            )
            if b.get("role") == "validation" and b.get("threshold") == PRIMARY_THRESHOLD and b.get("risk") == 0.01:
                ledger = os.path.join(
                    "ledgers",
                    row["experiment_id"].replace(":", "_"),
                    row["asset"],
                    "validation",
                    "r0.01_t0.55",
                    "equity.csv",
                )
                eq_path = os.path.join(os.path.dirname(out_path("MODEL_EQUITY_V10.csv")), ledger)
                if os.path.isfile(eq_path):
                    handle = open(eq_path, "r")
                    try:
                        import csv

                        reader = csv.DictReader(handle)
                        for er in reader:
                            eq_rows.append(
                                {
                                    "experiment_id": row["experiment_id"],
                                    "asset": row["asset"],
                                    "timestamp_utc": er.get("timestamp_utc"),
                                    "equity": er.get("equity"),
                                }
                            )
                    finally:
                        handle.close()
    if not eq_rows:
        eq_rows.append({"experiment_id": "NONE", "asset": "", "timestamp_utc": "", "equity": ""})
    write_csv(out_path("MODEL_EQUITY_V10.csv"), ["experiment_id", "asset", "timestamp_utc", "equity"], eq_rows)
    dump_json(out_path("MODEL_STRATEGY_METRICS_V10.json"), {"n": len(metrics_out), "rows": metrics_out})
    dump_json(out_path("MULTIPLE_TESTING_LEDGER_V10.json"), {"q": FDR_Q, "m": fdr.get("m"), "ids": p_index, "p": pvals, "adjusted": fdr.get("adjusted_p"), "discoveries": list(discoveries)})
    dump_json(out_path("PROGRAM_V10.json"), program)
    return {
        "universe": uni_path,
        "program": program,
        "n": len(results),
    }
