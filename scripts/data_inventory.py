"""Data Layer Audit V1. D1>10y / H1>5y / M15>2y. Read-only. Never overwrite."""
from __future__ import print_function

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.forensics.inventory import build_capability, inventory_disk, probe_mt5
from research_engine.forensics.reports import render_data_md


def main():
    disk = inventory_disk()
    probe = probe_mt5()
    cap = build_capability(disk, probe)
    out_dir = os.path.join(ROOT, "data", "market", "research_engine", "forensics")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    paths = (
        os.path.join(out_dir, "DATA_CAPABILITY_REAL.json"),
        os.path.join(ROOT, "docs", "research_engine", "DATA_CAPABILITY_REAL.json"),
    )
    for path in paths:
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        handle = open(path, "w")
        try:
            json.dump(cap, handle, indent=2, sort_keys=True)
            handle.write("\n")
        finally:
            handle.close()
    md = render_data_md(cap)
    md_path = os.path.join(ROOT, "docs", "research_engine", "DATA_CAPABILITY_REAL.md")
    handle = open(md_path, "w")
    try:
        handle.write(md)
        if not md.endswith("\n"):
            handle.write("\n")
    finally:
        handle.close()
    print(
        "DATA_CAPABILITY_REAL",
        cap.get("overall"),
        "disk=%s probe=%s"
        % (len(disk), (cap.get("probe") or {}).get("status")),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
