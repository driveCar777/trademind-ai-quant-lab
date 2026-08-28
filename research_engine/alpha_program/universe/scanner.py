"""Walk docs/data/research_engine/tests/registry. Do not read Final OOS payload."""
from __future__ import print_function

import json
import os
import re

from research_engine.holdout import final_oos_access
from research_protocol.hashing import canonical_hash


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SKIP_DIR_NAMES = {
    "__pycache__",
    ".git",
    "node_modules",
    ".pytest_cache",
    "final_oos",
    "longrun",
    "mine",
}
SKIP_FILE_SUFFIX = (".csv", ".pyc", ".png", ".jpg", ".zip", ".7z")
HASH_RE = re.compile(r"\b[a-f0-9]{64}\b")
HYP_RE = re.compile(r"\bHYP-[A-Z0-9]+-\d{4}\b")
DS_RE = re.compile(r"\btm-market-[A-Z0-9]+-(?:M15|H1|H4|D1)-\d{8}-\d+\b")


def _assert_no_oos():
    try:
        final_oos_access(reason="alpha_universe_scan")
    except Exception as exc:
        if type(exc).__name__ != "FinalOosAccessDenied":
            raise
        return True
    raise RuntimeError("FINAL_OOS_WAS_NOT_DENIED")


def _skip_dir(name):
    return name in SKIP_DIR_NAMES or name.startswith(".")


def _walk(rel):
    base = os.path.join(ROOT, rel)
    if not os.path.isdir(base):
        return
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if not _skip_dir(d)]
        for name in filenames:
            if name.endswith(SKIP_FILE_SUFFIX):
                continue
            path = os.path.join(dirpath, name)
            rel_path = os.path.relpath(path, ROOT).replace("\\", "/")
            if "final_oos" in rel_path.replace("\\", "/"):
                continue
            yield rel_path, path


def _read_text(path, limit=400000):
    try:
        handle = open(path, "r")
        try:
            return handle.read(limit)
        finally:
            handle.close()
    except Exception:
        return ""


def _read_json(path):
    try:
        handle = open(path, "r")
        try:
            return json.load(handle)
        finally:
            handle.close()
    except Exception:
        return None


def _record(rid, typ, mechanism, asset, timeframe, status, evidence, next_action, extra=None):
    row = {
        "id": rid,
        "type": typ,
        "mechanism": mechanism,
        "asset": asset,
        "timeframe": timeframe,
        "status": status,
        "evidence": evidence,
        "next_action": next_action,
    }
    if extra:
        row.update(extra)
    return row


def _scan_manifests():
    rows = []
    hashes = {}
    for rel, path in _walk(os.path.join("data", "market", "immutable")):
        if not rel.endswith("manifest.json"):
            continue
        manifest = _read_json(path)
        if not isinstance(manifest, dict):
            continue
        ds = manifest.get("dataset_id") or rel
        start = manifest.get("actual_start_utc") or manifest.get("data_start_utc")
        end = manifest.get("actual_end_utc") or manifest.get("data_end_utc")
        hashes[ds] = manifest.get("sha256")
        rows.append(
            _record(
                ds,
                "dataset",
                "immutable broker D1/intraday bars",
                manifest.get("logical_symbol"),
                manifest.get("timeframe"),
                "DONE",
                "manifest %s %s..%s sha256=%s n=%s" % (
                    rel, start, end, (manifest.get("sha256") or "")[:16], manifest.get("row_count"),
                ),
                "do_not_overwrite; coverage check is a separate probe",
                {"hash": manifest.get("sha256"), "lineage": "data_layer_v0.1"},
            )
        )
    return rows, hashes


def _scan_rankings():
    rows = []
    mapping = [
        (
            os.path.join("data", "market", "research_engine", "factor_discovery", "FACTOR_RANKING_V0.1.json"),
            "FACTOR_DISCOVERY_V0.1",
            "factor",
            "short-horizon factor farm on qualified bars",
            "FAILED",
            "NO_USEFUL_FACTORS_FOUND; do not rescan indicators",
        ),
        (
            os.path.join("data", "market", "research_engine", "strategy_discovery", "STRATEGY_RANKING_V0.5.json"),
            "RESEARCH_ENGINE_V0.5",
            "experiment",
            "state-level strategy sketches",
            "FAILED",
            "NO_USEFUL_STRATEGIES_FOUND; do not reuse as live book",
        ),
        (
            os.path.join("data", "market", "research_engine", "profit_discovery", "PROFIT_RANKING_V0.6.json"),
            "PROFIT_DISCOVERY_V0.6",
            "experiment",
            "state-level path after V0.6 cost/risk",
            "FAILED",
            "WEAK_EDGE_ONLY leftover only; do not retune",
        ),
        (
            os.path.join("data", "market", "research_engine", "cross_asset", "CROSS_ASSET_RANKING_V0.8.json"),
            "CROSS_ASSET_ALPHA_V0.8",
            "experiment",
            "next-day dollar-proxy cross asset",
            "FAILED",
            "NO_CANDIDATE; 3/3 FALSIFIED; do not add HYP-XA-0004",
        ),
        (
            os.path.join("data", "market", "research_engine", "regime_transition", "REGIME_RANKING_V0.9.json"),
            "REGIME_TRANSITION_V0.9",
            "experiment",
            "regime transition (delta state)",
            "FAILED",
            "NO_CANDIDATE; do not retune ADX/hold/VOL",
        ),
        (
            os.path.join("data", "market", "research_engine", "cross_residual", "RESIDUAL_RANKING_V0.91.json"),
            "CROSS_RESIDUAL_V0.91",
            "experiment",
            "GOLD/OIL log-spread residual",
            "FAILED",
            "NO_CANDIDATE; do not retune SMA60/percentiles",
        ),
    ]
    for rel, rid, typ, mech, status, nxt in mapping:
        path = os.path.join(ROOT, rel)
        payload = _read_json(path)
        if not isinstance(payload, dict):
            rows.append(_record(rid, typ, mech, "MULTI", "MULTI", "UNKNOWN", "missing %s" % rel, "locate ranking"))
            continue
        outcome = payload.get("outcome")
        evidence = "%s outcome=%s" % (rel.replace("\\", "/"), outcome)
        if rid == "PROFIT_DISCOVERY_V0.6":
            counts = payload.get("counts") or {}
            evidence += " CANDIDATE=%s WEAK_EDGE=%s" % (counts.get("CANDIDATE"), counts.get("WEAK_EDGE"))
        if rid == "CROSS_ASSET_ALPHA_V0.8":
            labels = []
            for hyp in payload.get("hypotheses") or []:
                labels.append("%s:%s" % (hyp.get("hypothesis_id"), hyp.get("label")))
            evidence += " " + ",".join(labels)
        rows.append(_record(rid, typ, mech, "MULTI", "D1/intraday", status, evidence, nxt, {"hash": payload.get("search_space_hash")}))
        for hyp in payload.get("hypotheses") or []:
            hid = hyp.get("hypothesis_id")
            if not hid:
                continue
            rows.append(
                _record(
                    hid,
                    "hypothesis",
                    hyp.get("feature") or hyp.get("kind") or mech,
                    hyp.get("target_asset") or "MULTI",
                    "D1",
                    "FAILED" if hyp.get("label") in ("FALSIFIED",) or status == "FAILED" else status,
                    "%s label=%s why=%s" % (rel.replace("\\", "/"), hyp.get("label"), ",".join(hyp.get("dataset_why") or hyp.get("label_why") or [])),
                    "do_not_repeat",
                    {"lineage": rid, "hash": hyp.get("content_hash")},
                )
            )
    return rows


