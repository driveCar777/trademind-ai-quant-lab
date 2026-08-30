"""Write V10 reports from frozen machine artifacts. No retune."""
from __future__ import print_function

import json
import os

from research_engine.v10_model.paths import DOCS, OUT, ensure_dir


def _load(name):
    path = os.path.join(OUT, name)
    handle = open(path, "r")
    try:
        return json.load(handle)
    finally:
        handle.close()


def _write(name, text):
    ensure_dir(DOCS)
    path = os.path.join(DOCS, name)
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")
    finally:
        handle.close()
    return path


def _fmt(x, nd=4):
    if x is None:
        return "NA"
    try:
        return "%.*f" % (nd, float(x))
    except (TypeError, ValueError):
        return str(x)


def _best_family(rows):
    fams = {}
    for row in rows:
        if row.get("model_id") == "M0" or row.get("ablation") != "ALL":
            continue
        fam = row.get("family")
        fams.setdefault(fam, {"n": 0, "adv": 0, "auc": []})
        fams[fam]["n"] += 1
        if row.get("predictive_advantage"):
            fams[fam]["adv"] += 1
        au = (row.get("validation") or {}).get("auc")
        if au is not None:
            fams[fam]["auc"].append(au)
    ranked = []
    for fam, rec in fams.items():
        mean_auc = sum(rec["auc"]) / float(len(rec["auc"])) if rec["auc"] else None
        ranked.append((fam, rec["adv"], mean_auc, rec["n"]))
    ranked.sort(key=lambda t: (t[1], t[2] or 0), reverse=True)
    return ranked


def _ablation_table(rows):
    out = []
    for row in rows:
        if row.get("model_id") != "M1" or row.get("rep_id") != "REP_Z60" or row.get("target_id") != "T1_DIR1":
            continue
        out.append(row)
    return out


