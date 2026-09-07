"""Compile raw per-date margin JSON into (T x N) arrays aligned to the frozen pack. PIT lag applied here."""
from __future__ import print_function

import glob
import gzip
import hashlib
import json
import os

import numpy as np

from research_engine.cn_a_share_margin_v23 import NORM, RAW, PIT_LAG_SESSIONS, MARGIN_DATASET_ID, ensure_v23

FIELDS = ("RZYE", "RZJME", "SZ", "RZMRE", "RQYL")


def _sym(code, market):
    code = str(code).zfill(6)
    if code.startswith(("6", "9")):
        return "sh." + code
    if code.startswith(("0", "3", "2")):
        return "sz." + code
    if code.startswith(("4", "8")):
        return "bj." + code
    return None


def compile_arrays(pack):
    ensure_v23()
    dates = pack["dates"]
    symbols = pack["symbols"]
    dix = dict((d, i) for i, d in enumerate(dates))
    six = dict((s, j) for j, s in enumerate(symbols))
    T, N = len(dates), len(symbols)
    arr = dict((f, np.full((T, N), np.nan, dtype=np.float32)) for f in FIELDS)
    files = sorted(glob.glob(os.path.join(RAW, "*.json.gz")))
    n_rows = 0
    n_unmapped = 0
    h = hashlib.sha256()
    for f in files:
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            payload = json.load(fh)
        d = payload["date"]
        # PIT: row for session d becomes knowable at d+1 pre-open -> place at index(d) + lag
        i = dix.get(d)
        if i is None:
            continue
        i += PIT_LAG_SESSIONS
        if i >= T:
            continue
        h.update(d.encode())
        h.update(str(payload["n"]).encode())
        for r in payload["rows"]:
            sym = _sym(r.get("SCODE"), r.get("MARKET"))
            j = six.get(sym)
            if j is None:
                n_unmapped += 1
                continue
            n_rows += 1
            for fld in FIELDS:
                v = r.get(fld)
                if v is not None:
                    try:
                        arr[fld][i, j] = np.float32(v)
                    except (TypeError, ValueError):
                        pass
    for fld in FIELDS:
        np.save(os.path.join(NORM, fld + ".npy"), arr[fld])
    meta = {
        "margin_dataset_id": MARGIN_DATASET_ID,
        "n_files": len(files),
        "n_rows_mapped": n_rows,
        "n_rows_unmapped": n_unmapped,
        "pit_lag_sessions": PIT_LAG_SESSIONS,
        "first_file": os.path.basename(files[0]) if files else None,
        "last_file": os.path.basename(files[-1]) if files else None,
        "fields": list(FIELDS),
        "coverage_per_year": {},
        "raw_content_hash": h.hexdigest(),
    }
    cov = np.isfinite(arr["RZYE"]).sum(axis=1)
    for y in sorted(set(d[:4] for d in dates)):
        idx = [i for i, d in enumerate(dates) if d[:4] == y]
        meta["coverage_per_year"][y] = int(np.median(cov[idx])) if idx else 0
    with open(os.path.join(NORM, "META.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    print("V23_COMPILE", n_rows, "rows", n_unmapped, "unmapped", meta["coverage_per_year"], flush=True)
    return arr, meta


def load_arrays():
    return dict((f, np.load(os.path.join(NORM, f + ".npy"), mmap_mode="r")) for f in FIELDS)