def _scan_docs_and_code():
    rows = []
    seen_h = {}
    seen_ds = {}
    hashes = []
    file_count = 0
    for rel_root in ("docs", "research_engine", "tests", "registry"):
        for rel, path in _walk(rel_root):
            file_count += 1
            text = _read_text(path)
            if not text:
                continue
            for hid in HYP_RE.findall(text):
                seen_h[hid] = rel
            for ds in DS_RE.findall(text):
                seen_ds[ds] = rel
            if rel.endswith(".md") or rel.endswith(".json") or rel.endswith(".py"):
                for h in HASH_RE.findall(text.lower()):
                    hashes.append((rel, h))
    rows.append(
        _record(
            "SCAN-INDEX",
            "inventory",
            "filesystem walk",
            None,
            None,
            "DONE",
            "files=%s unique_hyp=%s unique_dataset=%s hash_mentions=%s" % (
                file_count, len(seen_h), len(seen_ds), len(hashes),
            ),
            "keep scanner as authority over chat memory",
        )
    )
    known = {
        "HYP-0001": ("FAILED", "14:11 persistence; do not reopen"),
        "HYP-XA-0001": ("FAILED", "V0.8 FALSIFIED"),
        "HYP-XA-0002": ("FAILED", "V0.8 FALSIFIED"),
        "HYP-XA-0003": ("FAILED", "V0.8 FALSIFIED"),
        "HYP-RT-0001": ("FAILED", "V0.9 FALSIFIED; do not retune"),
        "HYP-RT-0002": ("FAILED", "V0.9 INCONCLUSIVE; do not retune"),
        "HYP-RT-0003": ("FAILED", "V0.9 INCONCLUSIVE; do not retune"),
        "HYP-XR-0001": ("FAILED", "V0.91 FALSIFIED; do not retune"),
        "HYP-XR-0002": ("FAILED", "V0.91 no edge; do not retune"),
        "HYP-XR-0003": ("FAILED", "V0.91 no edge; do not retune"),
    }
    for hid, rel in sorted(seen_h.items()):
        status, nxt = known.get(hid, ("UNKNOWN", "classify before contracting"))
        rows.append(_record(hid, "hypothesis", "mentioned in tree", None, None, status, rel, nxt))
    # Rankings above already emit REGIME_TRANSITION_V0.9 / CROSS_RESIDUAL_V0.91 when present.
    blocked = [
        ("RP-IV", "implied volatility / options", "IV", "BLOCKED", "no options tape"),
        ("RP-CARRY", "carry / rate differential", "RATES", "BLOCKED", "no rates tape"),
        ("RP-FUNDING", "funding / basis", "CRYPTO/FUTURES", "BLOCKED", "no funding tape"),
        ("NEWS-01", "news / text event", "NEWS", "BLOCKED", "no news feed"),
    ]
    for rid, mech, asset, status, why in blocked:
        rows.append(_record(rid, "factor", mech, asset, None, status, why, "do_not_fake_data"))
    return rows


def build_universe():
    _assert_no_oos()
    rows = []
    ds_rows, ds_hashes = _scan_manifests()
    rows.extend(ds_rows)
    rows.extend(_scan_rankings())
    rows.extend(_scan_docs_and_code())
    seen = set()
    uniq = []
    for row in rows:
        key = (row["id"], row["type"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(row)
    payload = {
        "program_id": "ALPHA_UNIVERSE_DB_V1",
        "n": len(uniq),
        "FINAL_OOS_TOUCHED": False,
        "dataset_hashes": ds_hashes,
        "records": uniq,
    }
    payload["content_hash"] = canonical_hash(
        {"n": payload["n"], "ids": [r["id"] for r in uniq], "oos": False}
    )
    return payload


def dump_universe(path):
    payload = build_universe()
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    handle = open(path, "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    return payload