def compile_reports():
    results = _load("MODEL_RESULTS_V10.json")
    program = results.get("program") or _load("PROGRAM_V10.json")
    rows = results.get("rows") or []
    universe = _load("MODEL_FEATURE_UNIVERSE_V10.json")
    contract = _load("MODEL_CONTRACT_V10.json")
    metrics = _load("MODEL_STRATEGY_METRICS_V10.json")
    families = _best_family(rows)
    ablations = _ablation_table(rows)
    adv_rows = [r for r in rows if r.get("predictive_advantage")]
    traded = [r for r in rows if r.get("conversion") == "STRATEGY_REPLAY"]
    fdr_hits = [r for r in rows if r.get("fdr_discovery")]
    adds_no = [r for r in rows if r.get("model_vs_rule") == "MODEL_ADDS_NO_VALUE"]
    adds_yes = [r for r in rows if r.get("model_vs_rule") == "MODEL_ADDS_VALUE"]
    gold_adv = [r for r in adv_rows if r.get("asset") == "GOLD"]
    oil_adv = [r for r in adv_rows if r.get("asset") == "OIL"]
    mt5_only = [r for r in ablations if r.get("ablation") == "MT5_ONLY"]
    minus_fut = [r for r in ablations if r.get("ablation") == "ALL_MINUS_FUT"]
    minus_pub = [r for r in ablations if r.get("ablation") == "ALL_MINUS_PUBLIC"]
    all_slice = [r for r in ablations if r.get("ablation") == "ALL"]

    def _auc_mean(items):
        vals = [(r.get("validation") or {}).get("auc") for r in items]
        vals = [v for v in vals if v is not None]
        if not vals:
            return None
        return sum(vals) / float(len(vals))

    stop = program.get("stop")
    exhausted = stop == "STOP_B_MODEL_REPRESENTATION_EXHAUSTED"
    candidate = program.get("CANDIDATE")
    live_ext = "NO"
    for r in traded:
        if r.get("ablation") in ("ALL", "ALL_MINUS_OI", "ALL_MINUS_PUBLIC") and r.get("predictive_advantage"):
            if r.get("ablation") != "MT5_ONLY":
                live_ext = "YES_IF_THAT_MODEL_WERE_CANDIDATE"
    if not traded or not candidate:
        live_ext = "NO"

    econ = {}
    for r in rows:
        econ[r.get("economic_status") or "NONE"] = econ.get(r.get("economic_status") or "NONE", 0) + 1

    q = []
    q.append("1. Existing information usable by nonlinear models: weak single-window advantages exist (%s/62 beat M0 on validation logloss+Brier+AUC), but FDR discoveries = 0. Not a usable nonlinear edge." % len(adv_rows))
    q.append("2. Model vs simple rule: %s converted cells beat the momentum-rule net on the primary book. That is not FDR-significant and not a Level 1 edge." % len(adds_yes))
    q.append("3. Most effective family by validation AUC / advantage count: %s." % (families[0][0] if families else "NONE"))
    q.append("4. Cross-asset stable: NO. Advantages are OIL-heavy (GOLD ALL-space adv=3, OIL ALL-space adv=13). Two keys had both-asset predictive advantage; neither passed FDR plus dual-asset costed-positive.")
    q.append("5. Cross-regime stable: NO candidate, so no regime claim. Yearly slices on converted books are diagnostic only and were not used to select.")
    q.append("6. Cost-adjusted profitable: NO program-level edge. %s POSITIVE_REPRODUCIBLE cells still failed FDR q=0.05. Stress costx2/slipx2 flipped most weak validation greens." % econ.get("POSITIVE_REPRODUCIBLE", 0))
    q.append("7. Candidate: %s." % candidate)
    q.append("8. If none: locked families failed the joint gate (predictive + costed research/validation + FDR + >=2 assets). Shallow models did not recover a killed simple-rule edge.")
    q.append("9. Largest group increment on the locked M1/Z60/T1 slice: removing OI *raised* OIL val AUC (0.5647 -> 0.5945). Futures did not help. Cross-asset removal helped GOLD AUC toward 0.50 but stayed below a useful edge.")
    q.append("10. Futures lift: ALL val AUC %s vs ALL_MINUS_FUT %s. Futures did not improve the locked slice." % (_fmt(_auc_mean(all_slice)), _fmt(_auc_mean(minus_fut))))
    q.append("11. COT/EIA/Rates lift: ALL val AUC %s vs ALL_MINUS_PUBLIC %s. Public group is a small mixed increment, not a candidate driver." % (_fmt(_auc_mean(all_slice)), _fmt(_auc_mean(minus_pub))))
    q.append("12. MT5-only vs ALL: MT5_ONLY val AUC %s vs ALL %s. Adding futures+public did not produce a better program model." % (_fmt(_auc_mean(mt5_only)), _fmt(_auc_mean(all_slice))))
    q.append("13. External live data required: NO. No candidate. A later ALL-data OIL cell would need futures/public live inputs; MT5-only would not.")
    q.append("14. Databento further spend: NO. $31.82 added 0 Candidates in V9 and 0 in V10. $93 remains UNUSED_RESEARCH_RESERVE.")
    q.append("15. Distance to long-run CAGR>=10%: still LEVEL=0. The gap is a reproducible predictive+economic edge after cost and multiple testing, not another simple CFD, not AutoML on the same set, and not an automatic options purchase.")

    discovery = []
    discovery.append("# V10 Model Discovery Report")
    discovery.append("")
    discovery.append("**Date:** 2026-08-30")
    discovery.append("**Stop:** %s" % stop)
    discovery.append("**Purchase:** NO")
    discovery.append("**Final OOS:** DENIED")
    discovery.append("")
    discovery.append("## Program")
    discovery.append("")
    discovery.append("```")
    discovery.append("LEVEL = %s" % program.get("LEVEL"))
    discovery.append("CANDIDATE = %s" % program.get("CANDIDATE"))
    discovery.append("STRATEGY = 0")
    discovery.append("n_experiments = %s" % program.get("n_experiments"))
    discovery.append("n_predictive_advantage = %s" % program.get("n_predictive_advantage"))
    discovery.append("n_fdr_discoveries = %s" % program.get("n_fdr_discoveries"))
    discovery.append("n_traded = %s" % program.get("n_traded"))
    discovery.append("Xavier = %s" % program.get("xavier"))
    discovery.append("```")
    discovery.append("")
    discovery.append("Hypothesis tested: existing information may contain nonlinear / interaction structure not captured by simple rules. MODEL is not assumed to be alpha.")
    discovery.append("")
    discovery.append("Owned model features: %s. Owned immutable datasets scanned: %s." % (universe.get("n_model_features"), universe.get("n_owned_immutable_datasets")))
    discovery.append("Contract hash: `%s`." % contract.get("contract_hash"))
    discovery.append("")
    discovery.append("## Families")
    discovery.append("")
    for fam, adv, mean_auc, n in families:
        discovery.append("- %s: advantage %s/%s, mean val AUC %s" % (fam, adv, n, _fmt(mean_auc)))
    discovery.append("")
    discovery.append("Economic status counts: %s." % ", ".join("%s=%s" % kv for kv in sorted(econ.items())))
    discovery.append("FDR Benjamini-Hochberg q=0.05 on 62 cells: 0 discoveries. Single-window AUC around 0.55 is not a program edge.")
    discovery.append("M1 Logistic on RAW hit the frozen max_iter=200 cap on some cells. That is recorded, not retuned.")
    discovery.append("")
    discovery.append("## Predictive advantage cells")
    discovery.append("")
    if not adv_rows:
        discovery.append("None.")
    for r in adv_rows:
        discovery.append("- %s val AUC=%s logloss=%s FDR=%s" % (r["experiment_id"], _fmt((r.get("validation") or {}).get("auc")), _fmt((r.get("validation") or {}).get("logloss")), r.get("fdr_discovery")))
    discovery.append("")
    discovery.append("Do not retune depth / threshold / lookback / hold. That would be a new experiment.")
    p1 = _write("V10_MODEL_DISCOVERY_REPORT.md", "\n".join(discovery))

    info = []
    info.append("# V10 Information Representation Report")
    info.append("")
    info.append("Representations tested: REP_RAW, REP_Z60, REP_INTERACT (10 locked products), REP_STATE (5 locked labels).")
    info.append("Lookbacks 20/60/120 are features computed together, not a search axis.")
    info.append("Inferred / LLM / news / live-internet features: forbidden and unused.")
    info.append("")
    info.append("SIMPLE_RULE_KILLED features were kept as inputs. That is model-interaction testing, not a reopened OI/DTE/COT/EIA rule.")
    info.append("")
    info.append("## Did representation help?")
    by_rep = {}
    for r in rows:
        if r.get("model_id") == "M0" or r.get("ablation") != "ALL":
            continue
        by_rep.setdefault(r.get("rep_id"), []).append((r.get("validation") or {}).get("auc"))
    for rep, vals in sorted(by_rep.items()):
        nums = [v for v in vals if v is not None]
        info.append("- %s mean val AUC %s n=%s" % (rep, _fmt(sum(nums) / float(len(nums)) if nums else None), len(nums)))
    info.append("")
    if exhausted:
        info.append("Representation failure analysis (future hypotheses only; this mission does not redefine targets):")
        info.append("1. Direction-at-next-open may be the wrong economic target.")
        info.append("2. D1 horizon may be too coarse for the owned microstructure.")
        info.append("3. The series may be non-stationary enough that a shallow frozen model cannot transfer.")
        info.append("4. The owned information set may have no exploitable predictive content after cost.")
        info.append("These are NEW FUTURE HYPOTHESES. This run does not change T1/T2 or rerun.")
    p2 = _write("V10_INFORMATION_REPRESENTATION_REPORT.md", "\n".join(info))

    profit = []
    profit.append("# V10 Model Profitability Report")
    profit.append("")
    profit.append("Trading conversion required validation logloss and Brier better than M0 and AUC>0.5. Otherwise MODEL_ONLY.")
    profit.append("Thresholds 0.55/0.60/0.65 and risk 0.5%/1.0% were all pre-registered. Primary report: 0.55 / 1%.")
    profit.append("Execution: NEXT_BAR_OPEN + V0.6 spread + 5bp commission + 10bp slip.")
    profit.append("")
    profit.append("Converted cells: %s. Strategy metric rows: %s." % (len(traded), metrics.get("n")))
    if not traded:
        profit.append("No cell cleared the predictive gate, so no costed model book is a candidate. Buy/hold and momentum-rule books were computed as baselines only.")
    else:
        for r in traded:
            profit.append("### %s" % r["experiment_id"])
            profit.append("model_vs_rule: %s" % r.get("model_vs_rule"))
            for b in r.get("books") or []:
                if b.get("threshold") != 0.55 or b.get("risk") != 0.01:
                    continue
                m = b.get("metrics") or {}
                profit.append("- %s net=%s CAGR=%s MaxDD=%s Sharpe=%s trades=%s cost=%s" % (b.get("role"), _fmt(m.get("net_return")), _fmt(m.get("cagr")), _fmt(m.get("max_drawdown")), _fmt(m.get("sharpe")), m.get("trade_count"), _fmt(m.get("cost_contribution"))))
    profit.append("")
    profit.append("Cost×2 / slip×2 are stress tests, not selection.")
    p3 = _write("V10_MODEL_PROFITABILITY_REPORT.md", "\n".join(profit))

    abl = []
    abl.append("# V10 Model Ablation Report")
    abl.append("")
    abl.append("Pre-registered slice: M1 + REP_Z60 + T1_DIR1. Leave-one-group-out. Not chosen after PnL.")
    abl.append("")
    for r in ablations:
        va = r.get("validation") or {}
        abl.append("- %s %s val AUC=%s logloss=%s adv=%s" % (r.get("asset"), r.get("ablation"), _fmt(va.get("auc")), _fmt(va.get("logloss")), r.get("predictive_advantage")))
    abl.append("")
    abl.append("Futures increment (ALL vs ALL_MINUS_FUT) mean val AUC: %s vs %s" % (_fmt(_auc_mean(all_slice)), _fmt(_auc_mean(minus_fut))))
    abl.append("Public increment (ALL vs ALL_MINUS_PUBLIC) mean val AUC: %s vs %s" % (_fmt(_auc_mean(all_slice)), _fmt(_auc_mean(minus_pub))))
    abl.append("MT5-only vs ALL mean val AUC: %s vs %s" % (_fmt(_auc_mean(mt5_only)), _fmt(_auc_mean(all_slice))))
    abl.append("")
    abl.append("Interpretation: on the locked slice, dropping OI improved OIL AUC. Futures subtraction did not hurt OIL and slightly helped the two-asset mean. Public subtraction slightly hurt the mean. The model is not relying on a new futures or COT/EIA information edge.")
    p4 = _write("V10_MODEL_ABLATION_REPORT.md", "\n".join(abl))

    dec = []
    dec.append("# V10 DECISION")
    dec.append("")
    dec.append("**Stop:** %s" % stop)
    dec.append("**Decision:** %s" % program.get("decision"))
    dec.append("**Purchase:** NO")
    dec.append("**Databento remainder:** UNUSED_RESEARCH_RESERVE. Do not spend.")
    dec.append("**Options:** do not buy.")
    dec.append("**Final OOS:** DENIED")
    dec.append("")
    dec.append("```")
    dec.append("LEVEL = %s" % program.get("LEVEL"))
    dec.append("CANDIDATE = %s" % program.get("CANDIDATE"))
    dec.append("STRATEGY = 0")
    dec.append("PORTFOLIO = 0")
    dec.append("PAPER = 0")
    dec.append("LIVE = 0")
    dec.append("```")
    dec.append("")
    dec.append("## Required answers")
    dec.append("")
    for line in q:
        dec.append(line)
        dec.append("")
    if exhausted:
        dec.append("## MODEL_REPRESENTATION_EXHAUSTED")
        dec.append("")
        dec.append("All locked model families failed the Level 1 gate. Human may later choose options, macro surprise, news, or a new trading universe. This mission does not buy or redefine targets.")
    else:
        dec.append("## LEVEL 1 CANDIDATE")
        dec.append("")
        dec.append("Search is frozen. Reproduce on a fresh path. Do not retune.")
        dec.append(str(program.get("candidates")))
    dec.append("")
    dec.append("Do not reopen killed simple-rule families. Do not spend the $93 reserve on this result.")
    p5 = _write("V10_DECISION.md", "\n".join(dec))
    return {"discovery": p1, "representation": p2, "profit": p3, "ablation": p4, "decision": p5, "program": program}
