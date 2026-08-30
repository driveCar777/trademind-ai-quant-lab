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


def save_checkpoint(state):
    state["n_done"] = len(state.get("done") or {})
    dump_json(CHECKPOINT, state)
    dump_json(os.path.join(TMP, "v12_1_checkpoint.json"), {"n_done": state["n_done"], "n_failed": len(state.get("failed") or {})})
    if state.get("failed"):
        dump_json(FAILED, state["failed"])


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
            try:
                rec = pull_one(session, eq, with_qfq=with_qfq, with_adj=with_adj)
                print("OK", symbol, rec.get("n_raw"), flush=True)
                state.setdefault("done", {})[symbol] = rec
                if rec.get("empty"):
                    if symbol not in state.setdefault("empty", []):
                        state["empty"].append(symbol)
                state.get("failed", {}).pop(symbol, None)
            except Exception as exc:
                state.setdefault("failed", {})[symbol] = {
                    "error": str(exc),
                    "kind": classify_error(exc),
                }
                print("FAIL", symbol, exc, flush=True)
                try:
                    session.reset()
                except Exception:
                    pass
            if (i + 1) % 10 == 0:
                save_checkpoint(state)
                print("CHECKPOINT", state["n_done"] if False else len(state.get("done") or {}), "/", len(equities), "failed", len(state.get("failed") or {}), flush=True)
            if reset_every and (i + 1) % int(reset_every) == 0:
                session.reset()
                print("SESSION_RESET", i + 1, flush=True)
    finally:
        session.logout()
        save_checkpoint(state)
    return state
