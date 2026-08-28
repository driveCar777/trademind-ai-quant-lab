"""10-hour IS-only mine. Hits four Xavier :8002. Does not change Master/Worker."""
from __future__ import print_function

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "master", "api"))
os.environ["TRADEMIND_MT5_SEND"] = "0"

from app.service.mt5_service import fetch_history
from app.service.walkforward_service import (
    COMMISSION_BPS,
    IS_RATIO,
    MIN_BARS,
    SLIPPAGE_BPS,
    judge,
    score_is,
)

HOSTS = (
    "192.168.1.200",
    "192.168.1.201",
    "192.168.1.202",
    "192.168.1.203",
)
PORTS = (8002, 8003, 8004, 8005)
NODES = tuple("http://%s:%s" % (host, port) for host in HOSTS for port in PORTS)
SYMBOLS = ("XAUUSD", "EURUSD", "USDJPY", "CRUDE")
TIMEFRAMES = ("M15", "H1", "H4", "D1")
WIN_LENS = (600, 1000, 1400, 2000)
WIN_STEP = 100
DIR = os.path.join(ROOT, "data", "mine", "longrun")
HEARTBEAT = os.path.join(DIR, "heartbeat.json")
ROWS = os.path.join(DIR, "rows.jsonl")
BOARD = os.path.join(ROOT, "data", "mine", "BOARD.md")
PID_FILE = os.path.join(DIR, "miner.pid")
STOP_FILE = os.path.join(DIR, "STOP")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def candidates():
    rows = []
    for period in (5, 6, 7, 8, 9, 10, 12, 13, 14, 16, 18, 21, 24, 28, 32, 42):
        for osold in (15, 18, 20, 22, 25, 28, 30, 32, 35, 40):
            for obuy in (60, 65, 68, 70, 72, 75, 78, 80, 85):
                if osold >= obuy:
                    continue
                rows.append({
                    "id": "rsi-%s-%s-%s" % (period, osold, obuy),
                    "strategy": "RSI",
                    "params": {"period": period, "oversold": osold, "overbought": obuy},
                })
    for fast in (5, 8, 10, 12, 15, 18, 20, 24):
        for slow in (30, 35, 40, 45, 50, 60, 70, 80, 100):
            if fast >= slow:
                continue
            rows.append({
                "id": "sma-%s-%s" % (fast, slow),
                "strategy": "SMA_CROSS",
                "params": {"fast": fast, "slow": slow},
            })
    for period in (8, 10, 12, 15, 18, 20, 25, 30):
        for num_std in (1.2, 1.5, 1.8, 2.0, 2.2, 2.5, 3.0):
            rows.append({
                "id": "boll-%s-%s" % (period, str(num_std).replace(".", "p")),
                "strategy": "BOLLINGER",
                "params": {"period": period, "num_std": num_std},
            })
    for short in (6, 8, 12, 16):
        for long_p in (18, 21, 26, 32):
            if short >= long_p:
                continue
            for signal in (5, 7, 9, 12):
                rows.append({
                    "id": "macd-%s-%s-%s" % (short, long_p, signal),
                    "strategy": "EMA_MACD",
                    "params": {"short": short, "long": long_p, "signal": signal},
                })
    for entry in (10, 15, 20, 25, 30):
        for exit_p in (5, 8, 10, 12, 15):
            for atr in (7, 10, 14):
                rows.append({
                    "id": "turtle-%s-%s-%s" % (entry, exit_p, atr),
                    "strategy": "TURTLE",
                    "params": {"entry_period": entry, "exit_period": exit_p, "atr_period": atr},
                })
    for size in (1.0, 1.5, 2.0, 2.5, 3.0):
        for levels in (3, 5, 7):
            rows.append({
                "id": "grid-%s-%s" % (str(size).replace(".", "p"), levels),
                "strategy": "GRID",
                "params": {"grid_size_pct": size, "grid_levels": levels},
            })
    for ratio in (1.0, 1.2, 1.5):
        rows.append({
            "id": "vwap-%s" % str(ratio).replace(".", "p"),
            "strategy": "VWAP",
            "params": {"volume_confirm_ratio": ratio},
        })
    rows.append({"id": "regime", "strategy": "REGIME_SWITCH", "params": {}})
    return rows


