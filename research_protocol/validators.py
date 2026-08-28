"""Protocol gates. Fail closed."""
from __future__ import print_function

from research_protocol.contracts import verify_hash
from research_protocol.errors import ExperimentBlocked
from research_protocol.windows import window_guard


def block_if_hash_mismatch(dataset_dir, expected_sha256):
    return verify_hash(dataset_dir, expected_sha256)


def require_candidate_not_locked(window):
    if window.get("FINAL_OOS_LOCKED") is True:
        raise ExperimentBlocked("final_oos_must_remain_unlocked")
    if window.get("role") != "CANDIDATE_WINDOW":
        raise ExperimentBlocked("window_not_candidate")
    return True


def require_research_sample(signal_index, exit_index, window):
    ok, reason = window_guard(signal_index, exit_index, window, "research")
    if not ok:
        raise ExperimentBlocked(reason)
    return True
