"""V20 orchestrator: freeze index PIT if needed, then dual-book alpha."""
from __future__ import print_function

import os

from research_engine.cn_a_share.io_util import dump_json, load_json
from research_engine.cn_a_share_alpha.pack import load_pack, pack_exists, pack_panel
from research_engine.cn_a_share_alpha_v2.books import ew_overlapping
from research_engine.cn_a_share_index_v20 import HOLD_DAYS, RESEARCH, VALIDATION
from research_engine.cn_a_share_index_v20.contract import HYPOTHESES, build_contract
from research_engine.cn_a_share_index_v20.evaluate import apply_gates, decide, run_one, slim_rec
from research_engine.cn_a_share_index_v20.factory import download_index_monthly, normalize_index
from research_engine.cn_a_share_index_v20.paths import EQUITY, IDX_CSV, OUT, ensure_v20
from research_engine.cn_a_share_index_v20.pit import freeze_index_dataset, run_index_pit
from research_engine.cn_a_share_index_v20.signals import build_scores, load_index_rows
from research_engine.cn_a_share_macro_v17.evaluate import _json_safe
from research_engine.cn_a_share_strategy_v14_1.scores import eligible, exec_ok_matrix


def _progress(stage, **extra):
    payload = {"stage": stage}
    payload.update(extra)
    dump_json(os.path.join(OUT, "PROGRESS.json"), payload)
    print("V20_PROGRESS", stage, flush=True)


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


def prepare_index():
    ensure_v20()
    _progress("DOWNLOAD")
    download_index_monthly()
    _progress("NORMALIZE")
    rows, catalog = normalize_index()
    pit = run_index_pit(rows, catalog)
    if pit.get("pit_test_ok"):
        freeze_index_dataset(catalog, pit)
    dump_json(os.path.join(OUT, "READINESS.json"), {"pit_test_ok": pit.get("pit_test_ok"), "download_complete": catalog.get("download_complete"), "n_asof": catalog.get("n_asof")})
    return rows, catalog, pit


def main():
    ensure_v20()
    rows, catalog, pit = prepare_index()
    if not pit.get("pit_test_ok"):
        decision = decide([], False)
        decision["OVERALL"] = "INDEX_PIT_NOT_READY"
        decision["STOP"] = "INCOMPLETE"
        dump_json(os.path.join(OUT, "DECISION.json"), _json_safe(decision))
        _progress("PIT_FAIL", n_asof=catalog.get("n_asof"))
        print("V20_PIT_FAIL", catalog.get("n_asof"), flush=True)
        return decision
    contract = build_contract()
    dump_json(os.path.join(OUT, "CONTRACT.json"), contract)
    _progress("CONTRACT", contract_hash=contract["contract_hash"])
    if not pack_exists():
        pack_panel()
    pack = load_pack()
    xok = exec_ok_matrix(pack)
    elig = eligible(pack, 20)
    if not rows:
        rows = load_index_rows(IDX_CSV)
    cache = build_scores(pack, rows)
    ew = ew_overlapping(pack, elig, xok, RESEARCH[0], VALIDATION[1], HOLD_DAYS)
    done = {}
    part = os.path.join(OUT, "RESULTS_PARTIAL.json")
    if os.path.isfile(part):
        done = dict((r["id"], _hydrate(r)) for r in (load_json(part).get("hypotheses") or []))
    recs = []
    for hyp in HYPOTHESES:
        if hyp["id"] in done and "capital" in done[hyp["id"]]:
            print("V20_RESUME", hyp["id"], flush=True)
            recs.append(done[hyp["id"]])
            continue
        rec = run_one(pack, elig, xok, ew, cache, hyp)
        recs.append(rec)
        dump_json(os.path.join(OUT, "RESULTS_PARTIAL.json"), {"hypotheses": [slim_rec(r) for r in recs], "n": len(recs)})
        _progress("HYP_DONE", id=hyp["id"], n=len(recs))
    recs, candidates, _failures, _fdr = apply_gates(recs)
    dump_json(os.path.join(OUT, "RESULTS.json"), {"hypotheses": [slim_rec(r) for r in recs]})
    decision = decide(candidates, True)
    dump_json(os.path.join(OUT, "DECISION.json"), _json_safe(decision))
    _progress("COMPLETE", overall=decision["OVERALL"], stop=decision["STOP"])
    print("V20_DECISION", decision["OVERALL"], decision["STOP"], "L1", decision["NEW_CANDIDATE"], "IND", decision["NEW_INDEPENDENT_CANDIDATE"], flush=True)
    return decision


if __name__ == "__main__":
    main()
