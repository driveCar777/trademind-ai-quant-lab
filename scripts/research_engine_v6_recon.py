"""Print V6 catalog + pack recommendation. Does not download."""
from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.local_fs import force_project_temp
from research_engine.v6_external.acquire import acquire_status
from research_engine.v6_external.catalog import catalog, min_pack, recommended_pack
from research_engine.v6_external.contract import sealed_contract


def main():
    force_project_temp()
    cat = catalog()
    packs = min_pack()
    status = acquire_status()
    space = sealed_contract()
    print("V6 recon")
    print("dataset", cat["dataset"]["dataset_id"], "from", cat["dataset"]["available_from_utc"])
    print("credits", cat["pricing"]["new_user_credits_usd"], "standard", cat["pricing"]["standard_usd_per_month"])
    print("recommended_pack", recommended_pack())
    print("acquire_status", status["status"])
    print("term_structure_hash", space["search_space_hash"])
    print("choose", [row["id"] for row in packs["packs"] if row.get("choose")])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
