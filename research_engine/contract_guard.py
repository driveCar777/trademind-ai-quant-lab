"""Formal HYP-0001 identity. Locked 14:11 files are the only source of truth."""
from __future__ import print_function

from research_engine.errors import ContractMismatch

FORMAL_FAMILY = "FAM-MOMENTUM-0001"
FORMAL_PARENT = "HYP-0001"
DRAFT_FAMILY = "FAM-PERSISTENCE-0001"

LOCKED_PREREG_HASH = {
    "HYP-0001-A": "485d56a8f5a8e6822231760be240500ce6deb194471cde78172c3b5e4630b6d8",
    "HYP-0001-B": "fbd14d199ba6390ac91f8700d48053ff75c99d7510183d58eeb1a101238cd3db",
}

FORBIDDEN_IDS = (None, "", "PENDING", "pending")


def _bad_id(value):
    return value in FORBIDDEN_IDS


def assert_formal_family(family_id, where="family_id"):
    if family_id == DRAFT_FAMILY:
        raise ContractMismatch("CONTRACT_MISMATCH:%s=FAM-PERSISTENCE-0001" % where)
    if family_id != FORMAL_FAMILY:
        raise ContractMismatch("CONTRACT_MISMATCH:%s=%s" % (where, family_id))
    return True


def assert_locked_prereg_hash(hypothesis_id, preregister_hash):
    expected = LOCKED_PREREG_HASH.get(hypothesis_id)
    if expected is None:
        raise ContractMismatch("CONTRACT_MISMATCH:unknown_hypothesis:%s" % hypothesis_id)
    if preregister_hash != expected:
        raise ContractMismatch("CONTRACT_MISMATCH:preregister_hash")
    return True


def assert_continuation_contract(hyp, pre):
    texts = [
        str((hyp or {}).get("target_definition") or ""),
        str((hyp or {}).get("null_hypothesis") or ""),
        str((pre or {}).get("null_hypothesis") or ""),
        str((pre or {}).get("alternative_hypothesis") or ""),
    ]
    blob = " ".join(texts)
    if "continuation_mean" not in blob:
        raise ContractMismatch("CONTRACT_MISMATCH:missing_continuation_mean")
    if "unconditional mean" in blob.lower() and "continuation_mean = 0" not in blob:
        raise ContractMismatch("CONTRACT_MISMATCH:unconditional_mean_h0")
    return True


def assert_formal_contract(job, hyp, pre, exp):
    if _bad_id((job or {}).get("experiment_id")):
        raise ContractMismatch("CONTRACT_MISMATCH:experiment_id=PENDING")
    if _bad_id((exp or {}).get("experiment_id")):
        raise ContractMismatch("CONTRACT_MISMATCH:experiment_id=PENDING")
    if job.get("experiment_id") != exp.get("experiment_id"):
        raise ContractMismatch("CONTRACT_MISMATCH:experiment_id_mismatch")
    hid = job.get("hypothesis_id")
    if hid not in LOCKED_PREREG_HASH:
        raise ContractMismatch("CONTRACT_MISMATCH:hypothesis_id=%s" % hid)
    if hyp.get("hypothesis_id") != hid or pre.get("hypothesis_id") != hid:
        raise ContractMismatch("CONTRACT_MISMATCH:hypothesis_file_id")
    if exp.get("hypothesis_id") != hid:
        raise ContractMismatch("CONTRACT_MISMATCH:experiment_hypothesis")
    assert_formal_family(job.get("family_id"), "job.family_id")
    assert_formal_family(hyp.get("family_id"), "hypothesis.family_id")
    assert_formal_family(pre.get("family_id") or job.get("family_id"), "prereg.family_id")
    assert_formal_family(exp.get("family_id"), "experiment.family_id")
    if (hyp.get("parent_hypothesis_id") or job.get("parent_hypothesis_id")) not in (FORMAL_PARENT, None):
        if hyp.get("parent_hypothesis_id") != FORMAL_PARENT:
            raise ContractMismatch("CONTRACT_MISMATCH:parent")
    assert_locked_prereg_hash(hid, job.get("preregister_hash"))
    assert_locked_prereg_hash(hid, pre.get("preregister_hash"))
    if exp.get("preregister_hash") != pre.get("preregister_hash"):
        raise ContractMismatch("CONTRACT_MISMATCH:experiment_prereg_hash")
    if job.get("dataset_id") != exp.get("dataset_id"):
        raise ContractMismatch("CONTRACT_MISMATCH:dataset_id")
    job_hash = job.get("dataset_sha256") or job.get("dataset_hash")
    exp_hash = exp.get("dataset_sha256")
    if job_hash and exp_hash and job_hash != exp_hash:
        raise ContractMismatch("CONTRACT_MISMATCH:dataset_hash")
    assert_continuation_contract(hyp, pre)
    if _bad_id(job.get("preregister_hash")):
        raise ContractMismatch("CONTRACT_MISMATCH:preregister_hash=PENDING")
    return True


def assert_formal_result(payload):
    lineage = payload.get("lineage") or payload.get("lineage_partial") or {}
    if _bad_id(payload.get("experiment_id")) and _bad_id(lineage.get("experiment_id")):
        raise ContractMismatch("CONTRACT_MISMATCH:result_experiment_id")
    family = payload.get("family_id") or lineage.get("family_id")
    if family:
        assert_formal_family(family, "result.family_id")
    if payload.get("family_id") == DRAFT_FAMILY:
        raise ContractMismatch("CONTRACT_MISMATCH:result_draft_family")
    hid = payload.get("hypothesis_id")
    pre_hash = payload.get("preregister_hash") or lineage.get("preregister_hash")
    if hid and pre_hash:
        assert_locked_prereg_hash(hid, pre_hash)
    result = payload.get("result") or {}
    research = result.get("research") or payload.get("research") or {}
    cont = research.get("continuation") or {}
    if "continuation_mean" not in cont and payload.get("metric") != "continuation_mean":
        raise ContractMismatch("CONTRACT_MISMATCH:result_missing_continuation_mean")
    return True
