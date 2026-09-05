"""V16 orchestrator. Industry monthly PIT then financial annual. Auto-advance."""
from __future__ import print_function

import csv
import os
import shutil

from research_engine.cn_a_share.io_util import dump_json, load_json
from research_engine.cn_a_share_information_v16 import NEW_PURCHASE
from research_engine.cn_a_share_information_v16.alpha import run_financial_alpha
from research_engine.cn_a_share_information_v16.contract import build_industry_contract
from research_engine.cn_a_share_information_v16.financial_factory import download_profit_annual, normalize_financials
from research_engine.cn_a_share_information_v16.financial_pit import freeze_financial_dataset, run_financial_pit
from research_engine.cn_a_share_information_v16.industry_alpha import run_industry_alpha
from research_engine.cn_a_share_information_v16.industry_factory import download_industry_monthly, normalize_industry
from research_engine.cn_a_share_information_v16.industry_pit import freeze_industry_dataset, run_industry_pit
from research_engine.cn_a_share_information_v16.paths import FIN_REF, IND_NORM, IND_REF, OUT, ensure_v16
from research_engine.cn_a_share_information_v16.quality import run_financial_quality
from research_engine.cn_a_share_information_v16.readiness import financial_ready, industry_ready, write_readiness
from research_engine.cn_a_share_information_v16.source_audit import run_source_audit


def _copy_json(src, name):
    if os.path.isfile(src):
        shutil.copyfile(src, os.path.join(OUT, name))


def load_industry_rows():
    path = os.path.join(IND_NORM, "INDUSTRY_MONTHLY.csv")
    handle = open(path, "r", encoding="utf-8")
    try:
        return list(csv.DictReader(handle))
    finally:
        handle.close()


def decide(ready, fin_cands, ind_cands, fin_ran, ind_ran):
    candidates = list(fin_cands or []) + list(ind_cands or [])
    n = len(candidates)
    independent = [c for c in candidates if c.get("cluster_tag") == "POTENTIALLY_INDEPENDENT"]
    same = [c for c in candidates if c.get("cluster_tag") == "SAME_CLUSTER"]
    fin_status = ready.get("FINANCIAL_ALPHA_STATUS")
    ind_status = ready.get("INDUSTRY_ALPHA_STATUS")
    if n and independent:
        overall = "NEW_INDEPENDENT_CANDIDATE"
        nxt = "CANDIDATE_REPRODUCTION"
        stop = "STOP_A"
    elif n:
        overall = "WEAK_CANDIDATE_SAME_CLUSTER"
        nxt = "KEEP_LOW_VOL_CLUSTER_NO_NEW_SLEEVE"
        stop = "STOP_A"
    elif fin_ran or ind_ran:
        overall = "STOP_B"
        nxt = "NO_NEW_CANDIDATE"
        if not (fin_cands or ind_cands):
            if fin_ran:
                nxt = "FINANCIAL_ALPHA_NO_CANDIDATE"
            if ind_ran and not fin_cands:
                nxt = "FINANCIAL_AND_INDUSTRY_NO_CANDIDATE" if fin_ran else "INDUSTRY_ALPHA_NO_CANDIDATE"
        stop = "STOP_B"
    elif fin_status != "READY" and ind_status != "READY":
        overall = "CURRENT_A_SHARE_INFORMATION_EXHAUSTED_EXCEPT_EXTERNAL"
        nxt = "NO_PURCHASE_DISCUSSION_ONLY"
        stop = "STOP_DATA_BLOCKED"
    else:
        overall = "READY_BUT_NOT_RUN"
        nxt = "RUN_ALPHA"
        stop = "INCOMPLETE"
    return {
        "LEVEL": 1,
        "EXISTING_CANDIDATE": 2,
        "NEW_CANDIDATE": n,
        "CANDIDATE": 2 + n,
        "STRATEGY": 2,
        "PORTFOLIO": 0,
        "PAPER": 0,
        "LIVE": 0,
        "FINANCIAL_ALPHA_READY": ready.get("FINANCIAL_ALPHA_READY"),
        "INDUSTRY_ALPHA_READY": ready.get("INDUSTRY_ALPHA_READY"),
        "FINANCIAL_RAN": fin_ran,
        "INDUSTRY_RAN": ind_ran,
        "OVERALL": overall,
        "NEXT": nxt,
        "STOP": stop,
        "candidate_ids": [c["id"] for c in candidates],
        "independent_ids": [c["id"] for c in independent],
        "same_cluster_ids": [c["id"] for c in same],
        "new_purchase": NEW_PURCHASE,
        "final_oos": "DENIED",
        "h11_h12": "KEEP_LOW_PRIORITY",
    }


