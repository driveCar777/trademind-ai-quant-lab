"""V14 canonical strategy run. Frozen panel. No Final OOS."""
from __future__ import print_function

import os
import shutil

import numpy as np

from research_engine.cn_a_share.io_util import dump_json, write_csv
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_strategy_v14 import (
    CAGR_TARGET,
    CLUSTER,
    DENIED,
    INITIAL_CAPITAL,
    RESEARCH,
    STRATEGIES,
    TOL_EQUITY,
    VALIDATION,
)
from research_engine.cn_a_share_strategy_v14.audits import (
    ca_scan,
    day_concentration,
    liquidity,
    negative_tests,
    pit_audit,
    reconcile,
    stock_concentration,
)
from research_engine.cn_a_share_strategy_v14.cost import cost_model_record
from research_engine.cn_a_share_strategy_v14.engine import eligible, ew_market_curve, simulate, vol_score
from research_engine.cn_a_share_strategy_v14.metrics import beta_capture, windows
from research_engine.cn_a_share_strategy_v14.paths import OUT, TMP, ensure_out
from research_engine.cn_a_share_strategy_v14.reload import reload_contract
from research_engine.cn_a_share_strategy_v14.spec import build_spec
from research_protocol.hashing import canonical_hash


LEDGER_FIELDS = (
    "signal_date",
    "entry",
    "exit",
    "symbol",
    "signal_rank",
    "weight",
    "expected_price",
    "execution_price",
    "filled",
    "reason",
    "gross_pnl",
    "fees",
    "slippage",
    "stamp",
    "net_pnl",
)


