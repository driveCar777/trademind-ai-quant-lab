"""V17 orchestrator. Frozen panel + frozen macro. Resume per hypothesis."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import dump_json, load_json
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_alpha_v2.books import ew_overlapping
from research_engine.cn_a_share_macro_v17 import HOLD_DAYS, RESEARCH, VALIDATION
from research_engine.cn_a_share_macro_v17.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_macro_v17.evaluate import _json_safe, apply_gates, decide, run_one, slim_rec
from research_engine.cn_a_share_macro_v17.macro import load_aligned_shocks
from research_engine.cn_a_share_macro_v17.paths import OUT, ensure_v17
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix


def _progress(stage, **extra):
    payload = {"stage": stage}
    payload.update(extra)
    dump_json(os.path.join(OUT, "PROGRESS.json"), payload)
    print("V17_PROGRESS", stage, flush=True)


def _hydrate_rets(rec):
    if rec.get("period_rets") and rec.get("pred_rets"):
        return rec
    import csv

    from research_engine.cn_a_share_macro_v17.paths import EQUITY

    path = os.path.join(EQUITY, "%s.csv" % rec["id"])
    period = {}
    if os.path.isfile(path):
        handle = open(path, "r", encoding="utf-8")
        try:
            for row in csv.DictReader(handle):
                if row.get("signal_date") and row.get("capital_ret") not in (None, ""):
                    period[row["signal_date"]] = float(row["capital_ret"])
        finally:
            handle.close()
    rec["period_rets"] = period
    rec.setdefault("pred_rets", {})
    rec.setdefault("mechanism", "")
    return rec


def _load_partial():
    path = os.path.join(OUT, "RESULTS_PARTIAL.json")
    if not os.path.isfile(path):
        return []
    data = load_json(path)
    return [_hydrate_rets(r) for r in (data.get("hypotheses") or [])]


def _save_partial(recs):
    dump_json(os.path.join(OUT, "RESULTS_PARTIAL.json"), {"hypotheses": [slim_rec(r) for r in recs], "n": len(recs)})


def main():
    ensure_v17()
    contract = build_contract()
    dump_json(os.path.join(OUT, "CONTRACT.json"), contract)
    _progress("CONTRACT", contract_hash=contract["contract_hash"])
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    print("V17_PACK", len(pack["dates"]), len(pack["symbols"]), flush=True)
    shocks = load_aligned_shocks(pack["dates"])
    dump_json(os.path.join(OUT, "MACRO_ALIGN.json"), shocks["meta"])
    xok = exec_ok_matrix(pack)
    elig = eligible(pack, 20)
    ew = ew_overlapping(pack, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    done = dict((r["id"], r) for r in _load_partial())
    recs = []
    for hyp in HYPOTHESES:
        if hyp["id"] in done and "predictive" in done[hyp["id"]] and "capital" in done[hyp["id"]]:
            print("V17_RESUME", hyp["id"], flush=True)
            recs.append(done[hyp["id"]])
            continue
        rec = run_one(pack, elig, xok, ew, shocks, hyp, None)
        recs.append(rec)
        _save_partial(recs)
        _progress("HYP_DONE", id=hyp["id"], n=len(recs))
    recs, candidates, failures, fdr = apply_gates(recs, pack, elig, xok, shocks)
    dump_json(os.path.join(OUT, "RESULTS.json"), {"hypotheses": [slim_rec(r) for r in recs]})
    decision = decide(candidates, True)
    if decision.get("independent_ids"):
        decision["CANDIDATE"] = 2 + len(decision["independent_ids"])
    dump_json(os.path.join(OUT, "DECISION.json"), _json_safe(decision))
    _progress("COMPLETE", overall=decision["OVERALL"], stop=decision["STOP"], new_independent=decision["NEW_INDEPENDENT_CANDIDATE"])
    print("V17_DECISION", decision["OVERALL"], decision["STOP"], "L1", decision["NEW_CANDIDATE"], "IND", decision["NEW_INDEPENDENT_CANDIDATE"], flush=True)
    return decision


if __name__ == "__main__":
    main()
