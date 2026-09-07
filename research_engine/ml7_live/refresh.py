"""Incremental refresh of the four information layers into live/info_layers.

Seed: frozen raw files (immutable, one per year / report period) are hard-linked (or copied) into the live raw dir once.
Recent: files whose year / report period is still receiving filings are deleted and refetched when older than RECENT_REFETCH_DAYS.
Then each package's own resumable download.main() fills every missing file up to END_YEAR = asof year.
"""
from __future__ import print_function

import datetime
import glob
import os
import shutil
import time

from research_engine.ml7_live import FROZEN, RECENT_PERIOD_DAYS, RECENT_REFETCH_DAYS, paths

TAG = "ML7_REFRESH"


def _link_or_copy(src, dst):
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def seed(layer):
    p = paths(layer)["raw"]
    n = 0
    for f in sorted(glob.glob(os.path.join(FROZEN[layer], "*.json.gz"))):
        dst = os.path.join(p, os.path.basename(f))
        if not os.path.isfile(dst):
            _link_or_copy(f, dst)
            n += 1
    return n


def _period_of(name):
    """'CPD_2025-06-30.json.gz' -> '2025-06-30'; 'HOLDER_2026.json.gz' -> '2026-12-31'."""
    stem = name[:-len(".json.gz")]
    tail = stem.split("_")[-1]
    return tail if len(tail) == 10 else "%s-12-31" % tail


def expire_recent(layer, asof):
    """Delete live raw files that cover an open period and are older than RECENT_REFETCH_DAYS (they will be refetched)."""
    p = paths(layer)["raw"]
    asof_d = datetime.date.fromisoformat(asof)
    now = time.time()
    n = 0
    for f in glob.glob(os.path.join(p, "*.json.gz")):
        per = _period_of(os.path.basename(f))
        try:
            per_d = datetime.date.fromisoformat(per)
        except ValueError:
            continue
        open_period = (asof_d - per_d).days < RECENT_PERIOD_DAYS
        stale = (now - os.path.getmtime(f)) > RECENT_REFETCH_DAYS * 86400
        if open_period and stale:
            # never delete a frozen hard-link target: unlink only removes this directory entry
            os.remove(f)
            n += 1
    return n


def download(layer):
    if layer == "findeep":
        from research_engine.cn_a_share_findeep_v27 import download as dl
    elif layer == "preann":
        from research_engine.cn_a_share_preann_v38 import download as dl
    elif layer == "insider":
        from research_engine.cn_a_share_insider_v38 import download as dl
    else:
        from research_engine.cn_a_share_pledge_v38 import download as dl
    return dl.main()


def refresh_all(asof, layers=("findeep", "preann", "insider", "pledge")):
    out = {}
    for layer in layers:
        t0 = time.time()
        seeded = seed(layer)
        expired = expire_recent(layer, asof)
        try:
            fails = download(layer)
        except Exception as e:  # noqa
            fails = "error: " + str(e)[:150]
        out[layer] = {"seeded": seeded, "expired_refetched": expired, "download_fails": fails, "sec": round(time.time() - t0, 1)}
        print(TAG, layer, out[layer], flush=True)
    return out
