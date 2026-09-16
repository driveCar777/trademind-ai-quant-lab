"""Run manifest: unified, reproducible record of WHICH code / data / model produced a result.

Deterministic (semantic) fields drive `manifest_hash`; volatile identity/time fields (run_id,
generated_at_utc, git_commit, branch, env) are recorded SEPARATELY so time/commit changes never
pollute the reproducibility hash. Read-only: imports constants, never modifies alpha/baseline.
"""
from __future__ import print_function

import datetime
import hashlib
import json
import os
import platform
import subprocess

from research_engine.cn_a_short import (CONTRACT_ID, DERIVED_DATASET_ID, MIN_ELIGIBLE, OOS_WINDOW,
                                        RESEARCH_WINDOW, SEED, UPSTREAM_DATASET_HASH,
                                        UPSTREAM_DATASET_ID, VALIDATION_WINDOW)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CONTRACT_DOC = os.path.join(ROOT, "docs", "a_short", "A_SHORT_D1_RESEARCH_CONTRACT.md")

MODEL_ID = "20D_MOMENTUM_BASELINE"
MODEL_VERSION = "v1"


def _sha256_str(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _git(args):
    try:
        return subprocess.check_output(["git"] + args, cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


def _contract_hash():
    try:
        return hashlib.sha256(open(CONTRACT_DOC, "rb").read()).hexdigest()
    except Exception:
        return None


def _cost_version():
    """Fingerprint of the canonical cost constants (read-only)."""
    try:
        from research_engine.cn_a_share_alpha.cost import COMMISSION, TRANSFER, SLIPPAGE, STAMP_NEW
        from research_engine.cn_a_short.cost import MIN_FEE, LOT
        payload = json.dumps({"commission": COMMISSION, "transfer": TRANSFER, "slippage": SLIPPAGE,
                              "stamp_new": STAMP_NEW, "min_fee": MIN_FEE, "lot": LOT}, sort_keys=True)
        return "cost/" + _sha256_str(payload)[:12]
    except Exception:
        return "cost/UNKNOWN"


def _execution_version():
    """Semantic version of the execution simulator (capital-path exit recovery)."""
    try:
        from research_engine.cn_a_short.baseline import EXIT_CARRY_MAX
        return "capital_path_exit_recovery/v1;EXIT_CARRY_MAX=%d" % EXIT_CARRY_MAX
    except Exception:
        return "capital_path_exit_recovery/v1"


def _dependencies():
    deps = {}
    try:
        import numpy
        deps["numpy"] = numpy.__version__
    except Exception:
        pass
    return deps


def universe_definition(config=None):
    """Structured universe definition (read from config/defaults; does NOT change anything)."""
    config = config or {}
    return {
        "boards": config.get("boards", "ALL"),
        "exclude_st": config.get("exclude_st", False),
        "min_hist": config.get("min_hist", 20),
        "min_eligible": config.get("min_eligible", MIN_ELIGIBLE),
    }


def new_run_id(experiment):
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    exp = "".join(c if (c.isalnum() or c in "_-") else "_" for c in str(experiment)).strip("_") or "run"
    return "A_SHORT_%s_%s" % (exp, ts)


def build_manifest(experiment, config=None, derived_dataset_hash=None, status=None):
    """Return (manifest_dict, manifest_hash). manifest_hash covers SEMANTIC fields only."""
    deterministic = {
        "contract_id": CONTRACT_ID,
        "contract_hash": _contract_hash(),
        "upstream_dataset_id": UPSTREAM_DATASET_ID,
        "upstream_hash": UPSTREAM_DATASET_HASH,
        "derived_dataset_id": DERIVED_DATASET_ID,
        "derived_dataset_hash": derived_dataset_hash,
        "seed": SEED,
        "research_window": list(RESEARCH_WINDOW),
        "validation_window": list(VALIDATION_WINDOW),
        "oos_window": list(OOS_WINDOW),
        "model_id": MODEL_ID,
        "model_version": MODEL_VERSION,
        "execution_version": _execution_version(),
        "cost_version": _cost_version(),
        "universe_definition": universe_definition(config),
    }
    manifest_hash = _sha256_str(json.dumps(deterministic, sort_keys=True, default=str))
    identity = {
        "run_id": new_run_id(experiment),
        "experiment": experiment,
        "generated_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "git_commit": _git(["rev-parse", "HEAD"]),
        "branch": _git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "dirty": bool(_git(["status", "--porcelain"])),
        "python_version": platform.python_version(),
        "os": platform.system(),
        "platform": platform.platform(),
        "dependencies": _dependencies(),
        "status": status,
    }
    manifest = {}
    manifest.update(deterministic)
    manifest.update(identity)
    manifest["manifest_hash"] = manifest_hash                # semantic; excludes time/commit/env
    manifest["_hash_excludes"] = ["run_id", "experiment", "generated_at_utc", "git_commit", "branch",
                                  "dirty", "python_version", "os", "platform", "dependencies", "status",
                                  "manifest_hash"]
    return manifest, manifest_hash


def manifest_hash_of(manifest):
    """Recompute the semantic hash from a manifest dict (for reproducibility checks)."""
    excl = set(manifest.get("_hash_excludes", []))
    deterministic = dict((k, v) for k, v in manifest.items() if k not in excl and k != "_hash_excludes")
    return _sha256_str(json.dumps(deterministic, sort_keys=True, default=str))


__all__ = ["build_manifest", "manifest_hash_of", "new_run_id", "universe_definition",
           "MODEL_ID", "MODEL_VERSION"]
