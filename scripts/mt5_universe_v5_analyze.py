#!/usr/bin/env python3
"""Build equivalence + taxonomy from V4 inventory (841 specs). No MT5 attach."""
from __future__ import print_function

import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.io_util import dump_json
from research_engine.local_fs import force_project_temp
from research_engine.mt5_universe.taxonomy import classify_row
from research_protocol.bars import load_json

force_project_temp(ROOT)

INV = os.path.join(ROOT, "data", "market", "research_engine", "mt5_history", "MT5_SYMBOL_INVENTORY_V1.json")
OUT = os.path.join(ROOT, "data", "market", "research_engine", "mt5_universe")


def main():
    payload = load_json(INV)
    symbols = list(payload.get("symbols") or [])
    rows = []
    groups = defaultdict(list)
    path_roots = Counter()
    asset_classes = Counter()
    instrument_types = Counter()
    listing_kinds = Counter()
    options = []
    futures = []
    disabled = []
    for spec in symbols:
        row = classify_row(spec)
        rows.append(row)
        groups[row["economic_underlying"]].append(row["symbol"])
        path_roots[row["path_root"]] += 1
        asset_classes[row["asset_class"]] += 1
        instrument_types[row["instrument_type"]] += 1
        listing_kinds[row["listing_kind"]] += 1
        if row["instrument_type"] == "OPTION":
            options.append(row["symbol"])
        if row["instrument_type"] == "FUTURE":
            futures.append(row["symbol"])
        if row.get("trade_mode") in (0, "0") or row.get("visible") is False:
            disabled.append(row["symbol"])

    clone_groups = {}
    unique = []
    clones = []
    for key, names in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(names) >= 2:
            clone_groups[key] = names
            clones.extend(names)
        else:
            unique.append(names[0])

    equivalence = {
        "map_id": "SYMBOL_EQUIVALENCE_MAP_V1",
        "source": "MT5_SYMBOL_INVENTORY_V1",
        "n_symbols": len(rows),
        "n_underlyings": len(groups),
        "n_clone_groups": len(clone_groups),
        "n_singleton_underlyings": len(unique),
        "note": "Same economic_underlying is not a new information set.",
        "groups": dict((k, v) for k, v in sorted(groups.items())),
        "clone_groups": clone_groups,
    }
    dump_json(os.path.join(OUT, "SYMBOL_EQUIVALENCE_MAP_V1.json"), equivalence)
    dump_json(
        os.path.join(OUT, "TAXONOMY_V5_DRAFT.json"),
        {
            "utc_source": "V4_INVENTORY",
            "n": len(rows),
            "path_roots": dict(path_roots),
            "asset_class_counts": dict(asset_classes),
            "instrument_type_counts": dict(instrument_types),
            "listing_kind_counts": dict(listing_kinds),
            "n_options": len(options),
            "n_futures": len(futures),
            "n_disabled_or_hidden": len(disabled),
            "options": options,
            "futures": futures,
            "rows": rows,
            "true_options": False,
            "true_futures": False,
            "information_note": "Ava listings are CFDs. option_mode=0 and expiration=0 on inventory.",
        },
    )
    print("ANALYZE_N", len(rows))
    print("UNDERLYINGS", len(groups), "CLONE_GROUPS", len(clone_groups), "SINGLETONS", len(unique))
    print("PATH_ROOTS", dict(path_roots))
    print("ASSET_CLASS", dict(asset_classes))
    print("INSTRUMENT", dict(instrument_types))
    print("LISTING", dict(listing_kinds))
    print("OPTIONS", len(options), "FUTURES", len(futures), "DISABLED", len(disabled))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
