"""Paper Ops Desk V2 (SPEC §29.5–29.8, docs/research_engine/PAPER_OPS_DESK_V2_DESIGN.md).

Three things, all read-only towards the research pipeline:
  * run manager  — start `python -m research_engine.ml1_live.daily` in the background with a lock file, expose progress + log;
  * journal      — owner's hand-entered fills / deposits; positions and cash are derived from events (never stored);
  * plan         — what to do today, on the real calendar, from the frozen V26.8 chain (signal every 21 sessions, hold 20).
No orders. No parameter of daily.py is reachable from here.
"""
from __future__ import print_function

import csv
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from app.service import paper_service as ps

ROOT = ps.ROOT
LIVE = ps.LIVE
SIGNALS = ps.SIGNALS
LEDGER_DIR = ps.LEDGER
BARS = LIVE / "bars"
RUNS = LIVE / "runs"
LOCK = RUNS / "CURRENT.json"
JOURNAL = LIVE / "paper" / "JOURNAL.json"
STATUS = LIVE / "STATUS.json"

CHAIN_ANCHOR = "2026-07-30"   # research_engine.ml1_live.CHAIN_ANCHOR_SIGNAL
FROZEN_END = "2026-08-28"     # ml1_live.FROZEN_END — STATUS asof before this is poison, not a holiday
HOLD = 20
STEP = HOLD + 1
LOT = 100
FEE_RESERVE = 200.0
DATA_READY_HOUR = 18          # BaoStock daily bars are complete ~17:30-18:00
UPDATE_WINDOW = "收盘后 18:30 以后更新；忘了就次日 08:30 前补。名单只看信号日收盘，平时不更新不会出错名单。"
COMMISSION_RATE = 0.0003
COMMISSION_MIN = 5.0
STAMP_TAX = 0.0005
STAGE_MARKERS = (  # (substring of a daily.py log line, stage label); later markers win
    ("ML1_LIVE asof_requested", "已选定截止日期"),
    ("ML1_LIVE_PANEL basics", "股票列表"),
    ("ML1_LIVE_PANEL bars plan", "日线：清点缺哪些天"),
    ("ML1_LIVE_PANEL bars fetching", "日线补漏（已有的跳过）"),
    ("ML1_LIVE_PANEL bars done", "日线完成"),
    ("ML1_LIVE_LAYERS margin", "融资融券"),
    ("ML1_LIVE_LAYERS holders", "股东户数"),
    ("ML1_LIVE_LAYERS index", "指数成分"),
    ("ML1_LIVE_PANEL live pack", "拼装面板"),
    ("ML1_LIVE_SCORE", "模型打分"),
    ("ML1_LIVE_LEDGER", "影子账本"),
    ("ML1_LIVE_TOP20", "短名单 / TOP20 账本"),
    ("ML7_REFRESH", "ML7 信息层增量下载"),
    ("_COMPILE", "ML7 信息层特征编译（约 3–5 分钟）"),
    ("ML7_FEATURES", "ML7 特征"),
    ("ML7_SCORE", "ML7 打分"),
    ("ML7_LEDGER", "ML7 账本"),
    ("ML1_LIVE DONE", "完成"),
)


# ----------------------------------------------------------------------------- helpers
def _now():
    return datetime.now()


def _load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _dump(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, default=str)
    os.replace(tmp, str(path))


def _days():
    # bypass paper_service's process cache so a finished update is seen at once
    ps._TRADING_DAYS = None
    days = ps._trading_days()
    if not days or days[-1] < "2020-01-01":
        _repair_live_calendar()
        ps._TRADING_DAYS = None
        days = ps._trading_days()
    return days


_WD = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
_REF_CAL = ROOT / "data" / "market" / "cn_a_share" / "reference" / "tm-cn-a-CALENDAR-20260830-000001.csv"


def _repair_live_calendar():
    """A killed daily.py can truncate live/calendar.csv (open-w then write). Rebuild from the frozen reference + dates already in live bars."""
    dst = LIVE / "calendar.csv"
    rows, seen = [], set()
    src = _REF_CAL if _REF_CAL.is_file() else dst
    if src.is_file():
        try:
            with open(src, encoding="utf-8", newline="") as fh:
                for r in csv.DictReader(fh):
                    d = r.get("calendar_date")
                    if not d or d in seen:
                        continue
                    seen.add(d)
                    rows.append({"calendar_date": d, "is_trading_day": r.get("is_trading_day"), "weekday": r.get("weekday") or _WD[datetime.strptime(d, "%Y-%m-%d").weekday()]})
        except OSError:
            pass
    sample = BARS / "sh.600000.csv"
    if not sample.is_file() and BARS.is_dir():
        sample = next(BARS.glob("*.csv"), None)
    if sample and Path(sample).is_file():
        try:
            with open(sample, encoding="utf-8", newline="") as fh:
                for r in csv.DictReader(fh):
                    d = r.get("date")
                    if not d or d in seen:
                        continue
                    seen.add(d)
                    rows.append({"calendar_date": d, "is_trading_day": 1, "weekday": _WD[datetime.strptime(d, "%Y-%m-%d").weekday()]})
        except OSError:
            pass
    if not rows:
        return
    rows.sort(key=lambda r: r["calendar_date"])
    last = datetime.strptime(rows[-1]["calendar_date"], "%Y-%m-%d").date()
    end = _now().date() + timedelta(days=120)
    d = last + timedelta(days=1)
    while d <= end:
        iso = d.isoformat()
        if iso not in seen:
            seen.add(iso)
            rows.append({"calendar_date": iso, "is_trading_day": 0 if d.weekday() >= 5 else 1, "weekday": _WD[d.weekday()]})
        d += timedelta(days=1)
    rows.sort(key=lambda r: r["calendar_date"])
    tmp = str(dst) + ".tmp"
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=("calendar_date", "is_trading_day", "weekday"))
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, str(dst))


def _idx(days, d):
    try:
        return days.index(d)
    except ValueError:
        return None


def _last_close(symbol):
    p = BARS / (symbol + ".csv")
    if not p.is_file():
        return None, None
    try:
        with open(p, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError:
        return None, None
    for r in reversed(rows):
        try:
            c = float(r.get("close") or 0)
        except ValueError:
            continue
        if c > 0:
            return c, r.get("date")
    return None, None


def _live_mark(symbol, lots, cost_in):
    """Same mark as the journal account: last close on disk. Missing close → cost, never ¥0."""
    px, pdate = _last_close(symbol)
    shares = (lots or 0) * LOT
    if px and px > 0 and shares:
        val = px * shares
        unreal = (val - cost_in) if cost_in is not None else None
        return px, pdate, val, unreal, False
    return None, None, (cost_in if cost_in is not None else None), None, True


def _est_fee(side, amount):
    fee = max(COMMISSION_MIN, amount * COMMISSION_RATE)
    if side == "SELL":
        fee += amount * STAMP_TAX
    return round(fee, 2)


# ----------------------------------------------------------------------------- chain calendar
def chain_signals(days, upto=None):
    """Signal dates every 21 sessions after the V28 anchor, up to `upto` (inclusive) or the end of the calendar."""
    i = _idx(days, CHAIN_ANCHOR)
    if i is None:
        return []
    out = []
    i += STEP
    while i < len(days):
        if upto and days[i] > upto:
            break
        out.append(days[i])
        i += STEP
    return out


def period_of(days, signal_date):
    i = _idx(days, signal_date)
    if i is None:
        return {}
    g = lambda k: days[k] if 0 <= k < len(days) else None  # noqa
    return {"signal_date": signal_date, "entry": g(i + 1), "exit_date": g(i + STEP), "next_signal": g(i + STEP), "next_entry": g(i + STEP + 1)}


# ----------------------------------------------------------------------------- freshness
def freshness(days, status, with_gap=False):
    now = _now()
    today = now.date().isoformat()
    calendar_stale = (not days) or (days[-1] < today)
    is_td = today in days
    before = [d for d in days if d < today]
    asof = (status or {}).get("asof_session") or ((status or {}).get("live_pack") or {}).get("asof")
    asof_bogus = bool(asof and asof < FROZEN_END)
    if calendar_stale:
        # Local calendar file does not reach today (truncated write ≠ holiday). After 18:00 asof is today so daily.py can refresh the calendar.
        last_completed = today if now.hour >= DATA_READY_HOUR else (before[-1] if before else today)
        stale = 1
        needs = True
    else:
        last_completed = today if (is_td and now.hour >= DATA_READY_HOUR) else (before[-1] if before else None)
        stale = 0
        if asof and last_completed and asof < last_completed:
            stale = len([d for d in days if asof < d <= last_completed])
        needs = stale > 0
    if asof_bogus:
        needs = True
        stale = max(stale, 1)
    nxt = [d for d in days if d > today]
    out = {"today": today, "weekday": now.strftime("%a"), "today_is_trading_day": is_td, "calendar_stale": calendar_stale,
           "last_completed_session": last_completed, "next_trading_day": nxt[0] if nxt else None, "asof_session": asof,
           "asof_bogus": asof_bogus, "stale_sessions": stale, "needs_update": needs, "data_ready_after": "%02d:00" % DATA_READY_HOUR,
           "update_window": UPDATE_WINDOW, "clock": now.strftime("%Y-%m-%d %H:%M")}
    if with_gap and last_completed:
        out["bars_gap"] = bars_coverage(last_completed)
        out["needs_gapfill"] = (not out["needs_update"]) and int((out["bars_gap"] or {}).get("n_missing") or 0) > 0
    return out


# ----------------------------------------------------------------------------- run manager
def _pid_cmd(pid):
    try:
        import psutil
        return " ".join(psutil.Process(int(pid)).cmdline() or [])
    except Exception:
        pass
    if os.name == "nt":
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Process -Filter 'ProcessId=%d').CommandLine" % int(pid)],
                capture_output=True, text=True, timeout=10,
            ).stdout or ""
            return (out or "").strip()
        except Exception:
            return ""
    return ""


