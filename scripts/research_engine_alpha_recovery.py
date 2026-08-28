"""Alpha Recovery Program V1.0. Forensics + inventory + one paper contract. Does not run it."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.forensics.pipeline import run


def main():
    payload, extra = run(write=True, probe=True)
    print(
        "ALPHA_RECOVERY",
        payload.get("selection", {}).get("chosen"),
        payload.get("contract", {}).get("search_space_hash"),
        "executed=%s" % payload.get("executed_new_family"),
        "probe=%s" % payload.get("capability_overall"),
    )
    for path in extra.get("written") or []:
        print("wrote", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
