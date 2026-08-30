"""Checkpointed equity daily pull. One session. Raw is never overwritten in place."""
from __future__ import print_function

import csv
import os
import time

from research_engine.cn_a_share.io_util import dump_json, load_json
from research_engine.cn_a_share.paths import PANEL_RAW, REFERENCE, TMP, ensure_tree
from research_engine.cn_a_share.session import BaoSession, classify_error
from research_engine.cn_a_share.universe_daily import load_equities
from research_protocol.hashing import file_sha256


CHECKPOINT = os.path.join(PANEL_RAW, "CHECKPOINT.json")
FAILED = os.path.join(PANEL_RAW, "FAILED_SYMBOLS.json")
FAILED_QUEUE = os.path.join(PANEL_RAW, "FAILED_QUEUE.json")
KNOWN_DATA_GAP = ("sz.000033", "sz.000038")
CHECKPOINT_MARKS = (10, 25, 50, 100)
K_FIELDS = (
    "date",
    "code",
    "open",
    "high",
    "low",
    "close",
    "preclose",
    "volume",
    "amount",
    "adjustflag",
    "turn",
    "tradestatus",
    "pctChg",
    "isST",
)


def _symbol_dir(symbol):
    return os.path.join(PANEL_RAW, "symbols", symbol)


def _write_vendor_csv(path, rows):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    tmp = path + ".part"
    handle = open(tmp, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(handle, fieldnames=list(K_FIELDS), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    finally:
        handle.close()
    if os.path.isfile(path):
        os.remove(path)
    os.rename(tmp, path)
    return file_sha256(path)


def load_checkpoint():
    if os.path.isfile(CHECKPOINT):
        return load_json(CHECKPOINT)
    return {"done": {}, "empty": [], "failed": {}, "n_done": 0, "started_at": None}


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _queue_from_state(state):
    queue = {
        "TRANSIENT": {},
        "PERMANENT": {},
        "SOURCE_ERROR": {},
        "EMPTY_HISTORY": [],
        "DATA_GAP": [],
    }
    for symbol, rec in (state.get("failed") or {}).items():
        kind = rec.get("kind") or "TRANSIENT"
        if kind not in queue:
            kind = "TRANSIENT"
        if kind in ("EMPTY_HISTORY", "DATA_GAP"):
            queue[kind].append(symbol)
        else:
            queue[kind][symbol] = rec
    for symbol in state.get("empty") or []:
        bucket = "DATA_GAP" if symbol in KNOWN_DATA_GAP else "EMPTY_HISTORY"
        if symbol not in queue[bucket]:
            queue[bucket].append(symbol)
    return queue


def save_checkpoint(state):
    state["n_done"] = len(state.get("done") or {})
    state["timestamp"] = _now()
    dump_json(CHECKPOINT, state)
    dump_json(
        os.path.join(TMP, "v12_1_checkpoint.json"),
        {"n_done": state["n_done"], "n_failed": len(state.get("failed") or {})},
    )
    queue = _queue_from_state(state)
    dump_json(FAILED_QUEUE, queue)
    if state.get("failed"):
        dump_json(FAILED, state["failed"])
    from research_engine.cn_a_share.paths import QUALITY

    dump_json(
        os.path.join(QUALITY, "PANEL_PROGRESS_V12_2.json"),
        {
            "n_done": state["n_done"],
            "n_failed": len(state.get("failed") or {}),
            "n_empty": len(state.get("empty") or []),
            "last_success": state.get("last_success"),
            "timestamp": state.get("timestamp"),
        },
    )


def window_for(eq):
    start = eq.get("listing_date") or "1990-12-19"
    end = eq.get("delisting_date") or "2026-08-28"
    if eq.get("delisting_date"):
        end = eq["delisting_date"]
    return start, end


def pull_one(session, eq, with_qfq=False, with_adj=False):
    symbol = eq["symbol"]
    start, end = window_for(eq)
    raw = session.query_kline(symbol, start, end, "3")
    dest = _symbol_dir(symbol)
    if not os.path.isdir(dest):
        os.makedirs(dest)
    raw_path = os.path.join(dest, "raw.csv")
    sha_raw = _write_vendor_csv(raw_path, raw)
    n_qfq = 0
    sha_qfq = None
    n_adj = 0
    if with_qfq:
        qfq = session.query_kline(symbol, start, end, "2")
        sha_qfq = _write_vendor_csv(os.path.join(dest, "qfq.csv"), qfq)
        n_qfq = len(qfq)
    if with_adj:
        try:
            adj = session.query_adjust_factor(symbol, start, end)
        except Exception:
            adj = []
        n_adj = len(adj)
        if adj:
            dump_json(os.path.join(dest, "adjust_factor.json"), adj)
    dump_json(
        os.path.join(dest, "meta.json"),
        {
            "symbol": symbol,
            "start": start,
            "end": end,
            "n_raw": len(raw),
            "n_qfq": n_qfq,
            "n_adjust_factor": n_adj,
            "sha256_raw": sha_raw,
            "sha256_qfq": sha_qfq,
            "empty": len(raw) == 0,
            "source": "BAOSTOCK",
            "adjust_convention": {"3": "RAW_UNADJUSTED", "2": "FORWARD_QFQ"},
            "phase": "RAW" if not with_qfq else "RAW_QFQ",
        },
    )
    return {
        "symbol": symbol,
        "n_raw": len(raw),
        "n_qfq": n_qfq,
        "n_adjust_factor": n_adj,
        "sha256_raw": sha_raw,
        "sha256_qfq": sha_qfq,
        "empty": len(raw) == 0,
    }


def already_done(state, symbol):
    raw_path = os.path.join(_symbol_dir(symbol), "raw.csv")
    if os.path.isfile(raw_path):
        return True
    rec = (state.get("done") or {}).get(symbol)
    return bool(rec and os.path.isfile(raw_path))


def verify_existing(symbol):
    """If raw.csv exists, never re-request. SKIP when hash matches meta."""
    raw_path = os.path.join(_symbol_dir(symbol), "raw.csv")
    if not os.path.isfile(raw_path):
        return None
    sha = file_sha256(raw_path)
    meta_path = os.path.join(_symbol_dir(symbol), "meta.json")
    meta = load_json(meta_path) if os.path.isfile(meta_path) else {}
    unchanged = bool(meta.get("sha256_raw") and meta.get("sha256_raw") == sha)
    n = 0
    handle = open(raw_path, "r", encoding="utf-8")
    try:
        n = max(0, sum(1 for _ in handle) - 1)
    finally:
        handle.close()
    return {
        "symbol": symbol,
        "status": "SKIP" if unchanged else "VERIFY_EXISTING",
        "rows": n,
        "sha256_raw": sha,
        "hash_unchanged": unchanged,
        "empty": n == 0,
        "n_raw": n,
    }


def recover_from_disk(state):
    root = os.path.join(PANEL_RAW, "symbols")
    if not os.path.isdir(root):
        return state
    for name in os.listdir(root):
        raw_path = os.path.join(root, name, "raw.csv")
        if not os.path.isfile(raw_path):
            continue
        if name in (state.get("done") or {}):
            continue
        n = 0
        handle = open(raw_path, "r", encoding="utf-8")
        try:
            n = max(0, sum(1 for _ in handle) - 1)
        finally:
            handle.close()
        state.setdefault("done", {})[name] = {"symbol": name, "n_raw": n, "empty": n == 0, "recovered": True}
        if n == 0 and name not in state.setdefault("empty", []):
            state["empty"].append(name)
    return state


def acquire(limit=None, reset_every=200, only_failed=False, sleep_s=0.02, with_qfq=False, with_adj=False):
    ensure_tree()
    if not os.path.isdir(PANEL_RAW):
        os.makedirs(PANEL_RAW)
    from research_engine.cn_a_share.guard import disk_ok_for_download

    ok, flag, d_free, _c = disk_ok_for_download()
    if not ok:
        raise RuntimeError("DISK_GUARD:%s D=%.1f" % (flag, d_free))
    basic = os.path.join(REFERENCE, "tm-cn-a-BASIC-20260830-000001.csv")
    equities = load_equities(basic)
    state = recover_from_disk(load_checkpoint())
    if not state.get("started_at"):
        state["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    save_checkpoint(state)
    if only_failed:
        wanted = [e for e in equities if e["symbol"] in (state.get("failed") or {})]
    else:
        wanted = [e for e in equities if not already_done(state, e["symbol"])]
    if limit:
        wanted = wanted[: int(limit)]
    session = BaoSession(sleep_s=sleep_s)
    session.login()
    try:
        for i, eq in enumerate(wanted):
            symbol = eq["symbol"]
            ok_disk, disk_flag, d_free, _c = disk_ok_for_download()
            if not ok_disk:
                print("DISK_GUARD", disk_flag, d_free, flush=True)
                break
            existing = verify_existing(symbol)
            if existing:
                print("SKIP", symbol, existing.get("rows"), existing.get("status"), flush=True)
                rec = dict(existing)
                rec["last_success"] = _now()
                rec["last_error"] = None
                rec["attempts"] = int(((state.get("done") or {}).get(symbol) or {}).get("attempts") or 1)
                rec["timestamp"] = _now()
                state.setdefault("done", {})[symbol] = rec
                if rec.get("empty") and symbol not in state.setdefault("empty", []):
                    state["empty"].append(symbol)
                state["last_success"] = symbol
                continue
            attempts = int(((state.get("failed") or {}).get(symbol) or {}).get("attempts") or 0)
            try:
                rec = pull_one(session, eq, with_qfq=with_qfq, with_adj=with_adj)
                status = "EMPTY_HISTORY" if rec.get("empty") else "OK"
                if rec.get("empty") and symbol in KNOWN_DATA_GAP:
                    status = "DATA_GAP"
                rec.update(
                    {
                        "status": status,
                        "rows": rec.get("n_raw"),
                        "last_success": _now(),
                        "last_error": None,
                        "attempts": attempts + 1,
                        "timestamp": _now(),
                    }
                )
                print("OK", symbol, rec.get("n_raw"), status, flush=True)
                state.setdefault("done", {})[symbol] = rec
                state["last_success"] = symbol
                if rec.get("empty"):
                    if symbol not in state.setdefault("empty", []):
                        state["empty"].append(symbol)
                state.get("failed", {}).pop(symbol, None)
            except Exception as exc:
                kind = classify_error(exc)
                fail = {
                    "symbol": symbol,
                    "status": "FAILED",
                    "rows": 0,
                    "last_success": ((state.get("done") or {}).get(symbol) or {}).get("last_success"),
                    "last_error": str(exc),
                    "attempts": attempts + 1,
                    "timestamp": _now(),
                    "error": str(exc),
                    "kind": kind,
                }
                state.setdefault("failed", {})[symbol] = fail
                print("FAIL", symbol, kind, exc, flush=True)
                if kind != "PERMANENT":
                    try:
                        session.reset()
                    except Exception:
                        pass
            n_done = len(state.get("done") or {})
            if n_done in CHECKPOINT_MARKS or n_done % 10 == 0 or n_done % 25 == 0 or n_done % 50 == 0 or n_done % 100 == 0:
                save_checkpoint(state)
                print(
                    "CHECKPOINT",
                    n_done,
                    "/",
                    len(equities),
                    "failed",
                    len(state.get("failed") or {}),
                    flush=True,
                )
            if reset_every and (i + 1) % int(reset_every) == 0:
                session.reset()
                print("SESSION_RESET", i + 1, flush=True)
    finally:
        session.logout()
        save_checkpoint(state)
    return state
