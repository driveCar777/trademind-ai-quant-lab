"""Quote + acquire pack E. Stops on credential or over-credit. No ticks."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.data_sources.pipeline import AcquisitionBlocked
from research_engine.local_fs import force_project_temp
from research_engine.v6_external.acquire import acquire_status, run_acquire


def main():
    force_project_temp()
    status = acquire_status()
    print("V6 acquire status", status["status"])
    if status["status"] == "CREDENTIAL_REQUIRED":
        print("HUMAN_REQUIRED: put TRADEMIND_DATABENTO_API_KEY in .env")
        print("Then say: key is in .env, continue V6 acquire.")
        print("Do not open $199 Standard.")
        return 2
    try:
        result = run_acquire()
    except AcquisitionBlocked as exc:
        print("STOPPED", exc)
        return 2
    print("ACQUIRED", result["quote"]["total_usd"], "usd")
    for row in result["frozen"]:
        print(row["dataset_id"], row["sha256"][:16], row["qualification"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
