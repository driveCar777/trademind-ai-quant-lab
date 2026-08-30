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


def pull_one(session, eq):
    symbol = eq["symbol"]
    start, end = window_for(eq)
    raw = session.query_kline(symbol, start, end, "3")
    qfq = session.query_kline(symbol, start, end, "2")
    try:
        adj = session.query_adjust_factor(symbol, start, end)
    except Exception as exc:
        adj = []
        adj_err = str(exc)
    else:
        adj_err = None
    dest = _symbol_dir(symbol)
    if not os.path.isdir(dest):
        os.makedirs(dest)
    raw_path = os.path.join(dest, "raw.csv")
    qfq_path = os.path.join(dest, "qfq.csv")
    sha_raw = _write_vendor_csv(raw_path, raw)
    sha_qfq = _write_vendor_csv(qfq_path, qfq)
    dump_json(
        os.path.join(dest, "meta.json"),
        {
            "symbol": symbol,
            "start": start,
            "end": end,
            "n_raw": len(raw),
            "n_qfq": len(qfq),
            "n_adjust_factor": len(adj),
            "adjust_factor_error": adj_err,
            "sha256_raw": sha_raw,
            "sha256_qfq": sha_qfq,
            "empty": len(raw) == 0,
            "source": "BAOSTOCK",
            "adjust_convention": {"3": "RAW_UNADJUSTED", "2": "FORWARD_QFQ"},
        },
    )
    if adj:
        dump_json(os.path.join(dest, "adjust_factor.json"), adj)
    return {
        "symbol": symbol,
        "n_raw": len(raw),
        "n_qfq": len(qfq),
        "n_adjust_factor": len(adj),
        "sha256_raw": sha_raw,
        "sha256_qfq": sha_qfq,
        "empty": len(raw) == 0,
    }


def already_done(state, symbol):
    rec = (state.get("done") or {}).get(symbol)
    if not rec:
        return False
    raw_path = os.path.join(_symbol_dir(symbol), "raw.csv")
    return os.path.isfile(raw_path)


def acquire(limit=None, reset_every=200, only_failed=False, sleep_s=0.05):
    ensure_tree()
    if not os.path.isdir(PANEL_RAW):
        os.makedirs(PANEL_RAW)
    basic = os.path.join(REFERENCE, "tm-cn-a-BASIC-20260830-000001.csv")
    equities = load_equities(basic)
    state = load_checkpoint()
    if not state.get("started_at"):
        state["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
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
                rec = pull_one(session, eq)
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
            if (i + 1) % 20 == 0:
                save_checkpoint(state)
                print("CHECKPOINT", state["n_done"] if False else len(state.get("done") or {}), "/", len(equities), "failed", len(state.get("failed") or {}), flush=True)
            if reset_every and (i + 1) % int(reset_every) == 0:
                session.reset()
                print("SESSION_RESET", i + 1, flush=True)
    finally:
        session.logout()
        save_checkpoint(state)
    return state
