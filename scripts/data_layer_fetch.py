"""Read-only MT5 dataset fetch. Does not start backtests or send orders."""

from __future__ import print_function

import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from data_layer.config import load_data_sources
from data_layer.fetch import fetch_and_freeze, fetch_matrix
from data_layer.logging_util import DataLayerLogger
from data_layer.storage import ensure_layout


def main(argv=None):
    parser = argparse.ArgumentParser(description="TradeMind Data Layer V0.1 read-only fetch")
    parser.add_argument("--logical", help="GOLD / EURUSD / USDJPY / OIL")
    parser.add_argument("--timeframe", help="M15 / H1 / H4 / D1")
    parser.add_argument("--matrix", action="store_true", help="4 symbols x 4 timeframes")
    args = parser.parse_args(argv)

    cfg = load_data_sources()
    ensure_layout(cfg["storage_root"])
    logger = DataLayerLogger(os.path.join(cfg["storage_root"], "logs", "data_layer.log"))

    if args.matrix:
        results = fetch_matrix(cfg, logger)
        print(json.dumps(_summarize(results), ensure_ascii=True, indent=2))
        return 0 if all(item.get("ok") for item in results) else 1

    if not args.logical or not args.timeframe:
        parser.error("use --matrix or both --logical and --timeframe")

    result = fetch_and_freeze(args.logical, args.timeframe, cfg, logger)
    print(json.dumps({"ok": True, "dataset_id": result["dataset_id"], "quality": result["quality"]}, indent=2))
    return 0


def _summarize(results):
    rows = []
    for item in results:
        if item.get("ok"):
            result = item["result"]
            manifest = result["manifest"]
            rows.append(
                {
                    "ok": True,
                    "dataset_id": manifest["dataset_id"],
                    "logical_symbol": manifest["logical_symbol"],
                    "mt5_symbol": manifest["mt5_symbol"],
                    "timeframe": manifest["timeframe"],
                    "row_count": manifest["row_count"],
                    "validation_status": manifest["validation_status"],
                    "history_shortfall": manifest.get("history_shortfall"),
                }
            )
        else:
            rows.append(item)
    return {"count": len(rows), "datasets": rows}


if __name__ == "__main__":
    sys.exit(main())
