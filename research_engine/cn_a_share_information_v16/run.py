"""V16 orchestrator. Auto-advance until Candidate, domain exhaustion, or payment."""
from __future__ import print_function

import os
import shutil

from research_engine.cn_a_share.io_util import dump_json, load_json
from research_engine.cn_a_share_information_v16 import NEW_PURCHASE
from research_engine.cn_a_share_information_v16.alpha import run_financial_alpha
from research_engine.cn_a_share_information_v16.contract import build_industry_contract
from research_engine.cn_a_share_information_v16.financial_factory import download_profit_annual, load_normalized_rows, normalize_financials
from research_engine.cn_a_share_information_v16.financial_pit import freeze_financial_dataset, run_financial_pit
from research_engine.cn_a_share_information_v16.industry_factory import download_industry_snapshot
from research_engine.cn_a_share_information_v16.industry_pit import run_industry_pit
from research_engine.cn_a_share_information_v16.paths import FIN_REF, IND_REF, OUT, ensure_v16
from research_engine.cn_a_share_information_v16.quality import run_financial_quality
from research_engine.cn_a_share_information_v16.readiness import financial_ready, industry_ready, write_readiness
from research_engine.cn_a_share_information_v16.source_audit import run_source_audit


def _copy_json(src, name):
    if os.path.isfile(src):
        shutil.copyfile(src, os.path.join(OUT, name))


def decide(ready, candidates, fin_ran, ind_ran):
    n = len(candidates or [])
    independent = [c for c in candidates or [] if c.get("cluster_tag") == "POTENTIALLY_INDEPENDENT"]
    same = [c for c in candidates or [] if c.get("cluster_tag") == "SAME_CLUSTER"]
    fin_status = ready.get("FINANCIAL_ALPHA_STATUS")
    ind_status = ready.get("INDUSTRY_ALPHA_STATUS")
    if fin_status != "READY" and ind_status != "READY":
        overall = "CURRENT_A_SHARE_INFORMATION_EXHAUSTED_EXCEPT_EXTERNAL"
        nxt = "NO_PURCHASE_DISCUSSION_ONLY"
        stop = "STOP_DATA_BLOCKED"
    elif n == 0:
        overall = "STOP_B"
        nxt = "FINANCIAL_ALPHA_NO_CANDIDATE" if fin_ran else "NO_FINANCIAL_ALPHA_RUN"
        if not fin_ran and fin_status != "READY":
            overall = "FINANCIAL_BLOCKED_INDUSTRY_BLOCKED"
            nxt = "CURRENT_A_SHARE_INFORMATION_EXHAUSTED_EXCEPT_EXTERNAL"
        stop = "STOP_B"
    elif independent:
        overall = "NEW_INDEPENDENT_CANDIDATE"
        nxt = "CANDIDATE_REPRODUCTION"
        stop = "STOP_A"
    else:
        overall = "WEAK_CANDIDATE_SAME_CLUSTER"
        nxt = "KEEP_LOW_VOL_CLUSTER_NO_NEW_SLEEVE"
        stop = "STOP_A"
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
        "candidate_ids": [c["id"] for c in candidates or []],
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
    ind_norms, ind_cat = download_industry_snapshot()
    ind_pit = run_industry_pit(ind_norms, ind_cat)
    dump_json(os.path.join(OUT, "INDUSTRY_ALPHA_CONTRACT.json"), build_industry_contract(True))
    dump_json(os.path.join(OUT, "INDUSTRY_RESULTS.json"), {"blocked": True, "status": "INDUSTRY_PIT_BLOCKED", "hypotheses": []})
    if not skip_download:
        download_profit_annual(max_symbols=max_symbols)
    rows, catalog = normalize_financials()
    _copy_json(os.path.join(FIN_REF, "FINANCIAL_CATALOG.json"), "FINANCIAL_CATALOG.json")
    _copy_json(os.path.join(IND_REF, "INDUSTRY_CATALOG.json"), "INDUSTRY_CATALOG.json")
    quality = run_financial_quality(rows)
    pit = run_financial_pit(rows, catalog)
    if pit.get("pit_test_ok") and pit.get("coverage_ok"):
        freeze_financial_dataset(rows, catalog, pit)
    fin_g = financial_ready(pit, quality, catalog)
    ind_g = industry_ready(ind_pit)
    ready = write_readiness(fin_g, ind_g)
    candidates = []
    fin_ran = False
    if ready.get("FINANCIAL_ALPHA_READY"):
        _recs, candidates = run_financial_alpha(rows)
        fin_ran = True
    else:
        dump_json(os.path.join(OUT, "FINANCIAL_RESULTS.json"), {"blocked": True, "status": ready.get("FINANCIAL_ALPHA_STATUS")})
        dump_json(os.path.join(OUT, "CANDIDATES.json"), {"n": 0, "ids": []})
        if not os.path.isfile(os.path.join(OUT, "FAILURES.json")):
            dump_json(
                os.path.join(OUT, "FAILURES.json"),
                {
                    "n": 1,
                    "rows": [
                        {
                            "id": "FINANCIAL_DOMAIN",
                            "family": "DATA",
                            "mechanism": "PIT financial panel",
                            "why_failed": [k for k, v in (fin_g.get("checks") or {}).items() if not v] or ["not_ready"],
                            "reopen": "New free source with announcement dates and coverage. Do not buy.",
                        }
                    ],
                },
            )
        if not os.path.isfile(os.path.join(OUT, "FDR.json")):
            dump_json(os.path.join(OUT, "FDR.json"), {"q": 0.05, "adjusted_p": [], "discoveries": []})
    decision = decide(ready, candidates, fin_ran, False)
    dump_json(os.path.join(OUT, "DECISION.json"), decision)
    print("V16_DONE", decision["OVERALL"], decision["NEXT"], flush=True)
    return decision


if __name__ == "__main__":
    run_v16()