def _find_daily_pids():
    """Any python running ml1_live.daily (lock file can vanish; wmic is gone on some Win11)."""
    pids = []
    if os.name != "nt":
        return pids
    cmd = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "$_.Name -match 'python' -and $_.CommandLine -and "
        "($_.CommandLine -like '*ml1_live.daily*' -or $_.CommandLine -like '*research_engine.ml1_live.daily*') "
        "} | Select-Object -ExpandProperty ProcessId"
    )
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=15).stdout or ""
    except Exception:
        return pids
    for ln in out.splitlines():
        s = ln.strip()
        if s.isdigit():
            pids.append(int(s))
    return pids


def _pid_is_daily(pid):
    cmd = (_pid_cmd(pid) or "").lower()
    return "ml1_live.daily" in cmd or "research_engine.ml1_live" in cmd


def _pid_alive(pid):
    if not pid:
        return False
    try:
        import psutil
        return psutil.pid_exists(int(pid)) and psutil.Process(int(pid)).status() != psutil.STATUS_ZOMBIE
    except ImportError:
        pass
    except Exception:  # noqa
        return False
    try:
        if os.name == "nt":
            out = subprocess.run(["tasklist", "/FI", "PID eq %d" % int(pid), "/NH", "/FO", "CSV"], capture_output=True, text=True, timeout=10).stdout
            return ('"%d"' % int(pid)) in out
        os.kill(int(pid), 0)
        return True
    except Exception:  # noqa
        return False


def _python():
    # daily.py needs baostock/lightgbm; Master venv often does not. Override with TRADEMIND_DAILY_PYTHON.
    return os.environ.get("TRADEMIND_DAILY_PYTHON") or shutil.which("python") or sys.executable


_COV = {"t": 0.0, "asof": None, "val": None}


def _last_csv_date(path):
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            n = fh.tell()
            if n <= 0:
                return None
            fh.seek(max(0, n - 800))
            chunk = fh.read().decode("utf-8", "replace")
    except OSError:
        return None
    for ln in reversed(chunk.splitlines()):
        if not ln or ln.startswith("date"):
            continue
        return ln.split(",", 1)[0]
    return None


def bars_coverage(asof, ttl=30):
    """How many live bar files already include `asof` (last row date >= asof). Cached ~30s — not on the 8s poll path."""
    now = time.time()
    if _COV["val"] is not None and _COV["asof"] == asof and now - _COV["t"] < ttl:
        return _COV["val"]
    n_files = n_ok = n_missing = n_empty = 0
    if asof and BARS.is_dir():
        for p in BARS.glob("*.csv"):
            n_files += 1
            last = _last_csv_date(p)
            if not last:
                n_empty += 1
                n_missing += 1
            elif last >= asof:
                n_ok += 1
            else:
                n_missing += 1
    out = {"asof": asof, "n_files": n_files, "n_ok": n_ok, "n_missing": n_missing, "n_empty": n_empty}
    _COV["t"], _COV["asof"], _COV["val"] = now, asof, out
    return out


def _date_reason(fresh):
    asof = fresh.get("last_completed_session") or "—"
    if not fresh.get("today_is_trading_day"):
        return "今天休市，截止日期自动回跳到最近一个开盘日 %s（不会用明天）。" % asof
    hour = _now().hour
    if hour < DATA_READY_HOUR:
        return "今天还没收盘齐（%s 前），截止日期是上一交易日 %s。" % (fresh.get("data_ready_after") or "18:00", asof)
    return "今天已收盘，截止日期就是今天 %s。" % asof


def _decorate_run(out, fresh=None, coverage=None, **extra):
    if fresh is None:
        fresh = freshness(_days(), _load(STATUS, {}) or {})
    out["asof_target"] = fresh.get("last_completed_session")
    out["needs_update"] = fresh.get("needs_update")
    out["stale_sessions"] = fresh.get("stale_sessions")
    if coverage is not None:
        out["bars_gap"] = coverage
    out.update(extra)
    return out


def _log_tail(path, n=25):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return []
    return lines[-n:]


def _stage(lines):
    stage = "启动中（导入模型库 / 连接 BaoStock）"
    for ln in lines:
        for marker, label in STAGE_MARKERS:
            if marker in ln:
                stage = label
        if "ML1_LIVE asof_requested" in ln:
            stage = "截止日期 " + ln.split()[-1]
        if "bars plan" in ln and "gap" in ln:
            bits = ln.split()
            try:
                stage = "日线缺口 %s / %s · 截止日期 %s" % (bits[bits.index("gap") + 1], bits[bits.index("/") + 1], bits[bits.index("asof") + 1])
            except (ValueError, IndexError):
                stage = "日线：清点缺哪些天"
        if "bars fetching" in ln:
            bits = ln.split()
            try:
                i = bits.index("fetching")
                n = bits[bits.index("fetched") + 1] if "fetched" in bits else "?"
                stage = "日线正在拉 %s · 已补 %s 只" % (bits[i + 1], n)
            except (ValueError, IndexError):
                stage = "日线补漏"
        if "ML1_LIVE_PANEL bars" in ln and "done" not in ln and "fetching" not in ln and "plan" not in ln:
            parts = ln.split()
            if len(parts) > 3 and parts[2].isdigit():
                stage = "日线 %s 只已补" % parts[2]
        if "BAR_HANG" in ln:
            stage = "日线：一只卡住已跳过，继续"
        if "PAPER_OPS STOP" in ln:
            stage = "已停止"
        if "ML1_LIVE_LAYERS holders" in ln and "/" in ln:
            parts = ln.split()
            try:
                k = parts.index("/")
                stage = "股东户数 %s/%s" % (parts[k - 1], parts[k + 1])
            except (ValueError, IndexError):
                pass
    return stage


def _last_run_summary():
    st = _load(STATUS, {}) or {}
    errs = []
    for k, v in (st.get("steps") or {}).items():
        if isinstance(v, dict) and v.get("error"):
            errs.append("%s: %s" % (k, v["error"]))
    if isinstance(st.get("ml7"), dict) and st["ml7"].get("error"):
        errs.append("ml7: " + st["ml7"]["error"])
    return {"asof_session": st.get("asof_session"), "started_at": st.get("started_at"), "elapsed_s": st.get("elapsed_s"),
            "fetch": (st.get("steps") or {}).get("fetch"), "errors": errs, "signal": st.get("signal"),
            "ledger_top20": {k: (st.get("ledger_top20") or {}).get(k) for k in ("n_periods", "n_periods_closed", "equity_end_closed", "mtm_equity", "open_signal_date")}}


