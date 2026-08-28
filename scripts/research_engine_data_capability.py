"""Check D1/H1/M15 coverage. Optional read-only MT5 probe. Never overwrite."""
from __future__ import print_function

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.alpha_program.data_capability import build_plan, inventory_disk, probe_mt5, render_plan_md


def main():
    disk = inventory_disk()
    probe = probe_mt5()
    plan = build_plan(disk, probe)
    out_dir = os.path.join(ROOT, "data", "market", "research_engine", "alpha_program")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    payload = {"disk": disk, "probe": probe, "plan": plan}
    handle = open(os.path.join(out_dir, "DATA_CAPABILITY.json"), "w")
    try:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    md = render_plan_md(plan, disk)
    for path in (
        os.path.join(ROOT, "docs", "research_engine", "DATA_ACQUISITION_PLAN.md"),
        os.path.join(out_dir, "DATA_ACQUISITION_PLAN.md"),
    ):
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        fh = open(path, "w")
        try:
            fh.write(md)
            if not md.endswith("\n"):
                fh.write("\n")
        finally:
            fh.close()
    print("DATA_CAPABILITY", plan.get("status"), "disk=%s probe=%s" % (len(disk), probe.get("status")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
