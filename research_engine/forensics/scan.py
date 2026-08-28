"""Load frozen rankings, contracts, results, and dataset manifests. No Final OOS."""
from __future__ import print_function

import json
import os

from research_engine.holdout import final_oos_access


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENGINE_DATA = os.path.join(ROOT, "data", "market", "research_engine")
IMMUTABLE = os.path.join(ROOT, "data", "market", "immutable")
DOCS = os.path.join(ROOT, "docs", "research_engine")
RESULTS = os.path.join(ENGINE_DATA, "results")

RANKING_FILES = (
    ("HYP-0001", os.path.join(ENGINE_DATA, "registry", "HOME_ROWS.json")),
    ("FACTOR_DISCOVERY_V0.1", os.path.join(ENGINE_DATA, "factor_discovery", "FACTOR_RANKING_V0.1.json")),
    ("RESEARCH_ENGINE_V0.5", os.path.join(ENGINE_DATA, "strategy_discovery", "STRATEGY_RANKING_V0.5.json")),
    ("PROFIT_DISCOVERY_V0.6", os.path.join(ENGINE_DATA, "profit_discovery", "PROFIT_RANKING_V0.6.json")),
    ("CROSS_ASSET_ALPHA_V0.8", os.path.join(ENGINE_DATA, "cross_asset", "CROSS_ASSET_RANKING_V0.8.json")),
    ("REGIME_TRANSITION_V0.9", os.path.join(ENGINE_DATA, "regime_transition", "REGIME_RANKING_V0.9.json")),
    ("CROSS_RESIDUAL_V0.91", os.path.join(ENGINE_DATA, "cross_residual", "RESIDUAL_RANKING_V0.91.json")),
)


def deny_oos():
    try:
        final_oos_access(reason="alpha_forensics")
    except Exception as exc:
        if type(exc).__name__ != "FinalOosAccessDenied":
            raise
        return True
    raise RuntimeError("FINAL_OOS_WAS_NOT_DENIED")


def load_json(path):
    if not os.path.isfile(path):
        return None
    handle = open(path, "r")
    try:
        return json.load(handle)
    finally:
        handle.close()


def load_rankings():
    deny_oos()
    out = []
    for family, path in RANKING_FILES:
        payload = load_json(path)
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        out.append(
            {
                "family": family,
                "path": rel,
                "exists": payload is not None,
                "payload": payload,
            }
        )
    return out


def load_dataset_manifests():
    deny_oos()
    rows = []
    if not os.path.isdir(IMMUTABLE):
        return rows
    for name in sorted(os.listdir(IMMUTABLE)):
        path = os.path.join(IMMUTABLE, name, "manifest.json")
        payload = load_json(path)
        if payload:
            rows.append(payload)
    return rows


def list_contract_docs():
    deny_oos()
    rows = []
    if not os.path.isdir(DOCS):
        return rows
    for name in sorted(os.listdir(DOCS)):
        low = name.lower()
        if "contract" not in low:
            continue
        if not name.endswith(".md"):
            continue
        rows.append(os.path.join("docs", "research_engine", name).replace("\\", "/"))
    return rows


def scan_hyp0001_results():
    """Count HYP-0001 formal result files. Dates/labels only. No OOS payload."""
    deny_oos()
    n_files = 0
    verdicts = {}
    if not os.path.isdir(RESULTS):
        return {"n_files": 0, "verdicts": {}, "note": "results/ missing"}
    for dirpath, dirnames, filenames in os.walk(RESULTS):
        rel = os.path.relpath(dirpath, ROOT).replace("\\", "/")
        if "final_oos" in rel:
            dirnames[:] = []
            continue
        for name in filenames:
            if not name.startswith("HYP-0001"):
                continue
            if not name.endswith(".json"):
                continue
            n_files += 1
            payload = load_json(os.path.join(dirpath, name))
            if not payload:
                continue
            result = payload.get("result") or {}
            verdict = result.get("verdict") or {}
            for key, value in verdict.items():
                bucket = verdicts.setdefault(key, {})
                bucket[value] = bucket.get(value, 0) + 1
    return {"n_files": n_files, "verdicts": verdicts}