def run_v16(max_symbols=None, skip_download=False):
    ensure_v16()
    print("V16_START", flush=True)
    audit_path = os.path.join(OUT, "SOURCE_AUDIT.json")
    if os.path.isfile(audit_path):
        audit = load_json(audit_path)
        print("V16_AUDIT_CACHE", audit.get("verdict"), flush=True)
    else:
        audit = run_source_audit()
    if not skip_download:
        download_profit_annual(max_symbols=max_symbols)
        download_industry_monthly()
    try:
        ind_rows, ind_cat = normalize_industry()
    except Exception as exc:
        print("V16_IND_NORM_FAIL", exc, flush=True)
        ind_rows, ind_cat = [], {}
    _copy_json(os.path.join(IND_REF, "INDUSTRY_CATALOG.json"), "INDUSTRY_CATALOG.json")
    if ind_rows:
        ind_pit = run_industry_pit(ind_rows, ind_cat)
        if ind_pit.get("pit_test_ok"):
            freeze_industry_dataset(ind_cat, ind_pit)
            dump_json(os.path.join(OUT, "INDUSTRY_ALPHA_CONTRACT.json"), build_industry_contract(False))
        else:
            dump_json(os.path.join(OUT, "INDUSTRY_ALPHA_CONTRACT.json"), build_industry_contract(True))
    else:
        ind_pit = {"pit_test_ok": False, "current_only": True, "pit_available": False, "effective_dating": False, "historical_membership": False, "status": "DOWNLOAD_INCOMPLETE"}
        dump_json(os.path.join(OUT, "INDUSTRY_ALPHA_CONTRACT.json"), build_industry_contract(True))
    fin_rows, fin_cat = normalize_financials()
    _copy_json(os.path.join(FIN_REF, "FINANCIAL_CATALOG.json"), "FINANCIAL_CATALOG.json")
    quality = run_financial_quality(fin_rows)
    pit = run_financial_pit(fin_rows, fin_cat)
    if pit.get("pit_test_ok") and pit.get("coverage_ok"):
        freeze_financial_dataset(fin_rows, fin_cat, pit)
    ready = write_readiness(financial_ready(pit, quality, fin_cat), industry_ready(ind_pit))
    fin_cands, ind_cands = [], []
    fin_ran = ind_ran = False
    all_fail = []
    if ready.get("FINANCIAL_ALPHA_READY"):
        _recs, fin_cands = run_financial_alpha(fin_rows)
        fin_ran = True
        all_fail.extend(load_json(os.path.join(OUT, "FAILURES.json")).get("rows") or [])
    else:
        dump_json(os.path.join(OUT, "FINANCIAL_RESULTS.json"), {"blocked": True, "status": ready.get("FINANCIAL_ALPHA_STATUS")})
    if ready.get("INDUSTRY_ALPHA_READY"):
        _irecs, ind_cands, ifail = run_industry_alpha(ind_rows)
        ind_ran = True
        all_fail.extend(ifail)
    else:
        dump_json(os.path.join(OUT, "INDUSTRY_RESULTS.json"), {"blocked": True, "status": ready.get("INDUSTRY_ALPHA_STATUS")})
    dump_json(os.path.join(OUT, "CANDIDATES.json"), {"n": len(fin_cands) + len(ind_cands), "financial": [c["id"] for c in fin_cands], "industry": [c["id"] for c in ind_cands]})
    dump_json(os.path.join(OUT, "FAILURES.json"), {"n": len(all_fail), "rows": all_fail})
    if not os.path.isfile(os.path.join(OUT, "FDR.json")):
        dump_json(os.path.join(OUT, "FDR.json"), {"q": 0.05, "note": "see FINANCIAL_RESULTS and INDUSTRY_FDR"})
    decision = decide(ready, fin_cands, ind_cands, fin_ran, ind_ran)
    dump_json(os.path.join(OUT, "DECISION.json"), decision)
    print("V16_DONE", decision["OVERALL"], decision["NEXT"], flush=True)
    return decision


if __name__ == "__main__":
    run_v16()
