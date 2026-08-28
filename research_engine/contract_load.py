"""Load locked 14:11 contracts. Never rewrite them."""
from __future__ import print_function

import os

from research_engine.contract_guard import assert_formal_contract
from research_engine.hypothesis import hypothesis_hash
from research_engine.io_util import load_json

DEFAULT_ENGINE_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "market",
    "research_engine",
)


def locked_paths(engine_root=None):
    root = engine_root or DEFAULT_ENGINE_ROOT
    return {
        "root": root,
        "hypothesis": os.path.join(root, "hypothesis"),
        "preregistration": os.path.join(root, "preregistration"),
        "experiments": os.path.join(root, "experiments"),
        "jobs": os.path.join(root, "jobs"),
        "family": os.path.join(root, "registry", "FAM-MOMENTUM-0001.json"),
    }


def load_locked_hypothesis(hypothesis_id, engine_root=None):
    path = os.path.join(locked_paths(engine_root)["hypothesis"], hypothesis_id + ".json")
    hyp = load_json(path)
    attached = dict(hyp)
    if "hypothesis_hash" not in attached:
        attached["hypothesis_hash"] = hypothesis_hash(attached)
    return attached


def load_locked_prereg(hypothesis_id, engine_root=None):
    path = os.path.join(locked_paths(engine_root)["preregistration"], hypothesis_id + ".json")
    return load_json(path)


def load_locked_experiment(experiment_id, engine_root=None):
    path = os.path.join(locked_paths(engine_root)["experiments"], experiment_id + ".json")
    return load_json(path)


def load_all_jobs(engine_root=None):
    path = os.path.join(locked_paths(engine_root)["jobs"], "ALL_JOBS.json")
    return load_json(path)


def jobs_for_node(node_name, engine_root=None):
    payload = load_all_jobs(engine_root)
    return list(payload.get(node_name) or [])


def load_bundle(job, engine_root=None, contracts_root=None):
    if contracts_root:
        hyp = load_json(os.path.join(contracts_root, "hypothesis", job["hypothesis_id"] + ".json"))
        pre = load_json(os.path.join(contracts_root, "preregistration", job["hypothesis_id"] + ".json"))
        exp = load_json(os.path.join(contracts_root, "experiments", job["experiment_id"] + ".json"))
        if "hypothesis_hash" not in hyp:
            hyp = dict(hyp)
            hyp["hypothesis_hash"] = hypothesis_hash(hyp)
    else:
        hyp = load_locked_hypothesis(job["hypothesis_id"], engine_root)
        pre = load_locked_prereg(job["hypothesis_id"], engine_root)
        exp = load_locked_experiment(job["experiment_id"], engine_root)
    assert_formal_contract(job, hyp, pre, exp)
    return hyp, pre, exp


def existing_prereg_pairs(engine_root=None):
    paths = locked_paths(engine_root)
    rows = []
    for hid in ("HYP-0001-A", "HYP-0001-B"):
        hpath = os.path.join(paths["hypothesis"], hid + ".json")
        ppath = os.path.join(paths["preregistration"], hid + ".json")
        if os.path.isfile(hpath) and os.path.isfile(ppath):
            rows.append((load_json(hpath), load_json(ppath)))
    return rows


def existing_experiments(engine_root=None):
    folder = locked_paths(engine_root)["experiments"]
    rows = []
    if not os.path.isdir(folder):
        return rows
    for name in sorted(os.listdir(folder)):
        if name.endswith(".json") and name.startswith("tm-exp-20260825-141158-"):
            rows.append(load_json(os.path.join(folder, name)))
    return rows
