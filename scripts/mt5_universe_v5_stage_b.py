#!/usr/bin/env python3
"""Stage B: deep history only for interesting unique underlyings. Resume-safe."""
from __future__ import print_function

import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from research_engine.local_fs import force_project_temp

force_project_temp(ROOT)

from data_layer.config import load_data_sources
from data_layer.readonly_mt5 import import_readonly_mt5, initialize_readonly
from research_engine.io_util import dump_json
from research_engine.mt5_history.probe import probe_from_pos
from research_engine.mt5_universe.qualify import coverage
from research_protocol.bars import load_json

OUT = os.path.join(ROOT, "data", "market", "research_engine", "mt5_universe")
CKPT = os.path.join(OUT, "STAGE_B_CHECKPOINT.json")
STEPS = (2000, 10000, 20000, 50000, 80000)
DEEP = ("H1", "H4", "M15", "W1")


def disk_free_gb(letter):
    return float(shutil.disk_usage("%s:\\" % letter).free) / (1024.0 * 1024.0 * 1024.0)


def assert_disk():
    c_gb = disk_free_gb("C")
    d_gb = disk_free_gb("D")
    if c_gb < 20.0:
        raise RuntimeError("C_FREE_BELOW_20GB:%.2f" % c_gb)
    return c_gb, d_gb


def probe_tf(mt5, symbol, timeframe, steps):
    row = probe_from_pos(mt5, symbol, timeframe, 250000, sleep_s=0.02, steps=steps)
    if row is None:
        return {"status": "NOT_AVAILABLE", "timeframe": timeframe}
    years = float(row.get("calendar_span") or 0)
    if row.get("status") == "OK":
        row["coverage"] = coverage(timeframe, years)
    else:
        row["coverage"] = "NOT_AVAILABLE"
    return row


def main():
    c_gb, d_gb = assert_disk()
    print("STAGE_B_DISK", "C", round(c_gb, 2), "D", round(d_gb, 2), flush=True)
    cand = load_json(os.path.join(OUT, "STAGE_B_CANDIDATES.json"))
    wanted = list(cand.get("symbols") or [])
    done = {}
    if os.path.isfile(CKPT):
        done = dict((r["symbol"], r) for r in (load_json(CKPT).get("rows") or []))
        print("STAGE_B_RESUME", len(done), flush=True)
    cfg = load_data_sources()
    mt5, ver = import_readonly_mt5()
    path = cfg.get("terminal_path") or r"C:\Program Files\Ava Trade MT5 Terminal"
    try:
        initialize_readonly(mt5, cfg.get("terminal_path"))
    except Exception:
        initialize_readonly(mt5, path)
    rows = list(done.values())
    try:
        for name in wanted:
            if name in done:
                continue
            print("STAGE_B", name, flush=True)
            mt5.symbol_select(name, True)
            history = {}
            history["D1"] = probe_tf(mt5, name, "D1", STEPS)
            years = float((history["D1"] or {}).get("calendar_span") or 0)
            if years >= 5.0:
                for tf in DEEP:
                    history[tf] = probe_tf(mt5, name, tf, (2000, 10000, 50000, 80000))
            row = {
                "symbol": name,
                "probe_stage": "B",
                "d1_years": years,
                "timeframes": history,
            }
            rows.append(row)
            done[name] = row
            dump_json(CKPT, {"n": len(done), "rows": list(done.values())})
            print("STAGE_B_OK", name, "D1", years, flush=True)
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
    dump_json(
        os.path.join(OUT, "STAGE_B_HISTORY.json"),
        {"n": len(rows), "package": ver, "rows": rows},
    )
    print("STAGE_B_DONE", len(rows), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