def windows_of(n):
    out = []
    for length in WIN_LENS:
        if length < MIN_BARS or length > n:
            continue
        start = 0
        while start + length <= n:
            out.append((start, length))
            start += WIN_STEP
    if n >= MIN_BARS and (0, n) not in out:
        out.append((0, n))
    return out


def live_nodes():
    ok = []
    for base in NODES:
        try:
            resp = requests.get(base + "/version", timeout=4)
            body = resp.json() if resp.status_code == 200 else {}
            if resp.status_code == 200 and str(body.get("version") or "") >= "2.1.4":
                ok.append(base)
        except requests.RequestException:
            continue
    return ok


class Miner(object):
    def __init__(self, hours, per_node):
        self.deadline = time.time() + hours * 3600.0
        self.per_node = max(1, per_node)
        self.lock = threading.Lock()
        self.done = 0
        self.ok = 0
        self.err = 0
        self.survived = 0
        self.started = time.time()
        self.cycle = 0
        self.last_job = ""
        self.node_ok = 0
        self.node_hits = {base: 0 for base in NODES}
        self.node_err = {base: 0 for base in NODES}
        self.shortlist = {}
        self.seen = set()
        self._load_seen()

    def _load_seen(self):
        if not os.path.isfile(ROWS):
            return
        with open(ROWS, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                key = row.get("key")
                if key:
                    self.seen.add(key)
                    self._note_short(row)

    def remaining(self):
        return max(0.0, self.deadline - time.time())

    def stopped(self):
        return os.path.isfile(STOP_FILE) or time.time() >= self.deadline

    def _note_short(self, row):
        if (row.get("is_profit") or -999) <= 0 or row.get("verdict") != "survived":
            return
        key = "%s %s" % (row.get("symbol"), row.get("timeframe"))
        cur = self.shortlist.get(key) or []
        cur.append(row)
        cur.sort(key=lambda item: item.get("is_score") or -999, reverse=True)
        uniq = []
        seen_id = set()
        for item in cur:
            cid = item.get("id")
            if cid in seen_id:
                continue
            seen_id.add(cid)
            uniq.append(item)
            if len(uniq) >= 5:
                break
        self.shortlist[key] = uniq

    def record(self, row, error=False):
        with self.lock:
            self.done += 1
            if error:
                self.err += 1
            else:
                self.ok += 1
                if row.get("verdict") == "survived":
                    self.survived += 1
                self._note_short(row)
                self.seen.add(row.get("key"))
            self.last_job = row.get("key") or self.last_job
            node = row.get("node")
            if node:
                self.node_hits[node] = self.node_hits.get(node, 0) + 1
                if error:
                    self.node_err[node] = self.node_err.get(node, 0) + 1
            if not error:
                with open(ROWS, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            if self.done % 40 == 0 or error:
                self.write_heartbeat()
            if self.done % 400 == 0:
                self.write_board()

    def write_heartbeat(self):
        elapsed = max(1.0, time.time() - self.started)
        payload = {
            "updated_at": utc_now(),
            "pid": os.getpid(),
            "hours_left": round(self.remaining() / 3600.0, 3),
            "elapsed_min": round(elapsed / 60.0, 2),
            "cycle": self.cycle,
            "jobs_done": self.done,
            "jobs_ok": self.ok,
            "jobs_err": self.err,
            "survived": self.survived,
            "jobs_per_min": round(self.done * 60.0 / elapsed, 1),
            "nodes_live": self.node_ok,
            "node_hits": self.node_hits,
            "node_err": self.node_err,
            "last_job": self.last_job,
            "shortlist_windows": sorted(self.shortlist.keys()),
            "stop_file": os.path.isfile(STOP_FILE),
            "note": "IS-only pick. OOS published, not used to choose. Engine frozen V11.7.",
        }
        tmp = HEARTBEAT + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
            os.replace(tmp, HEARTBEAT)
        except OSError:
            pass

    def write_board(self):
        lines = [
            "# 证伪实验室挖掘板",
            "",
            "长任务心跳：`data/mine/longrun/heartbeat.json`。停：放空文件 `data/mine/longrun/STOP`。",
            "引擎冻在 V11.7。只按样本内打分。survived 不是下单。",
            "",
            "已完成 %s 笔，样本外 survived %s，错误 %s。" % (self.ok, self.survived, self.err),
            "",
        ]
        if not self.shortlist:
            lines.append("短名单还在积累。")
        for key in sorted(self.shortlist.keys()):
            lines.append("### %s" % key)
            for row in self.shortlist[key][:3]:
                lines.append(
                    "- %s  IS %+s  DD %s  OOS %+s  OOS_DD %s  成交 %s/%s"
                    % (
                        row.get("id"),
                        row.get("is_profit"),
                        row.get("is_drawdown"),
                        row.get("oos_profit"),
                        row.get("oos_drawdown"),
                        row.get("is_trades"),
                        row.get("oos_trades"),
                    )
                )
            lines.append("")
        with open(BOARD, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")


def pull_book():
    book = []
    for logical in SYMBOLS:
        for tf in TIMEFRAMES:
            try:
                pulled = fetch_history(logical, bars=2000, timeframe=tf)
            except Exception as exc:
                print("PULL_FAIL", logical, tf, exc, flush=True)
                continue
            closes = pulled.get("close") or []
            if len(closes) < MIN_BARS:
                print("PULL_SHORT", logical, tf, len(closes), flush=True)
                continue
            book.append({
                "logical": logical,
                "symbol": pulled.get("symbol") or logical,
                "timeframe": pulled.get("timeframe") or tf,
                "closes": [float(x) for x in closes],
            })
            print("PULLED", logical, pulled.get("symbol"), pulled.get("timeframe"), len(closes), flush=True)
    return book


def run_one(session, base, series, start, length, cand):
    window = series["closes"][start:start + length]
    cut = int(len(window) * IS_RATIO)
    payload = {
        "strategy": cand["strategy"],
        "symbol": series["symbol"],
        "start": "mine-%s" % cand["id"],
        "close": window,
        "cut": cut,
        "slippage_bps": SLIPPAGE_BPS,
        "commission_bps": COMMISSION_BPS,
        "params": cand.get("params") or {},
    }
    resp = session.post(base + "/backtest", json=payload, timeout=90)
    body = resp.json()
    if resp.status_code != 200 or body.get("error"):
        raise RuntimeError(body.get("error") or ("http-%s" % resp.status_code))
    is_row = body.get("is") or {}
    oos_row = body.get("oos") or {}
    key = "%s|%s|%s|%s|%s" % (series["symbol"], series["timeframe"], start, length, cand["id"])
    return {
        "key": key,
        "id": cand["id"],
        "strategy": cand["strategy"],
        "params": cand.get("params") or {},
        "symbol": series["symbol"],
        "timeframe": series["timeframe"],
        "win_start": start,
        "win_len": length,
        "cut": cut,
        "bars": len(window),
        "node": base,
        "verdict": judge(is_row, oos_row),
        "is_profit": is_row.get("profit"),
        "oos_profit": oos_row.get("profit"),
        "is_drawdown": is_row.get("max_drawdown"),
        "oos_drawdown": oos_row.get("max_drawdown"),
        "is_trades": is_row.get("total_trades"),
        "oos_trades": oos_row.get("total_trades"),
        "is_score": score_is(is_row),
        "at": utc_now(),
    }


def job_iter(book, cands, cycle, seen):
    offset = (cycle * 37) % WIN_STEP
    for series in book:
        wins = windows_of(len(series["closes"]))
        if offset:
            shifted = []
            n = len(series["closes"])
            for length in WIN_LENS:
                if length < MIN_BARS or length > n:
                    continue
                start = offset
                while start + length <= n:
                    shifted.append((start, length))
                    start += WIN_STEP
            if shifted:
                wins = shifted
        for start, length in wins:
            for cand in cands:
                key = "%s|%s|%s|%s|%s" % (series["symbol"], series["timeframe"], start, length, cand["id"])
                if cycle == 0 and key in seen:
                    continue
                if cycle > 0:
                    key = "%s|c%s" % (key, cycle)
                yield series, start, length, cand, key


def print_status():
    if not os.path.isfile(HEARTBEAT):
        print("NO_HEARTBEAT")
        return 1
    with open(HEARTBEAT, "r", encoding="utf-8") as fh:
        print(fh.read())
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=float, default=10)
    parser.add_argument("--per-node", type=int, default=4)
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.status:
        return print_status()

    os.makedirs(DIR, exist_ok=True)
    if os.path.isfile(STOP_FILE):
        os.remove(STOP_FILE)
    with open(PID_FILE, "w", encoding="utf-8") as fh:
        fh.write(str(os.getpid()))

    cands = candidates()
    miner = Miner(args.hours, args.per_node)
    print(
        "START hours=%s per_node=%s candidates=%s pid=%s"
        % (args.hours, args.per_node, len(cands), os.getpid()),
        flush=True,
    )
    miner.write_heartbeat()

    tls = threading.local()

    def session():
        sess = getattr(tls, "session", None)
        if sess is None:
            sess = requests.Session()
            tls.session = sess
        return sess

    def work(item):
        series, start, length, cand, key = item
        nodes = live
        if not nodes:
            raise RuntimeError("no_nodes")
        base = nodes[hash(key) % len(nodes)]
        try:
            row = run_one(session(), base, series, start, length, cand)
            row["key"] = key
            miner.record(row)
        except Exception as exc:
            alt = [n for n in nodes if n != base] or nodes
            try:
                row = run_one(session(), alt[0], series, start, length, cand)
                row["key"] = key
                miner.record(row)
            except Exception as exc2:
                miner.record({
                    "key": key,
                    "id": cand["id"],
                    "symbol": series.get("symbol"),
                    "timeframe": series.get("timeframe"),
                    "node": base,
                    "error": str(exc2) or str(exc),
                    "at": utc_now(),
                }, error=True)

    while not miner.stopped():
        live = live_nodes()
        miner.node_ok = len(live)
        miner.write_heartbeat()
        if not live:
            print("WAIT_NODES", flush=True)
            time.sleep(15)
            continue
        book = pull_book()
        if not book:
            print("WAIT_MT5", flush=True)
            time.sleep(20)
            continue
        workers = min(len(live) * miner.per_node, 16)
        print(
            "CYCLE %s nodes=%s series=%s workers=%s left_h=%.2f"
            % (miner.cycle, len(live), len(book), workers, miner.remaining() / 3600.0),
            flush=True,
        )
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = []
            for item in job_iter(book, cands, miner.cycle, miner.seen):
                if miner.stopped():
                    break
                futs.append(pool.submit(work, item))
                if len(futs) >= 800:
                    for fut in futs:
                        fut.result()
                    futs = []
                    live = live_nodes() or live
                    miner.node_ok = len(live)
            for fut in futs:
                fut.result()
        miner.cycle += 1
        miner.write_board()
        miner.write_heartbeat()
        print("CYCLE_DONE", miner.cycle, "jobs", miner.done, flush=True)

    miner.write_board()
    miner.write_heartbeat()
    print("DONE jobs=%s ok=%s err=%s left_h=%.2f" % (miner.done, miner.ok, miner.err, miner.remaining() / 3600.0), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