def _fdr_count(fdr):
    if not fdr:
        return 0
    disc = fdr.get("discoveries")
    if isinstance(disc, list):
        return len(disc)
    if disc is None:
        return 0
    try:
        return int(disc)
    except Exception:
        return 0


def extract_family_facts(row):
    payload = row.get("payload") or {}
    facts = {
        "family": row["family"],
        "path": row["path"],
        "exists": row["exists"],
        "outcome": payload.get("outcome"),
        "n_hypotheses": 0,
        "labels": [],
        "fdr_discoveries": 0,
        "research_trades": [],
        "validation_trades": [],
        "research_tr": [],
        "research_p": [],
        "occupancy": [],
    }
    if payload is None:
        return facts
    if isinstance(payload, list):
        facts["n_hypotheses"] = 0
        if row["family"] == "HYP-0001":
            facts["outcome"] = facts.get("outcome") or "WEAK_SUPPORT_NOT_A_BOOK"
        return facts
    facts["fdr_discoveries"] = _fdr_count(payload.get("fdr") or {})
    counts = payload.get("counts")
    if isinstance(counts, dict):
        facts["counts"] = counts
        total = 0
        for key in ("REJECTED", "PROMISING", "CANDIDATE", "INCONCLUSIVE", "WEAK_EDGE", "NO_EDGE"):
            total += int(counts.get(key) or 0)
        facts["n_hypotheses"] = total
    hyps = payload.get("hypotheses") or payload.get("candidates") or []
    if hyps:
        facts["n_hypotheses"] = len(hyps)
    for hyp in hyps:
        if not isinstance(hyp, dict):
            continue
        hid = hyp.get("hypothesis_id") or hyp.get("name") or hyp.get("kind")
        facts["labels"].append("%s:%s" % (hid, hyp.get("label") or hyp.get("status")))
        research = hyp.get("research") or {}
        validation = hyp.get("validation") or {}
        if research.get("n_trade") is not None:
            facts["research_trades"].append(int(research.get("n_trade") or 0))
        if validation.get("n_trade") is not None:
            facts["validation_trades"].append(int(validation.get("n_trade") or 0))
        if research.get("total_return") is not None:
            facts["research_tr"].append(float(research.get("total_return")))
        if research.get("raw_p") is not None:
            facts["research_p"].append(float(research.get("raw_p")))
        if research.get("occupancy") is not None:
            facts["occupancy"].append(float(research.get("occupancy")))
    if row["family"] == "PROFIT_DISCOVERY_V0.6":
        for port in payload.get("portfolios") or []:
            research = (port.get("portfolio") or {}).get("research") or {}
            if research.get("total_return") is not None:
                facts["research_tr"].append(float(research.get("total_return")))
            if research.get("trade_count") is not None:
                facts["research_trades"].append(int(research.get("trade_count") or 0))
    if row["family"] == "HYP-0001" and not facts["outcome"]:
        facts["outcome"] = "WEAK_SUPPORT_NOT_A_BOOK"
    return facts


def scan_index():
    rankings = load_rankings()
    return {
        "rankings": [
            {
                "family": r["family"],
                "path": r["path"],
                "exists": r["exists"],
                "outcome": None if not isinstance(r.get("payload"), dict) else (r.get("payload") or {}).get("outcome"),
            }
            for r in rankings
        ],
        "datasets": [
            {
                "dataset_id": m.get("dataset_id"),
                "asset": m.get("logical_symbol"),
                "timeframe": m.get("timeframe"),
                "n": m.get("row_count"),
                "start": m.get("actual_start_utc") or m.get("data_start_utc"),
                "end": m.get("actual_end_utc") or m.get("data_end_utc"),
                "sha256": m.get("sha256"),
            }
            for m in load_dataset_manifests()
        ],
        "contracts": list_contract_docs(),
        "hyp0001_results": scan_hyp0001_results(),
    }