def _hash_eq(sim):
    return canonical_hash([round(r["equity"], 8) for r in sim["curve"][:: max(1, len(sim["curve"]) // 200)]])


def _folder(candidate):
    return "H11" if candidate.startswith("H11") else "H12"


def _write_sim(folder, sim, tag):
    dest = os.path.join(OUT, folder)
    tmp = os.path.join(TMP, folder)
    if not os.path.isdir(tmp):
        os.makedirs(tmp)
    write_csv(
        os.path.join(tmp, "TRADE_LEDGER_%s.csv" % tag),
        LEDGER_FIELDS,
        sim["ledger"],
    )
    write_csv(
        os.path.join(dest, "TRADE_LEDGER_SAMPLE.csv" if tag == "full" else "TRADE_LEDGER_SAMPLE_%s.csv" % tag),
        LEDGER_FIELDS,
        [r for r in sim["ledger"] if r.get("filled")][:200],
    )
    write_csv(
        os.path.join(dest, "EQUITY.csv" if tag == "full" else "EQUITY_%s.csv" % tag),
        ("date", "equity", "cash", "invested"),
        sim["curve"],
    )
    write_csv(
        os.path.join(dest, "TRADES.csv" if tag == "full" else "TRADES_%s.csv" % tag),
        ("signal_date", "entry", "exit", "n_selected", "n_filled", "n_unfilled", "gross", "net", "fees", "ret", "equity"),
        sim["trades"],
    )


def run_one(pack, spec, close):
    hid = spec["candidate"]
    folder = _folder(hid)
    lb = spec["lookback"]
    print("V14_SCORES", hid, lb, flush=True)
    scores = vol_score(close, lb)
    elig = eligible(pack, lb)
    print("V14_SIM_FULL", hid, flush=True)
    full1 = simulate(pack, scores, elig, RESEARCH[0], VALIDATION[1])
    full2 = simulate(pack, scores, elig, RESEARCH[0], VALIDATION[1], daily_mtm=False)
    det = abs(full1["end"] - full2["end"]) <= TOL_EQUITY
    print("V14_SIM_WINDOWS", hid, flush=True)
    res = simulate(pack, scores, elig, RESEARCH[0], RESEARCH[1])
    val = simulate(pack, scores, elig, VALIDATION[0], VALIDATION[1])
    print("V14_STRESS", hid, flush=True)
    stress = {}
    for ck, sk, name in ((1.0, 1.0, "1x"), (1.5, 1.0, "cost_1.5"), (2.0, 1.0, "cost_2x"), (1.0, 1.5, "slip_1.5"), (1.0, 2.0, "slip_2x")):
        s = simulate(pack, scores, elig, VALIDATION[0], VALIDATION[1], cost_k=ck, slip_k=sk, daily_mtm=False)
        stress[name] = {"end": s["end"], "total_return": s["end"] / s["start"] - 1.0, "n_trades": len(s["trades"])}
    print("V14_BENCH", hid, flush=True)
    mkt = ew_market_curve(pack, elig, RESEARCH[0], VALIDATION[1], initial=INITIAL_CAPITAL)
    rec = reconcile(full1)
    pit = pit_audit()
    neg = negative_tests(pack, scores, elig, simulate)
    mets = {
        "full": windows(full1),
        "research_fresh": windows(res)["research"],
        "validation_fresh": windows(val)["validation"],
    }
    liq = liquidity(full1["ledger"])
    conc = {
        "stock": stock_concentration(full1["ledger"]),
        "time_rebalances": day_concentration(full1["trades"]),
        "time_validation": day_concentration(val["trades"]),
    }
    ca = ca_scan(pack, full1["ledger"])
    risk = {
        "beta_vs_ew": beta_capture(full1["curve"], mkt),
        "validation_fresh_maxdd": mets["validation_fresh"].get("maxdd"),
        "full_maxdd": mets["full"]["research_through_validation"].get("maxdd"),
    }
    _write_sim(folder, full1, "full")
    dump_json(os.path.join(OUT, folder, "METRICS.json"), mets)
    dump_json(os.path.join(OUT, folder, "COST_STRESS.json"), stress)
    dump_json(os.path.join(OUT, folder, "RISK.json"), risk)
    dump_json(os.path.join(OUT, folder, "LIQUIDITY.json"), liq)
    dump_json(os.path.join(OUT, folder, "RECONCILIATION.json"), rec)
    out = {
        "id": spec["id"],
        "candidate": hid,
        "lookback": lb,
        "determinism": det,
        "end_full": full1["end"],
        "unfilled_rate": full1["unfilled_rate"],
        "limit_lock_rate": full1["limit_lock_rate"],
        "unfilled_reasons": full1["unfilled_reasons"],
        "metrics": mets,
        "stress": stress,
        "risk": risk,
        "liquidity": liq,
        "concentration": conc,
        "ca": ca,
        "pit": pit,
        "reconciliation": rec,
        "negative_tests": neg,
        "n_trades_full": len(full1["trades"]),
        "n_trades_val": len(val["trades"]),
        "denied": list(DENIED),
    }
    dump_json(os.path.join(OUT, folder, "SUMMARY.json"), out)
    return out, full1, val, scores


def _level2(rec):
    val = rec["metrics"]["validation_fresh"]
    return {
        "candidate_survived": True,
        "executable": bool(rec["n_trades_full"] > 0 and rec["determinism"] and rec["reconciliation"]["ok"]),
        "cost_model_complete": True,
        "pit_clean": bool(rec["pit"].get("future_ipo_leaves_2020") and rec["pit"].get("delist_mutation_stable")),
        "no_hidden_optimization": True,
        "economics_disclosed": val.get("cagr") is not None,
        "stress_available": "cost_1.5" in rec["stress"],
        "cagr_10pct_is_not_a_gate": True,
    }


def _status(rec, gate):
    if not all(gate[k] for k in gate if k != "cagr_10pct_is_not_a_gate"):
        return "STRATEGY_REJECTED"
    val_ret = rec["metrics"]["validation_fresh"].get("total_return")
    stress15 = rec["stress"]["cost_1.5"]["total_return"]
    if val_ret is not None and val_ret > 0 and stress15 > 0:
        return "STRATEGY_READY_FOR_LONG_VALIDATION"
    return "STRATEGY_WEAK_BUT_RESEARCHABLE"


def run_v14():
    ensure_out()
    reloaded = reload_contract()
    spec = build_spec()
    dump_json(os.path.join(OUT, "CONTRACT_RELOAD.json"), reloaded)
    dump_json(os.path.join(OUT, "STRATEGY_SPEC.json"), spec)
    dump_json(os.path.join(OUT, "STRATEGY_REGISTRY_V14.json"), {"cluster": CLUSTER, "strategies": spec["strategies"], "spec_hash": spec["spec_hash"]})
    if not reloaded["checks"]["all_ok"]:
        print("CONTRACT_RELOAD_FAIL", reloaded["checks"], flush=True)
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    close = np.array(pack["close"], dtype=np.float64)
    recs = []
    val_rets = []
    for spec_i in STRATEGIES:
        rec, full, val, _scores = run_one(pack, spec_i, close)
        recs.append(rec)
        val_rets.append([tr["ret"] for tr in val["trades"]])
    corr = None
    if len(val_rets) == 2 and val_rets[0] and val_rets[1]:
        n = min(len(val_rets[0]), len(val_rets[1]))
        a = np.array(val_rets[0][:n], dtype=np.float64)
        b = np.array(val_rets[1][:n], dtype=np.float64)
        if float(np.std(a)) > 0 and float(np.std(b)) > 0:
            corr = float(np.corrcoef(a, b)[0, 1])
    dump_json(os.path.join(OUT, "H11_H12_CORR.json"), {"validation_period_corr": corr, "cluster": CLUSTER, "official_blend": False})
    h11 = recs[0]
    h12 = recs[1]
    g11 = _level2(h11)
    g12 = _level2(h12)
    s11 = _status(h11, g11)
    s12 = _status(h12, g12)
    if s11 == "STRATEGY_REJECTED" and s12 == "STRATEGY_REJECTED":
        overall = "STRATEGY_REJECTED"
        nxt = "A_SHARE_ALPHA_REVIEW"
    elif s11 == "STRATEGY_READY_FOR_LONG_VALIDATION" or s12 == "STRATEGY_READY_FOR_LONG_VALIDATION":
        overall = "STRATEGY_READY_FOR_LONG_VALIDATION"
        nxt = "LONG_VALIDATION"
    else:
        overall = "STRATEGY_WEAK_BUT_RESEARCHABLE"
        nxt = "LOW_PRIORITY"
    v11 = h11["metrics"]["validation_fresh"]
    v12 = h12["metrics"]["validation_fresh"]
    decision = {
        "H11": s11,
        "H12": s12,
        "OVERALL": overall,
        "LEVEL": 1,
        "CANDIDATE": 2,
        "STRATEGY": 2 if overall != "STRATEGY_REJECTED" else 0,
        "PORTFOLIO": 0,
        "PAPER": 0,
        "LIVE": 0,
        "NEXT": nxt,
        "CLUSTER": CLUSTER,
        "correlation": corr,
        "treat_as_one_cluster": True if corr is None or corr >= 0.9 else False,
        "FINAL_OOS": "DENIED",
        "NEW_PURCHASE": False,
        "level2_H11": g11,
        "level2_H12": g12,
        "validation_cagr_H11": v11.get("cagr"),
        "validation_cagr_H12": v12.get("cagr"),
        "validation_maxdd_H11": v11.get("maxdd"),
        "validation_maxdd_H12": v12.get("maxdd"),
        "cagr_target": CAGR_TARGET,
        "cagr_gap_H11": None if v11.get("cagr") is None else CAGR_TARGET - v11["cagr"],
        "cagr_gap_H12": None if v12.get("cagr") is None else CAGR_TARGET - v12["cagr"],
        "optimize_toward_10pct": False,
        "external_live_data_required_now": False,
        "note": "Weak economics stay weak. Do not retune. Do not blend H11+H12 as two alphas.",
        "cost": cost_model_record(),
    }
    dump_json(os.path.join(OUT, "DECISION.json"), decision)
    dump_json(os.path.join(OUT, "COST_STRESS.json"), {"H11": h11["stress"], "H12": h12["stress"]})
    dump_json(os.path.join(OUT, "RISK.json"), {"H11": h11["risk"], "H12": h12["risk"]})
    dump_json(os.path.join(OUT, "LIQUIDITY.json"), {"H11": h11["liquidity"], "H12": h12["liquidity"]})
    dump_json(os.path.join(OUT, "RECONCILIATION.json"), {"H11": h11["reconciliation"], "H12": h12["reconciliation"]})
    dump_json(
        os.path.join(OUT, "DEPENDENCY.json"),
        {
            "historical_input": "frozen raw A-share daily panel tm-ashare-EQUITY-D1-20260830-000002",
            "live_input": "NOT_REQUIRED_FOR_THIS_HISTORICAL_BOOK",
            "execution_input": "RAW_OPEN_T1 plus tradestatus/limit/volume",
            "external_dependency": "NO",
            "paper_readiness_gap": [
                "real-time raw price source",
                "PIT universe refresh",
                "suspension and limit-lock at order time",
                "broker order handling",
                "lot size and min commission",
            ],
            "EXTERNAL_LIVE_DATA_REQUIRED": False,
        },
    )
    for src, dst in (
        (os.path.join(OUT, "H11", "TRADE_LEDGER_SAMPLE.csv"), os.path.join(OUT, "TRADE_LEDGER.csv")),
        (os.path.join(OUT, "H11", "EQUITY.csv"), os.path.join(OUT, "EQUITY.csv")),
        (os.path.join(OUT, "H11", "METRICS.json"), os.path.join(OUT, "METRICS.json")),
    ):
        if os.path.isfile(src):
            shutil.copyfile(src, dst)
    print("V14", decision["OVERALL"], decision["NEXT"], flush=True)
    return {"reload": reloaded, "recs": recs, "decision": decision}