def run_status():
    lock = _load(LOCK, None)
    out = {"running": False, "pid": None, "started_at": None, "elapsed_s": None, "stage": None, "log": None, "log_tail": [],
           "last_run": _last_run_summary(), "last_failed": None, "python": _python(), "stopped": False, "skipped": False}
    if lock:
        pid = lock.get("pid")
        tail = _log_tail(lock.get("log"))
        out.update({"pid": pid, "started_at": lock.get("started_at"), "log": lock.get("log"), "log_tail": tail})
        if not pid:
            if time.time() - float(lock.get("t0") or 0) < 30:
                out["running"] = True
                out["elapsed_s"] = round(time.time() - float(lock.get("t0", time.time())), 0)
                out["stage"] = "正在启动"
            else:
                _archive_lock(lock, False, stopped=False)
                out["stage"] = "中断/失败"
                out["last_failed"] = {"started_at": lock.get("started_at"), "log": lock.get("log"), "tail": tail[-8:]}
        else:
            cmd = _pid_cmd(pid)
            alive = _pid_alive(pid)
            ours = _pid_is_daily(pid)
            young = time.time() - float(lock.get("t0") or 0) < 15
            # If the pid is alive but cmdline cannot be read, do not steal the lock (PID reuse is the other branch).
            still = alive and (ours or young or not cmd)
            if still:
                out["running"] = True
                out["elapsed_s"] = round(time.time() - float(lock.get("t0", time.time())), 0)
                out["stage"] = _stage(tail) if tail else "更新进行中"
            else:
                done = any("ML1_LIVE DONE" in ln for ln in tail)
                stopped = any("PAPER_OPS STOP" in ln for ln in tail)
                out["stage"] = "完成" if done else ("已停止" if stopped else "中断/失败")
                out["stopped"] = stopped and not done
                if not done and not stopped:
                    out["last_failed"] = {"started_at": lock.get("started_at"), "log": lock.get("log"), "tail": tail[-8:]}
                _archive_lock(lock, done, stopped=stopped and not done)
    if not out["running"]:
        orphans = _find_daily_pids()
        if orphans:
            out["running"] = True
            out["pid"] = orphans[0]
            out["stage"] = "发现已有更新进程（锁文件丢了）"
            out["elapsed_s"] = None
            if not lock:
                _dump(LOCK, {"pid": orphans[0], "t0": time.time(), "started_at": _now().strftime("%Y-%m-%dT%H:%M:%S"),
                             "log": None, "args": [], "asof": None, "recovered": True})
    hist = _load(RUNS / "HISTORY.json", []) or []
    out["history"] = hist[-10:]
    if not lock and hist:
        last = hist[-1]
        out["log"] = last.get("log")
        out["log_tail"] = _log_tail(out["log"], 40)
        if last.get("ok"):
            out["stage"] = "完成"
        elif last.get("stopped"):
            out["stage"] = "已停止"
            out["stopped"] = True
        else:
            out["stage"] = "中断/失败"
    if out["last_failed"] is None and hist:
        # Only the most recent run counts: a failure that was followed by a successful run is history, not a warning.
        h = hist[-1]
        if not h.get("ok") and not h.get("stopped"):
            out["last_failed"] = {"started_at": h.get("started_at"), "log": h.get("log"), "tail": h.get("tail")}
    return _decorate_run(out)


def _archive_lock(lock, ok, stopped=False):
    hist = _load(RUNS / "HISTORY.json", []) or []
    hist.append({"started_at": lock.get("started_at"), "ended_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "ok": ok,
                 "stopped": stopped, "log": lock.get("log"), "tail": _log_tail(lock.get("log"), 8), "args": lock.get("args"),
                 "asof": lock.get("asof")})
    _dump(RUNS / "HISTORY.json", hist[-200:])
    try:
        os.remove(str(LOCK))
    except OSError:
        pass


def _kill_pid(pid):
    pid = int(pid)
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=30)
        return
    try:
        os.kill(pid, 15)
    except OSError:
        pass
    time.sleep(1)
    if _pid_alive(pid):
        try:
            os.kill(pid, 9)
        except OSError:
            pass


def _try_claim_run(meta):
    """Create CURRENT.json exclusively so two Master workers cannot both spawn daily.py."""
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        fd = os.open(str(LOCK), flags)
    except OSError:
        return False
    try:
        os.write(fd, json.dumps(meta, ensure_ascii=False).encode("utf-8"))
    finally:
        os.close(fd)
    return True


