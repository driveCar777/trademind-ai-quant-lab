"""Pack frozen raw CSVs to D: npy. Never call BaoStock."""
from __future__ import print_function

import csv
import json
import os

import numpy as np

from research_engine.cn_a_share.calendar import load_calendar
from research_engine.cn_a_share.paths import PANEL_RAW, REFERENCE
from research_engine.cn_a_share.universe import listed_on
from research_engine.cn_a_share.universe_daily import load_equities
from research_engine.cn_a_share_alpha import DATASET_HASH, DATASET_ID
from research_engine.cn_a_share_alpha.paths import CACHE, ensure_alpha_tree
from research_protocol.hashing import canonical_hash


META_NAME = "meta.json"


def _cal_days():
    path = os.path.join(REFERENCE, "tm-cn-a-CALENDAR-20260830-000001.csv")
    rows = load_calendar(path)
    return [r["calendar_date"] for r in rows if str(r.get("is_trading_day")) in ("1", "1.0")]


def limit_pct_for(symbol, is_st, day):
    if is_st:
        return 0.05
    if symbol.startswith("bj."):
        return 0.30
    if symbol.startswith("sh.688"):
        return 0.20
    if symbol.startswith("sz.30"):
        return 0.20 if day >= "2020-08-24" else 0.10
    return 0.10


def pack_exists():
    return os.path.isfile(os.path.join(CACHE, "close.npy")) and os.path.isfile(os.path.join(CACHE, META_NAME))


def load_pack():
    meta = json.load(open(os.path.join(CACHE, META_NAME), "r", encoding="utf-8"))
    if meta.get("dataset_id") != DATASET_ID or meta.get("dataset_hash") != DATASET_HASH:
        raise RuntimeError("PACK_DATASET_MISMATCH")
    arrays = {}
    for key in ("open", "high", "low", "close", "preclose", "volume", "amount", "turn"):
        arrays[key] = np.load(os.path.join(CACHE, key + ".npy"), mmap_mode="r")
    for key in ("tradestatus", "isST", "listed"):
        arrays[key] = np.load(os.path.join(CACHE, key + ".npy"), mmap_mode="r")
    arrays["dates"] = [str(x) for x in np.load(os.path.join(CACHE, "dates.npy"), allow_pickle=True)]
    arrays["symbols"] = [str(x) for x in np.load(os.path.join(CACHE, "symbols.npy"), allow_pickle=True)]
    arrays["meta"] = meta
    return arrays


def pack_panel():
    ensure_alpha_tree()
    if pack_exists():
        print("PACK_EXISTS", CACHE, flush=True)
        return load_pack()
    dates = _cal_days()
    date_ix = dict((d, i) for i, d in enumerate(dates))
    basic = os.path.join(REFERENCE, "tm-cn-a-BASIC-20260830-000001.csv")
    equities = load_equities(basic)
    symbols = [e["symbol"] for e in equities]
    n_t = len(dates)
    n_n = len(symbols)
    print("PACK_ALLOC", n_t, n_n, flush=True)
    nan = np.float32(np.nan)
    store = {}
    for key in ("open", "high", "low", "close", "preclose", "volume", "amount", "turn"):
        store[key] = np.full((n_t, n_n), nan, dtype=np.float32)
    tradestatus = np.full((n_t, n_n), np.int8(-1))
    is_st = np.zeros((n_t, n_n), dtype=np.int8)
    listed = np.zeros((n_t, n_n), dtype=np.int8)
    eq_map = dict((e["symbol"], e) for e in equities)
    for j, e in enumerate(equities):
        for i, d in enumerate(dates):
            if listed_on(e, d):
                listed[i, j] = 1
    root = os.path.join(PANEL_RAW, "symbols")
    for j, symbol in enumerate(symbols):
        path = os.path.join(root, symbol, "raw.csv")
        if not os.path.isfile(path):
            continue
        handle = open(path, "r", encoding="utf-8")
        try:
            reader = csv.DictReader(handle)
            for row in reader:
                d = row.get("date")
                i = date_ix.get(d)
                if i is None:
                    continue
                def f(name):
                    v = row.get(name)
                    if v is None or v == "":
                        return nan
                    try:
                        return np.float32(v)
                    except ValueError:
                        return nan
                store["open"][i, j] = f("open")
                store["high"][i, j] = f("high")
                store["low"][i, j] = f("low")
                store["close"][i, j] = f("close")
                store["preclose"][i, j] = f("preclose")
                store["volume"][i, j] = f("volume")
                store["amount"][i, j] = f("amount")
                store["turn"][i, j] = f("turn")
                ts = row.get("tradestatus")
                tradestatus[i, j] = np.int8(int(float(ts))) if ts not in (None, "") else np.int8(-1)
                st = row.get("isST")
                is_st[i, j] = np.int8(1 if str(st) in ("1", "1.0") else 0)
        finally:
            handle.close()
        if (j + 1) % 200 == 0:
            print("PACK_SYM", j + 1, "/", n_n, flush=True)
    for key, arr in store.items():
        np.save(os.path.join(CACHE, key + ".npy"), arr)
    np.save(os.path.join(CACHE, "tradestatus.npy"), tradestatus)
    np.save(os.path.join(CACHE, "isST.npy"), is_st)
    np.save(os.path.join(CACHE, "listed.npy"), listed)
    np.save(os.path.join(CACHE, "dates.npy"), np.array(dates, dtype=object))
    np.save(os.path.join(CACHE, "symbols.npy"), np.array(symbols, dtype=object))
    meta = {
        "dataset_id": DATASET_ID,
        "dataset_hash": DATASET_HASH,
        "n_dates": n_t,
        "n_symbols": n_n,
        "source": "FROZEN_RAW_ONLY",
        "live_api": False,
    }
    meta["pack_hash"] = canonical_hash({"dataset_id": DATASET_ID, "n": n_n, "t": n_t})
    handle = open(os.path.join(CACHE, META_NAME), "w", encoding="utf-8")
    try:
        json.dump(meta, handle, indent=2, sort_keys=True)
        handle.write("\n")
    finally:
        handle.close()
    print("PACK_DONE", n_t, n_n, flush=True)
    return load_pack()
