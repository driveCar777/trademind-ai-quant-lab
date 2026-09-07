"""V19 orchestrator."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import dump_json, load_json
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_alpha_v2.books import ew_overlapping
from research_engine.cn_a_share_indmacro_v19 import HOLD_DAYS, RESEARCH, VALIDATION
from research_engine.cn_a_share_indmacro_v19.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_indmacro_v19.evaluate import apply_gates, decide, run_one, slim_rec
from research_engine.cn_a_share_indmacro_v19.paths import EQUITY, OUT, ensure_v19
from research_engine.cn_a_share_indmacro_v19.signals import industry_codes, industry_macro_score
from research_engine.cn_a_share_macro_v17.evaluate import SIGN, _json_safe
from research_engine.cn_a_share_macro_v17.macro import load_aligned_shocks
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix


def _progress(stage, **extra):
    payload = {"stage": stage}
    payload.update(extra)
    dump_json(os.path.join(OUT, "PROGRESS.json"), payload)
    print("V19_PROGRESS", stage, flush=True)


def _hydrate(rec):
    if rec.get("period_rets"):
        return rec
    import csv

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


def main():
    ensure_v19()
    contract = build_contract()
    dump_json(os.path.join(OUT, "CONTRACT.json"), contract)
    _progress("CONTRACT", contract_hash=contract["contract_hash"])
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    xok = exec_ok_matrix(pack)
    elig = eligible(pack, 20)
    print("V19_INDUSTRY_MAP", flush=True)
    codes = industry_codes(pack)
    shocks = load_aligned_shocks(pack["dates"])
    ew = ew_overlapping(pack, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    done = {}
    part = os.path.join(OUT, "RESULTS_PARTIAL.json")
    if os.path.isfile(part):
        done = dict((r["id"], _hydrate(r)) for r in (load_json(part).get("hypotheses") or []))
    recs = []
    for hyp in HYPOTHESES:
        if hyp["id"] in done and "capital" in done[hyp["id"]]:
            print("V19_RESUME", hyp["id"], flush=True)
            recs.append(done[hyp["id"]])
            continue
        print("V19", hyp["id"], "SCORE", flush=True)
        scores = industry_macro_score(pack, elig, codes, shocks[hyp["macro"]], hyp["lookback"], SIGN[hyp["signal"]])
        rec = run_one(pack, elig, xok, ew, scores, hyp)
        recs.append(rec)
        dump_json(os.path.join(OUT, "RESULTS_PARTIAL.json"), {"hypotheses": [slim_rec(r) for r in recs], "n": len(recs)})
        _progress("HYP_DONE", id=hyp["id"], n=len(recs))
        del scores
    recs, candidates, _f, _fdr = apply_gates(recs)
    dump_json(os.path.join(OUT, "RESULTS.json"), {"hypotheses": [slim_rec(r) for r in recs]})
    decision = decide(candidates, True)
    dump_json(os.path.join(OUT, "DECISION.json"), _json_safe(decision))
    _progress("COMPLETE", overall=decision["OVERALL"], stop=decision["STOP"])
    print("V19_DECISION", decision["OVERALL"], decision["STOP"], "L1", decision["NEW_CANDIDATE"], "IND", decision["NEW_INDEPENDENT_CANDIDATE"], flush=True)
    return decision


if __name__ == "__main__":
    main()