def _recent_baostock_blocked(minutes=120):
    cutoff = time.time() - minutes * 60
    if not RUNS.is_dir():
        return False
    logs = sorted(RUNS.glob("RUN_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:8]
    for p in logs:
        try:
            if p.stat().st_mtime < cutoff:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")[-12000:]
        except OSError:
            continue
        if "黑名单" in text:
            return True
    return False


def stop_update():
    lock = _load(LOCK, None)
    pids = list(_find_daily_pids())
    if lock and lock.get("pid") and _pid_is_daily(lock.get("pid")):
        pid = int(lock["pid"])
        if pid not in pids:
            pids.append(pid)
    if not pids:
        out = run_status()
        return _decorate_run(out, stopped=False, note="当前没有在跑的更新。")
    logp = (lock or {}).get("log")
    try:
        if logp:
            with open(logp, "a", encoding="utf-8") as fh:
                fh.write("\nPAPER_OPS STOP requested %s pids %s\n" % (_now().strftime("%Y-%m-%dT%H:%M:%S"), pids))
    except OSError:
        pass
    for pid in pids:
        _kill_pid(pid)
    time.sleep(1.2)
    left = [p for p in pids if _pid_alive(p)]
    if left:
        raise RuntimeError("停止失败：进程 %s 仍在。可在任务管理器结束 python。" % left)
    out = run_status()
    return _decorate_run(out, stopped=True, note="已停止。已下好的日线会留着，下次点更新从漏的票继续。")


def start_update(force=False):
    RUNS.mkdir(parents=True, exist_ok=True)
    orphans = _find_daily_pids()
    if orphans:
        cur = run_status()
        if force:
            raise RuntimeError("已有一次更新在跑（pid %s）。要停掉请点「停止更新」。" % orphans[0])
        cur["reused"] = True
        cur["running"] = True
        cur["pid"] = orphans[0]
        cur["note"] = "已有一次更新在跑（pid %s）。要点停止用右上角「停止更新」。不要连点。" % orphans[0]
        return cur
    cur = run_status()
    if cur["running"]:
        if force:
            raise RuntimeError("已有一次更新在跑（pid %s）。要停掉请点「停止更新」。" % cur["pid"])
        cur["reused"] = True
        cur["note"] = "已有一次更新在跑。要点停止用右上角「停止更新」。不要连点。"
        return cur
    fresh = freshness(_days(), _load(STATUS, {}) or {})
    asof = fresh.get("last_completed_session") or _now().date().isoformat()
    reason = _date_reason(fresh)
    local = "本地 STATUS 标签是 %s。" % (fresh.get("asof_session") or "无")
    blocked = _recent_baostock_blocked()
    bogus = bool(fresh.get("asof_bogus"))
    skip_fetch = bogus or blocked
    # Only scan bar tails when the calendar is already current — otherwise spawn immediately.
    cov = None
    n_miss = 0
    if not fresh.get("needs_update") and not skip_fetch:
        cov = bars_coverage(asof)
        n_miss = int(cov.get("n_missing") or 0)
        if not force and n_miss == 0:
            return _decorate_run(run_status(), fresh, cov, skipped=True, reused=False,
                                 note="%s %s 日线没有缺口。没有新任务。" % (reason, local))
    if blocked and not bogus and not fresh.get("needs_update"):
        return _decorate_run(run_status(), fresh, cov, skipped=True, reused=False,
                             note="BaoStock 刚把本机拉黑了（东财正常）。本地已是 %s，名单和账本都是最新的。先不要连点，几小时后再补漏。" % (fresh.get("asof_session") or asof))
    bits = [reason, local]
    if bogus:
        bits.append("截止日期标签被写坏了（不是行情回到 2007）。这次用本地日线重算到 %s，不连东财。" % asof)
    elif blocked:
        bits.append("东财暂不可用（黑名单）。这次只用本地已有日线重算，不连网。过一阵再点更新补漏。")
    elif fresh.get("needs_update"):
        bits.append("落后 %s 个交易日，会补缺的日线（已经有的票跳过）。" % fresh.get("stale_sessions"))
    elif n_miss > 0:
        bits.append("没有新的交易日，但有 %s 只日线缺 %s，这次只补漏。" % (n_miss, asof))
    ts = _now().strftime("%Y%m%d_%H%M%S")
    log = RUNS / ("RUN_%s.log" % ts)
    pending = {"pid": None, "t0": time.time(), "started_at": _now().strftime("%Y-%m-%dT%H:%M:%S"),
               "log": str(log), "args": ["-m", "research_engine.ml1_live.daily", "--asof", asof], "asof": asof, "pending": True}
    if not _try_claim_run(pending):
        cur = run_status()
        cur["reused"] = True
        cur["note"] = "已有一次更新在跑。要点停止用右上角「停止更新」。"
        return cur
    args = [_python(), "-m", "research_engine.ml1_live.daily", "--asof", asof]
    if skip_fetch:
        args.append("--skip-fetch")
        pending["args"] = args[1:]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    fh = open(str(log), "w", encoding="utf-8")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if os.name == "nt":
        flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        proc = subprocess.Popen(args, cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT, env=env, close_fds=False, creationflags=flags)
    except Exception:
        try:
            os.remove(str(LOCK))
        except OSError:
            pass
        raise
    _dump(LOCK, {"pid": proc.pid, "t0": time.time(), "started_at": _now().strftime("%Y-%m-%dT%H:%M:%S"),
                 "log": str(log), "args": args[1:], "asof": asof, "skip_fetch": skip_fetch})
    _COV["val"] = None
    out = run_status()
    out["reused"] = False
    out["skipped"] = False
    return _decorate_run(out, fresh, cov, note=" ".join(bits))


# ----------------------------------------------------------------------------- journal
def load_journal():
    j = _load(JOURNAL, None) or {"account": {"base_cash": 0.0}, "events": []}
    j.setdefault("account", {"base_cash": 0.0})
    j.setdefault("events", [])
    return j


def _make_event(body, keep_id=None, keep_ts=None, reestimate_fee=True):
    typ = str(body.get("type") or "").upper()
    if typ not in ("BUY", "SELL", "DEPOSIT", "WITHDRAW", "NOTE"):
        raise ValueError("type 必须是 BUY / SELL / DEPOSIT / WITHDRAW / NOTE")
    date = body.get("date") or _now().date().isoformat()
    ev = {"id": keep_id or uuid.uuid4().hex[:10], "ts": keep_ts or _now().strftime("%Y-%m-%dT%H:%M:%S"),
          "type": typ, "date": date, "note": (body.get("note") or "")[:200]}
    if typ in ("BUY", "SELL"):
        sym = str(body.get("symbol") or "").strip()
        if not sym:
            raise ValueError("symbol 必填")
        if "." not in sym:
            sym = ("sh." if sym.startswith("6") else "sz.") + sym
        lots = int(body.get("lots") or 0)
        price = float(body.get("price") or 0)
        if lots <= 0 or price <= 0:
            raise ValueError("lots 和 price 必须 > 0")
        amount = round(lots * LOT * price, 2)
        fee = body.get("fee")
        if fee is None or (reestimate_fee and fee == ""):
            fee = _est_fee(typ, amount)
        else:
            fee = float(fee)
        ev.update({"symbol": sym, "lots": lots, "price": price, "amount": amount, "fee": round(fee, 2)})
    elif typ in ("DEPOSIT", "WITHDRAW"):
        amt = float(body.get("amount") or 0)
        if amt <= 0:
            raise ValueError("amount 必须 > 0")
        ev["amount"] = round(amt, 2)
    return ev


def add_event(body):
    ev = _make_event(body)
    j = load_journal()
    j["events"].append(ev)
    j["events"].sort(key=lambda e: (e.get("date") or "", e.get("ts") or ""))
    _dump(JOURNAL, j)
    return ev


def update_event(event_id, body):
    j = load_journal()
    idx = next((i for i, e in enumerate(j["events"]) if e.get("id") == event_id), None)
    if idx is None:
        raise KeyError(event_id)
    old = j["events"][idx]
    merged = dict(old)
    for k, v in (body or {}).items():
        if k in ("id", "ts"):
            continue
        if v is not None:
            merged[k] = v
    reestimate = "fee" not in (body or {}) or body.get("fee") is None
    if reestimate:
        merged.pop("fee", None)
    ev = _make_event(merged, keep_id=old["id"], keep_ts=old.get("ts"), reestimate_fee=reestimate)
    j["events"][idx] = ev
    j["events"].sort(key=lambda e: (e.get("date") or "", e.get("ts") or ""))
    _dump(JOURNAL, j)
    return ev


def delete_event(event_id):
    j = load_journal()
    before = len(j["events"])
    j["events"] = [e for e in j["events"] if e.get("id") != event_id]
    if len(j["events"]) == before:
        raise KeyError(event_id)
    _dump(JOURNAL, j)
    return True


def derive_account(journal, days):
    """Cash + FIFO positions from events. Marks with the last close on disk."""
    names = ps._stock_names()
    cash = float((journal.get("account") or {}).get("base_cash") or 0.0)
    deposits = withdrawals = realized = fees = 0.0
    pos = {}  # symbol -> {"lots", "cost", "buy_date", "fills":[...]}
    for e in journal.get("events") or []:
        t = e.get("type")
        if t == "DEPOSIT":
            cash += e["amount"]
            deposits += e["amount"]
        elif t == "WITHDRAW":
            cash -= e["amount"]
            withdrawals += e["amount"]
        elif t == "BUY":
            cash -= e["amount"] + e["fee"]
            fees += e["fee"]
            p = pos.setdefault(e["symbol"], {"lots": 0, "cost": 0.0, "buy_date": e["date"], "fills": []})
            p["lots"] += e["lots"]
            p["cost"] += e["amount"] + e["fee"]
            p["fills"].append(e)
        elif t == "SELL":
            cash += e["amount"] - e["fee"]
            fees += e["fee"]
            p = pos.get(e["symbol"])
            if p and p["lots"] > 0:
                take = min(e["lots"], p["lots"])
                avg = p["cost"] / p["lots"] if p["lots"] else 0.0
                realized += (e["amount"] - e["fee"]) * (take / float(e["lots"])) - avg * take
                p["lots"] -= take
                p["cost"] -= avg * take
                if p["lots"] <= 0:
                    p["lots"], p["cost"] = 0, 0.0
                    p["closed"] = e["date"]
            else:
                realized += e["amount"] - e["fee"]
    positions, mv = [], 0.0
    for sym, p in pos.items():
        if p["lots"] <= 0:
            continue
        px, pdate = _last_close(sym)
        shares = p["lots"] * LOT
        val = px * shares if px else None
        if val:
            mv += val
        last_buy = next((f for f in reversed(p.get("fills") or []) if f.get("type") == "BUY"), None)
        positions.append({"symbol": sym, "name": names.get(sym, ""), "lots": p["lots"], "shares": shares, "avg_price": round(p["cost"] / shares, 4) if shares else None,
                          "buy_date": p["buy_date"], "mark_price": px, "mark_date": pdate, "cost_in": round(p["cost"], 2),
                          "market_value": round(val, 2) if val else None, "unrealized": round(val - p["cost"], 2) if val else None, "status": "HELD",
                          "buy_event_id": (last_buy or {}).get("id"), "buy_price": (last_buy or {}).get("price"), "buy_lots": (last_buy or {}).get("lots")})
    positions.sort(key=lambda r: r["symbol"])
    month = _now().strftime("%Y-%m")
    dep_months = sorted(set((e.get("date") or "")[:7] for e in journal.get("events") or [] if e.get("type") == "DEPOSIT"))
    n_ev = len(journal.get("events") or [])
    return {"source": "JOURNAL" if n_ev else "MODEL", "n_events": n_ev, "cash": round(cash, 2), "market_value": round(mv, 2), "equity": round(cash + mv, 2),
            "positions": positions, "deposits_total": round(deposits, 2), "withdrawals_total": round(withdrawals, 2),
            "realized_pnl": round(realized, 2), "fees_total": round(fees, 2), "month_contrib_logged": month in dep_months, "deposit_months": dep_months}


# ----------------------------------------------------------------------------- history
def _ledger():
    return _load(LEDGER_DIR / "LEDGER_TOP20.json", {}) or {}


def history(days, ledger):
    names = ps._stock_names()
    periods = list(ledger.get("periods") or [])
    chain = set(chain_signals(days))
    out = []
    for k, p in enumerate(periods):
        sd = p.get("signal_date")
        sl = _load(SIGNALS / ("SHORTLIST_SHADOW_%s.json" % sd), {}) or {}
        fills = ((ledger.get("fills_by_period") or {}).get(sd)) or []
        fill_by = dict((f.get("symbol"), f) for f in fills)
        rows = []
        for n in sl.get("names") or []:
            f = fill_by.get(n.get("symbol")) or {}
            lots = f.get("lots")
            cost = f.get("cost_in")
            px, pdate, val, unreal, missing = _live_mark(n.get("symbol"), lots, cost) if lots else (None, None, None, None, False)
            last_px = px if px else n.get("last_close")
            pnl = f.get("net") if f.get("net") is not None else (unreal if unreal is not None else f.get("unrealized"))
            rows.append({"rank": n.get("rank"), "symbol": n.get("symbol"), "name": names.get(n.get("symbol"), ""), "score": n.get("score"),
                         "last_close": last_px, "mark_date": pdate, "lots_100_est": n.get("lots_100_est"), "lots": lots, "open": f.get("open"),
                         "status": f.get("status"), "pnl": pnl, "mark_missing": missing})
        per = period_of(days, sd)
        unreal = p.get("unrealized")
        equity = p.get("equity") or p.get("mtm_equity")
        if p.get("status") == "OPEN":
            cash = p.get("cash")
            mv = sum((n.get("pnl") or 0) + (fill_by.get(n.get("symbol") or "", {}).get("cost_in") or 0) for n in rows if n.get("lots"))
            if cash is not None:
                equity = round(float(cash) + mv, 2)
                unreal = round(equity - float(p.get("equity_end_closed") or sl.get("capital_yuan") or 20000), 2)
            else:
                live_u = [n.get("pnl") for n in rows if n.get("pnl") is not None]
                if live_u:
                    unreal = round(sum(live_u), 2)
        out.append({"period_no": k + 1, "signal_date": sd, "entry": p.get("entry") or per.get("entry"), "exit": p.get("exit") or per.get("exit_date"),
                    "status": p.get("status"), "n_names": p.get("n_names") or len(rows), "n_fill": p.get("n_fill"), "capital_ret": p.get("capital_ret"),
                    "ret_unrealized": p.get("ret_unrealized"), "ew_ret": p.get("ew_ret"), "lo_minus_ew": p.get("lo_minus_ew"), "net_yuan": p.get("net_yuan"),
                    "unrealized": unreal, "equity": equity, "is_chain": sd in chain or sd == CHAIN_ANCHOR,
                    "unit_yuan": sl.get("unit_yuan"), "capital_yuan": sl.get("capital_yuan"), "names": rows})
    # forced lists on non-chain days (e.g. --force-score) are shown, but flagged
    for fn in sorted(os.listdir(SIGNALS)) if SIGNALS.is_dir() else []:
        if fn.startswith("SHORTLIST_20") and fn.endswith(".json"):
            sd = fn[len("SHORTLIST_"):-len(".json")]
            if sd not in chain and all(h["signal_date"] != sd for h in out):
                sl = _load(SIGNALS / fn, {}) or {}
                out.append({"period_no": None, "signal_date": sd, "entry": None, "exit": None, "status": "PREVIEW_NON_CHAIN", "n_names": sl.get("n_names"),
                            "is_chain": False, "unit_yuan": sl.get("unit_yuan"), "capital_yuan": sl.get("capital_yuan"),
                            "names": [{"rank": n.get("rank"), "symbol": n.get("symbol"), "name": names.get(n.get("symbol"), ""), "score": n.get("score"),
                                       "last_close": n.get("last_close"), "lots_100_est": n.get("lots_100_est")} for n in sl.get("names") or []],
                            "note": "非操作日强制打分的预览名单，不是当期持仓，不进账本"})
    out.sort(key=lambda h: h["signal_date"] or "")
    return out


def history_actual(days, journal, upto):
    """The owner's own periods, derived from journal fills: one row per chain period up to `upto` (last completed session or today).
    A period the owner did not trade is shown as NOT_TRADED so the timeline is never confused with the model's."""
    names = ps._stock_names()
    events = [e for e in journal.get("events") or [] if e.get("type") in ("BUY", "SELL")]
    sigs = chain_signals(days, upto=upto)
    out = []
    for k, sd in enumerate(sigs):
        per = period_of(days, sd)
        entry, nxt_entry = per.get("entry"), per.get("next_entry")
        if not entry:
            continue
        # buys from the entry day until (excluding) the next period's entry; sells until and including the next entry day
        buys = [e for e in events if e["type"] == "BUY" and entry <= e["date"] < (nxt_entry or "9999")]
        sells = [e for e in events if e["type"] == "SELL" and entry < e["date"] <= (nxt_entry or "9999")]
        if not buys and not sells:
            st = "PENDING_ENTRY" if entry > (upto or "") else "NOT_TRADED"
            out.append({"period_no": k + 1, "signal_date": sd, "entry": entry, "exit": per.get("exit_date"), "status": st, "n_names": 0,
                        "invested": 0.0, "proceeds": 0.0, "pnl": None, "capital_ret": None, "names": [], "is_chain": True})
            continue
        by = {}
        for e in buys:
            r = by.setdefault(e["symbol"], {"symbol": e["symbol"], "name": names.get(e["symbol"], ""), "lots": 0, "cost": 0.0, "sold_lots": 0, "proceeds": 0.0, "buy_date": e["date"]})
            r["lots"] += e["lots"]
            r["cost"] += e["amount"] + e["fee"]
        for e in sells:
            r = by.setdefault(e["symbol"], {"symbol": e["symbol"], "name": names.get(e["symbol"], ""), "lots": 0, "cost": 0.0, "sold_lots": 0, "proceeds": 0.0, "buy_date": None})
            r["sold_lots"] += e["lots"]
            r["proceeds"] += e["amount"] - e["fee"]
            r["sell_date"] = e["date"]
        rows, invested, proceeds, mv_open = [], 0.0, 0.0, 0.0
        all_closed = True
        for r in by.values():
            open_lots = max(r["lots"] - r["sold_lots"], 0)
            px, _d = _last_close(r["symbol"]) if open_lots else (None, None)
            open_val = (px or 0) * open_lots * LOT
            if open_lots:
                all_closed = False
            unit_cost = r["cost"] / r["lots"] if r["lots"] else 0.0
            pnl = r["proceeds"] + open_val - r["cost"] if r["lots"] else r["proceeds"]
            rows.append({"symbol": r["symbol"], "name": r["name"], "lots": r["lots"], "sold_lots": r["sold_lots"], "open_lots": open_lots, "buy_date": r["buy_date"],
                         "sell_date": r.get("sell_date"), "cost_in": round(r["cost"], 2), "avg_price": round(unit_cost / LOT, 4) if r["lots"] else None,
                         "proceeds": round(r["proceeds"], 2), "mark_price": px, "pnl": round(pnl, 2), "status": "CLOSED" if not open_lots else "HELD"})
            invested += r["cost"]
            proceeds += r["proceeds"]
            mv_open += open_val
        pnl = proceeds + mv_open - invested
        out.append({"period_no": k + 1, "signal_date": sd, "entry": entry, "exit": per.get("exit_date"), "status": "CLOSED" if all_closed else "OPEN",
                    "n_names": len(rows), "invested": round(invested, 2), "proceeds": round(proceeds, 2), "open_value": round(mv_open, 2), "pnl": round(pnl, 2),
                    "capital_ret": round(pnl / invested, 4) if invested else None, "names": sorted(rows, key=lambda r: r["symbol"]), "is_chain": True})
    return out


# ----------------------------------------------------------------------------- plan
def _universe(signal_date):
    for pre in ("SIGNAL_", "SHADOW_"):
        d = _load(SIGNALS / ("%s%s.json" % (pre, signal_date)), None)
        if d and d.get("names"):
            return d["names"]
    return None


def _model_positions(ledger, signal_date, days):
    names = ps._stock_names()
    fills = ((ledger.get("fills_by_period") or {}).get(signal_date)) or []
    per = period_of(days, signal_date)
    rows = []
    for f in fills:
        sym = f.get("symbol")
        lots = f.get("lots") or 0
        cost = f.get("cost_in")
        px, pdate, val, unreal, missing = _live_mark(sym, lots, cost)
        rows.append({"symbol": sym, "name": names.get(sym, ""), "lots": lots, "shares": lots * LOT, "avg_price": f.get("open"),
                     "buy_date": per.get("entry"), "mark_price": px, "mark_date": pdate, "cost_in": cost,
                     "market_value": round(val, 2) if val is not None else None,
                     "unrealized": round(unreal, 2) if unreal is not None else None,
                     "status": f.get("status") or "FILL", "mark_missing": missing})
    return rows


def _model_summary_live(top20, positions):
    out = {k: top20.get(k) for k in ("contract", "capital_yuan", "monthly_contrib", "n_target", "equity_end_closed", "cash", "positions_mv", "mtm_equity", "unrealized", "n_mark_missing",
                                     "n_periods", "n_periods_closed", "open_signal_date", "open_mark_date", "deposits_to_date")}
    if not positions:
        return out
    mv = sum((p.get("market_value") or 0.0) for p in positions)
    cash = out.get("cash")
    out["positions_mv"] = round(mv, 2)
    out["n_mark_missing"] = int(sum(1 for p in positions if p.get("mark_missing")))
    dates = [p.get("mark_date") for p in positions if p.get("mark_date")]
    if dates:
        out["open_mark_date"] = max(dates)
    if cash is not None:
        out["mtm_equity"] = round(float(cash) + mv, 2)
        base = out.get("equity_end_closed")
        if base is None:
            base = (out.get("capital_yuan") or 20000.0) + (out.get("deposits_to_date") or 0.0)
        out["unrealized"] = round(out["mtm_equity"] - float(base), 2)
    return out


def _buy_list(signal_date, settings, cash_available, source):
    uni = _universe(signal_date)
    sl = _load(SIGNALS / ("SHORTLIST_SHADOW_%s.json" % signal_date), None) or _load(SIGNALS / ("SHORTLIST_%s.json" % signal_date), None)
    names = ps._stock_names()
    if source == "JOURNAL" and uni:
        cap = max(float(cash_available), 0.0)
        pv = ps.preview_lots(uni, cap, int(settings.get("n_target") or 10), float(settings.get("max_price") or 100.0), settings.get("boards") or "MAIN", 1.0) if cap >= LOT else {"names": [], "est_invested_yuan": 0.0, "unit_yuan": None}
        rows, planned, unit = pv["names"], pv["est_invested_yuan"], pv.get("unit_yuan")
        basis = "按你的可用现金 ¥%.0f 重算（同一套 V26.8 算术）" % cap
    elif sl:
        rows, planned, unit = sl.get("names") or [], sl.get("est_invested_yuan"), sl.get("unit_yuan")
        basis = "官方影子账本 ¥%.0f 的手数（你还没登记成交/入金）" % float(sl.get("capital_yuan") or 0)
    else:
        return [], None, None, "名单文件不存在"
    for r in rows:
        r["name"] = names.get(r.get("symbol"), "")
    return rows, planned, unit, basis


def _split_period_list(signal_date, account, remark_latest=False):
    """Keep the period's recommended names on screen after a partial fill.
    Remaining = not yet held; logged = already in the journal. Names never vanish mid-registration."""
    sl = _load(SIGNALS / ("SHORTLIST_SHADOW_%s.json" % signal_date), None) or _load(SIGNALS / ("SHORTLIST_%s.json" % signal_date), None) or {}
    names = ps._stock_names()
    held = dict((p["symbol"], p) for p in (account.get("positions") or []))
    remaining, logged, planned = [], [], 0.0
    for n in sl.get("names") or []:
        r = {"rank": n.get("rank"), "symbol": n.get("symbol"), "name": names.get(n.get("symbol"), ""), "score": n.get("score"),
             "last_close": n.get("last_close"), "lots_100_est": n.get("lots_100_est"), "est_yuan": n.get("est_yuan")}
        if remark_latest:
            px, pdate = _last_close(r["symbol"])
            if px:
                r["last_close"], r["mark_date"] = px, pdate
                r["est_yuan"] = round((r.get("lots_100_est") or 0) * LOT * px, 2)
        p = held.get(r["symbol"])
        if p:
            r.update({"logged": True, "lots": p.get("lots"), "avg_price": p.get("avg_price"), "buy_event_id": p.get("buy_event_id"),
                      "buy_date": p.get("buy_date"), "unrealized": p.get("unrealized")})
            logged.append(r)
        else:
            r["logged"] = False
            remaining.append(r)
            planned += r.get("est_yuan") or 0.0
    return remaining, logged, planned


def _attach_period_list(out, signal_date, settings, account, source, remark_latest, asof, leftover=None):
    if source != "JOURNAL":
        return
    remaining, logged, planned = _split_period_list(signal_date, account, remark_latest=remark_latest)
    out["buy_list"] = remaining
    out["logged_list"] = logged
    out["continue_register"] = bool(remaining or logged)
    out["basis"] = ("本期 %s 名单 · 已登记 %d / %d 只 · 买几只登记几只，填错点「改」"
                    % (signal_date, len(logged), len(remaining) + len(logged)))
    if remaining:
        out["cash_check"] = _cash_check(account, planned, "JOURNAL", leftover or [])


def plan(days, fresh, status, ledger, settings, account, mode="MODEL"):
    """mode = 'JOURNAL' (the owner's real/simulated account, from fills) or 'MODEL' (the ¥20,000 shadow book).
    The two never mix: in JOURNAL mode the sell list, holdings and cash are the owner's own, even if partial or empty."""
    today = fresh["today"]
    now = _now()
    is_td = fresh["today_is_trading_day"]
    last_completed = fresh["last_completed_session"]
    ref_day = today if is_td else last_completed
    sigs_done = chain_signals(days, upto=last_completed or today)
    cur_sig = sigs_done[-1] if sigs_done else None
    per = period_of(days, cur_sig) if cur_sig else {}
    all_sigs = chain_signals(days)
    future = [s for s in all_sigs if s >= today]
    source = "JOURNAL" if mode == "JOURNAL" else "MODEL"
    out = {"mode": source, "phase": "NO_POSITION", "headline": "", "sub": "", "steps": [], "sell_list": [], "buy_list": [], "cash_check": None, "warnings": [],
           "key_dates": {"signal_date": cur_sig, "entry": per.get("entry"), "exit_date": per.get("exit_date"), "next_signal": per.get("next_signal") or (future[0] if future else None),
                         "next_entry": per.get("next_entry")},
           "sessions_held": None, "sessions_left": None, "sessions_total": HOLD, "today_action": "UNKNOWN", "basis": None}
    if not cur_sig:
        out.update({"headline": "还没有第一期名单", "sub": "第一个信号日 %s 收盘后更新数据即出名单。" % (future[0] if future else "—")})
        return out

    entry, exit_d = per.get("entry"), per.get("exit_date")
    i_ref, i_e, i_x = _idx(days, ref_day), _idx(days, entry), _idx(days, exit_d)
    if None not in (i_ref, i_e):
        out["sessions_held"] = max(0, min(i_ref - i_e, HOLD))
    if None not in (i_ref, i_x):
        out["sessions_left"] = max(0, i_x - i_ref)

    positions = account["positions"] if source == "JOURNAL" else _model_positions(ledger, cur_sig, days)
    have_pos = len(positions) > 0
    list_today = (SIGNALS / ("SHORTLIST_SHADOW_%s.json" % today)).is_file()
    stale_warn = "数据截至 %s，落后 %d 个交易日。名单不受影响，但持仓市值不是最新的。" % (fresh["asof_session"], fresh["stale_sessions"])
    if fresh.get("asof_bogus"):
        stale_warn = "上次更新把截止日期标签写成了 %s（日历被截断），不是行情回到 2007。K 线还在。点一次更新会用本地数据重算，不要连点。" % fresh.get("asof_session")
    n_model_names = len(_model_positions(ledger, cur_sig, days))
    partial_note = None
    if source == "JOURNAL" and have_pos and n_model_names and len(positions) < n_model_names:
        partial_note = "你只买了名单中的 %d/%d 只；系统只按你实际持有的算，卖出日也只让你卖这 %d 只。" % (len(positions), n_model_names, len(positions))

    # --- today is a chain signal day (== exit day of the current period, or the very first signal)
    if today in all_sigs and is_td:
        prev_positions = positions if cur_sig != today else (account["positions"] if source == "JOURNAL" else _model_positions(ledger, sigs_done[-2], days) if len(sigs_done) > 1 else [])
        if source == "JOURNAL" and not prev_positions and now.hour < DATA_READY_HOUR and not list_today:
            # nothing to sell for this account: today is only "wait for tonight's list"
            tp = period_of(days, today)
            out.update({"phase": "SIGNAL_TONIGHT", "today_action": "UPDATE", "headline": "今天不用卖（你没有持仓）· 今晚出新名单",
                        "sub": "今天是信号日。收盘后 18:30 以后点「更新数据」，名单出来后明天 %s 开盘买入。" % tp.get("entry"),
                        "steps": [{"when": "18:30 后", "text": "点「更新数据」"}, {"when": "跑完", "text": "刷新本页看买入名单和资金检查"}, {"when": "%s 开盘" % tp.get("entry"), "text": "买入名单，回来登记"}]})
            out["key_dates"].update({"signal_date": today, "entry": tp.get("entry"), "exit_date": tp.get("exit_date"), "next_signal": tp.get("next_signal"), "next_entry": tp.get("next_entry")})
            if account["cash"] <= 0:
                out["warnings"].append("你的账户现金为 0：先「入金」登记本金，明天的买入手数才算得出来。")
            return out
        out["key_dates"]["signal_date"] = today
        tp = period_of(days, today)
        out["key_dates"].update({"entry": tp.get("entry"), "exit_date": tp.get("exit_date"), "next_signal": tp.get("next_signal"), "next_entry": tp.get("next_entry")})
        out["sessions_held"], out["sessions_left"] = (HOLD, 0) if prev_positions else (None, None)
        contrib = float(settings.get("monthly_contrib") or 0)
        if source == "JOURNAL" and contrib > 0 and not _contrib_logged(account, today[:7]):
            out["warnings"].append("本月定投 ¥%.0f 还没登记入金（合同：每月第一个信号日先入金再买）。" % contrib)
        if list_today:
            out["phase"] = "LIST_READY_BUY_TOMORROW"
            out["today_action"] = "BUY"
            rows, planned, unit, basis = _buy_list(today, settings, account["cash"], source)
            out["buy_list"], out["basis"] = rows, basis
            out["headline"] = "今晚名单已出：明天 %s 开盘买入 %d 只" % (tp.get("entry"), len(rows))
            had_prev = bool(prev_positions) or source == "MODEL"
            out["sub"] = ("今天开盘应已卖出上一期持仓。" if had_prev else "") + "明早 09:15–09:25 集合竞价或 09:30 开盘按下表下单，然后回来登记成交。"
            out["steps"] = ([{"when": "今天已做", "text": "开盘卖出上一期持仓（没登记的请登记卖出）"}] if had_prev else []) + [
                            {"when": "%s 开盘" % tp.get("entry"), "text": "买入下表 %d 只，手数按表；开盘价与昨收差太多时手数=floor(单位/(100×开盘价))" % len(rows)},
                            {"when": "买完", "text": "回到本页逐只「登记买入」（手数、成交价）"}]
            out["cash_check"] = _cash_check(account, planned, source, prev_positions if source == "JOURNAL" else [])
            if source == "JOURNAL" and prev_positions:
                out["warnings"].append("你的成交日志里还有 %d 只上一期持仓没登记卖出。先卖后买，卖出后现金当天可用。" % len(prev_positions))
            if source == "JOURNAL" and account["cash"] <= 0:
                out["warnings"].append("你的账户现金为 0，名单算不出手数：先「入金」登记本金。")
        elif now.hour < DATA_READY_HOUR:
            out["phase"] = "SELL_TODAY"
            out["today_action"] = "SELL"
            out["sell_list"] = [dict(p, side="SELL") for p in prev_positions]
            out["headline"] = "今天开盘：卖出%s %d 只" % ("你持有的" if source == "JOURNAL" else "全部", len(prev_positions))
            out["sub"] = "持有期满。09:30 开盘按市价/对手价全部卖出；跌停或停牌卖不掉的明天再卖（最多顺延 10 个交易日）。今晚 18:30 后更新数据出新名单。"
            if partial_note:
                out["warnings"].append(partial_note)
            out["steps"] = [{"when": "09:30 开盘", "text": "卖出下表全部持仓"},
                            {"when": "卖完", "text": "回到本页逐只「登记卖出」"},
                            {"when": "18:30 后", "text": "点「更新数据」→ 出新名单 → 明早开盘买入"}]
        else:
            out["phase"] = "SIGNAL_TONIGHT"
            out["today_action"] = "UPDATE"
            out["sell_list"] = [dict(p, side="SELL") for p in prev_positions]
            out["headline"] = "今天是信号日：先更新数据，名单才会出来"
            out["sub"] = "收盘数据 18:00 后已齐。点右上「更新数据」（约 35 分钟），完成后本页会显示明早要买的名单。"
            out["steps"] = [{"when": "现在", "text": "点「更新数据」"}, {"when": "跑完", "text": "刷新本页看名单和资金检查"}, {"when": "明早开盘", "text": "买入名单"}]
            if prev_positions:
                out["warnings"].append("今天开盘应已卖出上一期 %d 只；没登记的请先登记卖出。" % len(prev_positions))
        if fresh["needs_update"] and out["phase"] != "SIGNAL_TONIGHT":
            out["warnings"].append(stale_warn)
        return out

    # --- entry day
    if today == entry and is_td:
        out["phase"] = "BUY_TODAY"
        out["today_action"] = "BUY"
        rows, planned, unit, basis = _buy_list(cur_sig, settings, account["cash"], source)
        out["buy_list"], out["basis"] = rows, basis
        out["headline"] = "今天开盘：买入 %d 只" % len(rows)
        out["sub"] = "09:15–09:25 集合竞价或 09:30 开盘按下表下单；每只手数以表为准，开盘价偏离昨收太多时手数=floor(单位/(100×开盘价))。买完回来登记。"
        out["steps"] = [{"when": "09:30 开盘", "text": "买入下表 %d 只" % len(rows)}, {"when": "买完", "text": "逐只「登记买入」"},
                        {"when": "%s 开盘" % exit_d, "text": "卖出全部（系统到那天会提示）"}]
        leftover = [p for p in (account["positions"] if source == "JOURNAL" else []) if (p.get("buy_date") or "") < (entry or "")]
        out["cash_check"] = _cash_check(account, planned, source, leftover)
        if leftover:
            out["warnings"].append("日志里还有 %d 只上一期持仓未登记卖出；先卖后买。" % len(leftover))
        _attach_period_list(out, cur_sig, settings, account, source, False, None, leftover)
        if source == "JOURNAL" and account["cash"] <= 0:
            out["warnings"].append("你的账户现金为 0，名单算不出手数：先「入金」登记本金。")
        if source == "JOURNAL" and float(settings.get("monthly_contrib") or 0) > 0 and not _contrib_logged(account, (cur_sig or today)[:7]):
            out["warnings"].append("本月定投 ¥%.0f 还没登记入金（合同：每月第一个信号日先入金再买）。" % float(settings["monthly_contrib"]))
        if fresh["needs_update"]:
            out["warnings"].append(stale_warn)
        return out

    # --- ordinary hold day (or weekend / holiday), account has positions (model always does once the entry has passed)
    in_period = bool(entry and last_completed and entry <= last_completed)
    if have_pos and in_period:
        out["phase"] = "HOLD"
        out["today_action"] = "HOLD"
        held, left = out["sessions_held"], out["sessions_left"]
        out["headline"] = "今天无需操作" if is_td else "今天休市，无需操作"
        who = "你持有的 %d 只" % len(positions) if source == "JOURNAL" else "全部"
        out["sub"] = "持有第 %s/%d 个交易日 · %s 开盘卖出%s · 当晚更新数据出新名单 · %s 开盘买入" % (held if held is not None else "—", HOLD, exit_d, who, per.get("next_entry"))
        out["steps"] = [{"when": "平时", "text": "什么都不用做；想看市值就 18:30 后点一次「更新数据」"},
                        {"when": "%s 开盘" % exit_d, "text": "卖出%s（%s 个交易日后）" % (who, left if left is not None else "—")},
                        {"when": "%s 晚" % exit_d, "text": "更新数据 → 新名单"}, {"when": "%s 开盘" % per.get("next_entry"), "text": "买入新名单"}]
        if partial_note:
            out["warnings"].append(partial_note)
        _attach_period_list(out, cur_sig, settings, account, source, True, fresh.get("asof_session"))
        if source == "JOURNAL" and out.get("buy_list"):
            out["steps"] = [{"when": "现在", "text": "还可继续登记下表剩下的 %d 只（填错点持仓「改」）" % len(out["buy_list"])}] + out["steps"]
        if fresh["needs_update"]:
            out["warnings"].append(stale_warn)
        return out

    # --- JOURNAL mode, period running but the owner holds nothing: do not tell them to join mid-period
    if source == "JOURNAL" and in_period:
        held, left = out["sessions_held"], out["sessions_left"]
        out["phase"] = "NO_POSITION"
        out["today_action"] = "WAIT"
        out["headline"] = "你还没有持仓 · 本期第 %s/%d 天" % (held if held is not None else "—", HOLD)
        out["sub"] = ("本期名单 %s 收盘出，正式买入日 %s 已过。两个选择：A. 等下一期——%s 晚更新数据出新名单，%s 开盘买入（合同路径）；"
                      "B. 现在按下面本期名单跟买，%s 开盘和大家一起卖——这是中途进场，历史上没测过，好坏未知，由你决定。"
                      % (cur_sig, entry, exit_d, per.get("next_entry"), exit_d))
        out["steps"] = [{"when": "现在", "text": "先「入金」登记模拟盘本金（现在 ¥%.0f）" % account["cash"] if account["cash"] <= 0 else "本金已登记 ¥%.0f" % account["cash"]},
                        {"when": "选 A", "text": "%s 晚 18:30 后「更新数据」→ 新名单 → %s 开盘买 → 回来登记" % (exit_d, per.get("next_entry"))},
                        {"when": "选 B", "text": "按下表任意几只在下一个开盘买入 → 回来「登记买入」→ 页面立刻切到持有状态，%s 提示卖出" % exit_d}]
        out["mid_entry_option"] = True
        _attach_period_list(out, cur_sig, settings, account, "JOURNAL", True, fresh.get("asof_session"))
        if out.get("basis"):
            out["basis"] = out["basis"] + " · 中途跟买（未检验）"
        if account["n_events"] == 0:
            out["warnings"].append("成交日志为空。若你其实已在模拟盘买了本期名单，请「登记买入」（日期填实际成交日），页面会立刻切到持有状态。")
        return out

    out["phase"] = "NO_POSITION"
    out["headline"] = "本期还没有开仓"
    out["sub"] = "名单 %s 已出，买入日 %s。" % (cur_sig, entry)
    return out


def _contrib_logged(account, month):
    return month in (account.get("deposit_months") or [])


def _cash_check(account, planned, source, leftover_positions):
    cash = account["cash"] if source == "JOURNAL" else None
    proceeds = 0.0
    for p in leftover_positions or []:
        if p.get("market_value"):
            proceeds += p["market_value"]
    if cash is None:
        return {"source": "MODEL", "cash_available": None, "reserve": FEE_RESERVE, "budget": None, "planned_yuan": planned, "ok": None,
                "shortfall": None, "note": "没有成交日志：按官方 ¥20,000 影子账本的手数。登记入金后会按你的现金重算。"}
    budget = cash - FEE_RESERVE
    ok = planned is not None and planned <= budget + 1e-6
    return {"source": "JOURNAL", "cash_available": round(cash, 2), "reserve": FEE_RESERVE, "budget": round(budget, 2), "planned_yuan": planned,
            "ok": ok, "shortfall": round(max(0.0, (planned or 0) - budget), 2), "pending_sell_value": round(proceeds, 2) if proceeds else 0.0,
            "note": "预留 ¥200 佣金；名单手数已按可用现金算，不够就少买，不会建议卖别的换这只。"}


# ----------------------------------------------------------------------------- entry point
def ops():
    days = _days()
    status = _load(STATUS, {}) or {}
    ledger = _ledger()
    settings = ps.load_settings()
    journal = load_journal()
    account = derive_account(journal, days)
    run = run_status()
    # Scanning 5k bar tails while daily.py is reading the same files makes this page hang.
    fresh = freshness(days, status, with_gap=not bool(run.get("running")))
    plans = {"actual": plan(days, fresh, status, ledger, settings, account, mode="JOURNAL"),
             "model": plan(days, fresh, status, ledger, settings, account, mode="MODEL")}
    for pl in plans.values():
        if run["running"]:
            pl["warnings"].insert(0, "数据正在更新（%s）。右上角可「停止更新」。跑完后刷新本页。" % (run.get("stage") or "运行中"))
        if run.get("stopped") and not run["running"]:
            pl["warnings"].append("上一次更新是手动停止的。已下好的日线留着，再点会从漏的地方继续。")
        elif run.get("last_failed") and not run["running"]:
            pl["warnings"].append("上一次更新没有正常结束（%s）。再点一次「更新数据」会从缺的地方继续。" % (run["last_failed"].get("started_at") or ""))
    pl = plans["model"]
    model_pos = _model_positions(ledger, pl["key_dates"].get("signal_date"), days) if pl["key_dates"].get("signal_date") else []
    top20 = ledger.get("summary") or status.get("ledger_top20") or {}
    hist_model = history(days, ledger)
    return {"freshness": fresh, "run": run,
            # `plan` kept for backward compatibility = the owner's own account plan
            "plan": plans["actual"], "plans": plans, "account": account, "model_positions": model_pos,
            "model_summary": _model_summary_live(top20, model_pos),
            "history": hist_model, "history_model": hist_model,
            "history_actual": history_actual(days, journal, fresh["last_completed_session"] or fresh["today"]),
            "journal_events": list(reversed(journal.get("events") or []))[:50], "settings": settings,
            "faq": FAQ, "orders_sent": False}


FAQ = [
    {"q": "系统什么时候让我卖？", "a": "只有卖出日（买入后第 20 个交易日）开盘卖全部。中间每天都是「无需操作」。没有加仓、做 T、止损——这些在研究期都测过，更差（V33/V34）。"},
    {"q": "明天再算会不会换一批票？", "a": "不会。名单只在信号日（每 21 个交易日一次）生成，平时运行只补数据。"},
    {"q": "几点更新数据？截止日期是哪一天？", "a": "截止日期永远是「最近一个已经收盘的交易日」，不是墙上的日历、也不会用未来。周末/节假日自动回跳到上一开盘日（周六 9 月 6 日 → 周五 9 月 4 日）。当天开市但 18:00 前点，也还是上一交易日。当天开市且 18:00 后点，截止日期才是今天。"},
    {"q": "已经更新过 / 漏了几只怎么办？怎么停止？", "a": "点更新立刻后台开始，页面上方出一条说明 3 秒后自己消失，不挡操作、没有浏览器弹窗。已经到截止日期且日线没有缺口：提示「没有新任务」。有缺口会写补漏只数。跑的时候右上角变成「停止更新」；停掉后已下好的日线留着，下次从漏的地方续。"},
    {"q": "隔几天没更新，会补齐吗？", "a": "会。一次运行补齐冻结末日到截止日期之间所有缺的交易日；已经有的票会跳过。"},
    {"q": "新闻、财报要更新吗？", "a": "ML1 只用价格、融资、股东户数、指数成分、年报，全部在同一次「更新数据」里自动增量；新闻不是特征。季报/预告/增减持/质押是 ML7 影子的输入，也一起更新。"},
    {"q": "每次计算要花钱吗？", "a": "不用。BaoStock、东方财富数据中心、中登（经东财）全免费。Databento 只花在期货研究上。"},
    {"q": "出名单前看余额吗？", "a": "看。登记入金/成交后，买入手数按你的可用现金 − ¥200 重算；不够就少买几手/几只，不会建议卖别的换这只。"},
    {"q": "买卖后要做什么？", "a": "回来「登记成交」，买几只登记几只。「我的模拟账户」只按你登记的算：没登记 = 空仓，系统不会假设你买了。"},
    {"q": "可以只买名单里的几只吗？", "a": "可以。名单是 10 只等金额，你买 3 只就登记 3 只；卖出日系统只让你卖这 3 只，历史每一期也按你实际的 3 只算。「模型影子账本」永远假设全买，两边互不影响。"},
    {"q": "我的模拟账户 vs 模型影子账本？", "a": "影子账本 = 官方 V26.8 合同（¥20,000 起、每期全买、每月定投 ¥2,000），假设名单全部按次日开盘成交；我的模拟账户 = 你登记的入金和成交（买几只算几只、你填的价和手续费）。两边手数/成本本来就可以不同，对不上不是算错。收盘价两边都读同一份日线最后一行，打开页面就更新，不必再跑 daily.py。"},
    {"q": "只有月初才能买吗？现在中途能进场吗？", "a": "跟月份无关：每 21 个交易日一期，信号日收盘出名单、次日开盘买、第 20 个交易日开盘卖。合同路径是等下一买入日。你空仓时页面同时给出本期名单作为选项 B：现在跟买、卖出日不变——这是中途进场，历史上没测过，好坏未知，买不买你定。登记一只后名单还在：已登记的标「已登记·改」，剩下的继续点「已买，登记」。"},
    {"q": "登记填错了怎么办？", "a": "持仓行或操作日志点「改」，改手数/价格/日期后保存（手续费空着会按新金额重估）。也可以「删」掉重登。改的是你的成交日志，不动模型影子账本。"},
    {"q": "这套东西能保证赚钱吗？", "a": "不能。历史三段账本为正（研究 +551%、验证 +39%、最终 OOS +71%），2017/2018 各 −30%；近 6 个月为负。它是一个有纪律的练手外壳，不是承诺。"},
]
