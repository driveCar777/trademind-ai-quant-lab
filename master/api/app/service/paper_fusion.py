"""Hot Desk V3 fusion pipeline (:9001 only). Pool = ML1 live output; Layer A = anonymous Grok keep[];
Layer B = web Grok overlay; hard rules truncate whatever Grok says. Paper only. Not a Candidate.

Never imports/changes daily.py, ML1 features, V26.8 shell, or the frozen :9000 journal.
"""
from __future__ import annotations

import csv
import json
import logging
import math
import os
import re
import threading
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.service import cursor_cloud as cc
from app.service import paper_hot as hot
from app.service import paper_ops as po
from app.service import paper_service as ps

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_ROOT))

from research_engine.hot_three_books import anon  # noqa: E402

log = logging.getLogger("app.paper_fusion")

HOT = hot.HOT
LAST_PATH = HOT / "FUSION_LAST.json"
RUN_PATH = HOT / "FUSION_RUN.json"
ANON_LOG = HOT / "FUSION_ANON_LOG.json"
POOL_PATH = HOT / "POOL.json"
HOT_POOL_OWNED_ASOF = "2026-09-14"  # Monday bars on disk; until then shared ML1 read-only
HOT_POOL_PAGE = 40
MAX_POOL_REFRESH_PER_DAY = 2
B2_PATH = hot.B2_PATH
B2_TOTAL_EXPECTED = 29

PROFILE = "HOT_V3_FUSION"
MAX_NAMES = 8
EXT_POOL_N = 30
MAX_PRICE = 100.0
CASH_RESERVE = 200.0
LOOKBACK = anon.LOOKBACK
LAYER_B_TIMEOUT_S = 900.0
LAYER_A_TIMEOUT_S = 900.0

_lock = threading.Lock()
_thread: Optional[threading.Thread] = None

DISCLAIMER = ("融合台 = 纸面实验。不是 Candidate、不是 Level-1、不是收益承诺。联网层无法回测（前视）。"
              "「激进」= 换手更高、费用更高，不是边更大。系统不发单。")


# ----------------------------------------------------------------------------- files
def _dump(path: Path, obj: Any) -> None:
    hot._dump(path, obj)


def _load(path: Path, default: Any) -> Any:
    return hot._load(path, default)


def _save_run(obj: Dict[str, Any]) -> None:
    try:
        _dump(RUN_PATH, obj)
    except OSError as exc:
        log.warning("FUSION_RUN write failed: %s", exc)


def plan_path(asof: str) -> Path:
    return HOT / ("FUSION_PLAN_%s.json" % asof)


# ----------------------------------------------------------------------------- pool (ML1 only)
def _is_main_board(sym: str) -> bool:
    return sym.startswith("sh.60") or sym.startswith("sz.00")


def _latest_shortlist() -> Tuple[Optional[Path], Dict[str, Any]]:
    sigs = po.SIGNALS
    if not sigs.is_dir():
        return None, {}
    cands = sorted(list(sigs.glob("SHORTLIST_20*.json")) + list(sigs.glob("SHORTLIST_SHADOW_*.json")),
                   key=lambda p: re.sub(r"^SHORTLIST_(SHADOW_)?", "", p.stem))
    if not cands:
        return None, {}
    p = cands[-1]
    return p, (_load(p, {}) or {})


def build_pool() -> Dict[str, Any]:
    """ML1 SHORTLIST (V26.8 names) ∪ ML1 SIGNAL top-30 by score (main board, ≤¥100). No new local model."""
    names_map = ps._stock_names()
    sl_path, sl = _latest_shortlist()
    sd = sl.get("signal_date") or (re.sub(r"^SHORTLIST_(SHADOW_)?", "", sl_path.stem) if sl_path else None)
    pool: List[Dict[str, Any]] = []
    seen = set()
    for n in sl.get("names") or []:
        sym = str(n.get("symbol") or "")
        if not sym or sym in seen:
            continue
        seen.add(sym)
        pool.append({"symbol": sym, "name": names_map.get(sym, ""), "source": "SHORTLIST", "rank": n.get("rank"),
                     "score": n.get("score"), "last_close": n.get("last_close")})
    n_short = len(pool)
    sig = {}
    if sd:
        sig = _load(po.SIGNALS / ("SIGNAL_%s.json" % sd), {}) or {}
    rows = [r for r in (sig.get("names") or []) if r.get("symbol") and _is_main_board(str(r["symbol"]))]
    rows.sort(key=lambda r: -(float(r.get("score") or 0.0)))
    for r in rows:
        if len(pool) - n_short >= EXT_POOL_N:
            break
        sym = str(r["symbol"])
        if sym in seen:
            continue
        px = r.get("last_close")
        if px is None or float(px) <= 0 or float(px) > MAX_PRICE:
            continue
        seen.add(sym)
        pool.append({"symbol": sym, "name": names_map.get(sym, ""), "source": "SIGNAL_TOP30", "rank": None,
                     "score": r.get("score"), "last_close": px})
    return {"signal_date": sd, "shortlist_file": sl_path.name if sl_path else None, "n_shortlist": n_short,
            "n_extended": len(pool) - n_short, "n_pool": len(pool), "names": pool,
            "owner": "shared_ml1_readonly", "writes_9000": False, "status": "SHARED_UNTIL_MONDAY"}


REFILL_RULE = ("合适就买 :9001 当前池。不合适则刷新 :9001 的 POOL.json（只写 live/paper_hot，永不写 :9000 SIGNAL/SHORTLIST）。"
               "本场不因刷新再调一次 Grok。持仓不因换池被卖掉。井 = 只读 ML1 SIGNAL。")


def hot_pool_owned(fresh: Optional[Dict[str, Any]] = None) -> bool:
    """Own pool starts when Monday's session is on disk (asof >= 2026-09-14). Holdings stay as they are until then."""
    asof = str((fresh or {}).get("asof_session") or "")
    return bool(asof and asof >= HOT_POOL_OWNED_ASOF)


def ml1_well() -> Dict[str, Any]:
    """Read-only ranked well from the latest ML1 SIGNAL. Never writes live/signals/."""
    names_map = ps._stock_names()
    sl_path, sl = _latest_shortlist()
    sd = sl.get("signal_date") or (re.sub(r"^SHORTLIST_(SHADOW_)?", "", sl_path.stem) if sl_path else None)
    sig: Dict[str, Any] = {}
    sig_name = None
    if sd:
        sig_name = "SIGNAL_%s.json" % sd
        sig = _load(po.SIGNALS / sig_name, {}) or {}
    rows = [r for r in (sig.get("names") or []) if r.get("symbol") and _is_main_board(str(r["symbol"]))]
    rows.sort(key=lambda r: -(float(r.get("score") or 0.0)))
    names: List[Dict[str, Any]] = []
    for r in rows:
        px = r.get("last_close")
        try:
            px_f = float(px or 0)
        except (TypeError, ValueError):
            px_f = 0.0
        if px_f <= 0 or px_f > MAX_PRICE:
            continue
        sym = str(r["symbol"])
        names.append({"symbol": sym, "name": names_map.get(sym, ""), "source": "WELL_SIGNAL",
                      "rank": r.get("rank"), "score": r.get("score"), "last_close": px_f})
    return {"signal_date": sd, "file": sig_name, "n_well": len(names), "names": names, "writes_9000": False}


def _pool_state(default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _load(POOL_PATH, None) or default or {}


def _write_pool_state(state: Dict[str, Any]) -> Dict[str, Any]:
    state = dict(state)
    state["owner"] = "hot_9001"
    state["writes_9000"] = False
    state["candidate"] = False
    _dump(POOL_PATH, state)
    return state


def _names_from_shared() -> List[Dict[str, Any]]:
    return [dict(n, source="HOT_POOL") for n in (build_pool().get("names") or [])]


def ensure_hot_pool_file() -> Dict[str, Any]:
    """Create a :9001-only snapshot if missing. Does not change :9000 files or the journal."""
    cur = _pool_state(None)
    if isinstance(cur, dict) and cur.get("names"):
        return cur
    well = ml1_well()
    names = _names_from_shared()
    state = {
        "status": "WAIT_MONDAY",
        "owner": "hot_9001",
        "writes_9000": False,
        "candidate": False,
        "well_signal_date": well.get("signal_date"),
        "well_file": well.get("file"),
        "n_well": well.get("n_well"),
        "generation": 0,
        "page_n": HOT_POOL_PAGE,
        "consumed": [n["symbol"] for n in names],
        "last_rejected": [],
        "refresh_days": {},
        "names": names,
        "note": "周一 asof>=%s 才用这份池诊股。现在只是热台副本，持仓不动。" % HOT_POOL_OWNED_ASOF,
    }
    return _write_pool_state(state)


def _state_to_pool(state: Dict[str, Any]) -> Dict[str, Any]:
    names = [dict(n, source=n.get("source") or "HOT_POOL") for n in (state.get("names") or [])]
    return {
        "signal_date": state.get("well_signal_date"),
        "shortlist_file": None,
        "n_shortlist": 0,
        "n_extended": 0,
        "n_pool": len(names),
        "names": names,
        "owner": "hot_9001",
        "writes_9000": False,
        "status": state.get("status") or "OWNED",
        "generation": int(state.get("generation") or 0),
        "n_well": state.get("n_well"),
        "n_consumed": len(state.get("consumed") or []),
        "pool_file": "POOL.json",
    }


def owned_pool(fresh: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Promote the Monday snapshot to the live :9001 pool. Same names at first — no forced sells."""
    state = ensure_hot_pool_file()
    well = ml1_well()
    if state.get("status") != "OWNED":
        state["status"] = "OWNED"
        state["well_signal_date"] = well.get("signal_date") or state.get("well_signal_date")
        state["well_file"] = well.get("file") or state.get("well_file")
        state["n_well"] = well.get("n_well")
        state["activated_asof"] = (fresh or {}).get("asof_session")
        state["note"] = "热台自有池。刷新只写 POOL.json。"
        _write_pool_state(state)
    elif well.get("signal_date") and well.get("signal_date") != state.get("well_signal_date"):
        # New :9000 SIGNAL is a new well only. Do not replace names until a refresh.
        state["well_signal_date"] = well.get("signal_date")
        state["well_file"] = well.get("file")
        state["n_well"] = well.get("n_well")
        state["consumed"] = [n["symbol"] for n in (state.get("names") or [])]
        _write_pool_state(state)
    return _state_to_pool(state)


def resolve_pool(fresh: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if hot_pool_owned(fresh):
        return owned_pool(fresh)
    ensure_hot_pool_file()
    return build_pool()


def _next_well_page(well_names: List[Dict[str, Any]], consumed: set, n: int) -> List[Dict[str, Any]]:
    page = []
    for r in well_names:
        if r.get("symbol") in consumed:
            continue
        page.append(dict(r, source="HOT_POOL"))
        if len(page) >= n:
            break
    return page


def refresh_hot_pool(fresh: Optional[Dict[str, Any]] = None, reason: str = "UNSUITABLE") -> Dict[str, Any]:
    """Replace :9001 POOL.json with the next unused well page. Never writes :9000. No second Grok call here."""
    if not hot_pool_owned(fresh):
        return {"status": "WAIT_MONDAY", "refreshed": False, "writes_9000": False}
    today = str((fresh or {}).get("today") or "")
    state = ensure_hot_pool_file()
    days = dict(state.get("refresh_days") or {})
    n_today = int(days.get(today) or 0) if today else 0
    if today and n_today >= MAX_POOL_REFRESH_PER_DAY:
        return {"status": "SKIPPED_REFRESH_BUDGET", "refreshed": False, "n_today": n_today,
                "max_per_day": MAX_POOL_REFRESH_PER_DAY, "writes_9000": False}
    well = ml1_well()
    if well.get("signal_date") and well.get("signal_date") != state.get("well_signal_date"):
        state["consumed"] = [n["symbol"] for n in (state.get("names") or [])]
        state["well_signal_date"] = well.get("signal_date")
        state["well_file"] = well.get("file")
        state["n_well"] = well.get("n_well")
    consumed = set(state.get("consumed") or [])
    rejected = [n["symbol"] for n in (state.get("names") or []) if n.get("symbol")]
    consumed.update(rejected)
    page = _next_well_page(well.get("names") or [], consumed, HOT_POOL_PAGE)
    if not page:
        state["status"] = "WELL_EXHAUSTED"
        _write_pool_state(state)
        return {"status": "WELL_EXHAUSTED", "refreshed": False, "n_remaining": 0, "writes_9000": False}
    old_gen = int(state.get("generation") or 0)
    consumed.update(n["symbol"] for n in page)
    if today:
        days[today] = n_today + 1
        for k in list(days.keys()):
            if k < today:
                days.pop(k, None)
    state.update({
        "status": "OWNED",
        "generation": old_gen + 1,
        "last_rejected": rejected,
        "consumed": sorted(consumed),
        "names": page,
        "refresh_days": days,
        "refreshed_at": po._now().strftime("%Y-%m-%dT%H:%M:%S"),
        "refresh_reason": reason,
        "well_signal_date": well.get("signal_date"),
        "well_file": well.get("file"),
        "n_well": well.get("n_well"),
        "note": "热台自有池已刷新。未写 :9000。",
    })
    _write_pool_state(state)
    return {"status": "REFRESHED", "refreshed": True, "generation": state["generation"],
            "n_new": len(page), "reason": reason, "writes_9000": False,
            "well_signal_date": well.get("signal_date")}


def stamp_pool(pool: Dict[str, Any]) -> Dict[str, Any]:
    """Mark each pool name NEW vs the last written plan's pool. First run / empty last → CURRENT."""
    last = _load(LAST_PATH, None) or {}
    prev_sd = None
    prev = set()
    if isinstance(last, dict):
        prev_sd = (last.get("pool") or {}).get("signal_date")
        for n in last.get("pool_names") or []:
            if isinstance(n, dict) and n.get("symbol"):
                prev.add(n["symbol"])
    names = []
    n_new = n_old = 0
    for n in pool.get("names") or []:
        row = dict(n)
        if not prev:
            row["pool_age"] = "CURRENT"
        elif row.get("symbol") in prev:
            row["pool_age"] = "OLD"
            n_old += 1
        else:
            row["pool_age"] = "NEW"
            n_new += 1
        names.append(row)
    out = dict(pool)
    out["names"] = names
    out["previous_signal_date"] = prev_sd
    out["pool_rotated"] = bool(prev_sd and pool.get("signal_date") and prev_sd != pool.get("signal_date"))
    out["n_new"] = n_new
    out["n_old"] = n_old
    out["refill_rule"] = REFILL_RULE
    return out


def _cash_policy(n_buy: int, n_sell: int) -> str:
    if n_buy + n_sell == 0:
        return "HOLD_CASH"
    if n_buy == 0 and n_sell > 0:
        return "SELL_TO_CASH"
    if n_buy > 0 and n_sell > 0:
        return "ROTATE_IN_POOL"
    return "DEPLOY_IN_POOL"


def _tag_action_sources(rows: List[Dict[str, Any]], kept_by: Dict[str, Any], held_by: Dict[str, Any]) -> None:
    for r in rows:
        k = kept_by.get(r.get("symbol")) or {}
        if k:
            r["name_source"] = k.get("source") or "SHORTLIST"
            r["pool_age"] = k.get("pool_age") or "CURRENT"
        elif r.get("symbol") in held_by:
            r["name_source"] = "HELD"
            r["pool_age"] = "HELD_OUT_OF_POOL"
        else:
            r["name_source"] = "UNKNOWN"
            r["pool_age"] = None


# ----------------------------------------------------------------------------- Layer A (anonymous)
_FROZEN = {"pack": None, "idx": None}


def _frozen_pack():
    """Frozen daily pack (read-only, ends 2026-08-28) — same object Book2 shares. Only used for the price tail;
    no historical evaluation happens here."""
    if _FROZEN["pack"] is None:
        try:
            from research_engine.hot_three_books.assets import load_assets
            pack = load_assets()[0]
            _FROZEN["pack"] = pack
            _FROZEN["idx"] = {s: j for j, s in enumerate(pack["symbols"])}
        except Exception as exc:  # pack missing → live rows only
            log.warning("frozen pack unavailable for price tail: %s", exc)
            _FROZEN["pack"], _FROZEN["idx"] = {}, {}
    return _FROZEN["pack"], _FROZEN["idx"]


def _frozen_tail(symbol: str, asof: Optional[str], lookback: int) -> List[Dict[str, float]]:
    pack, idx = _frozen_pack()
    if not pack or symbol not in idx:
        return []
    j = idx[symbol]
    dates = pack["dates"]
    hi = len(dates)
    if asof:
        while hi > 0 and dates[hi - 1] > asof:
            hi -= 1
    lo = max(0, hi - lookback)
    out = []
    for i in range(lo, hi):
        c = float(pack["close"][i, j])
        if not np.isfinite(c) or c <= 0:
            continue
        out.append({"date": dates[i], "open": float(pack["open"][i, j]), "high": float(pack["high"][i, j]),
                    "low": float(pack["low"][i, j]), "close": c})
    return out


def _read_bars(symbol: str, asof: Optional[str], lookback: int = LOOKBACK) -> List[Dict[str, float]]:
    """Frozen tail (≤ frozen end) + live/bars rows after it, clipped at asof. Last `lookback` bars."""
    out = _frozen_tail(symbol, asof, lookback)
    last = out[-1]["date"] if out else ""
    p = po.BARS / (symbol + ".csv")
    if p.is_file():
        try:
            with open(p, encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
        except OSError:
            rows = []
        for r in rows:
            d = r.get("date") or ""
            if not d or d <= last or (asof and d > asof):
                continue
            try:
                o, h, l, c = float(r.get("open") or 0), float(r.get("high") or 0), float(r.get("low") or 0), float(r.get("close") or 0)
            except ValueError:
                continue
            if c <= 0:
                continue
            out.append({"date": d, "open": o, "high": h, "low": l, "close": c})
    return out[-lookback:]


def live_mini_pack(symbols: List[str], asof: Optional[str]) -> Tuple[Dict[str, Any], List[str]]:
    """Build a pack-like dict from live/bars so anon.pack_window can be reused byte-for-byte."""
    per = {}
    dates = set()
    for s in symbols:
        bars = _read_bars(s, asof)
        if len(bars) >= 20:
            per[s] = bars
            dates.update(b["date"] for b in bars)
    dl = sorted(dates)[-LOOKBACK:]
    syms = [s for s in symbols if s in per]
    n, k = len(dl), len(syms)
    O, H, L, C = (np.full((n, k), np.nan) for _ in range(4))
    di = {d: i for i, d in enumerate(dl)}
    for j, s in enumerate(syms):
        for b in per[s]:
            i = di.get(b["date"])
            if i is None:
                continue
            O[i, j], H[i, j], L[i, j], C[i, j] = b["open"], b["high"], b["low"], b["close"]
    return {"symbols": syms, "dates": dl, "open": O, "high": H, "low": L, "close": C}, syms


def anon_payload(symbols: List[str], asof: Optional[str]) -> Tuple[Dict[str, Any], Dict[str, str], List[str]]:
    pack, syms = live_mini_pack(symbols, asof)
    if not syms:
        return {"series": []}, {}, []
    payload, mapping = anon.pack_window(pack, len(pack["dates"]) - 1, list(range(len(syms))))
    anon.assert_clean(payload)
    return payload, mapping, syms


def _smoke() -> bool:
    return bool(os.environ.get("TRADEMIND_HOT_SMOKE"))


def layer_a_keep(payload: Dict[str, Any], valid_ids: List[str], model_id: str) -> Tuple[List[str], Dict[str, Any]]:
    if _smoke():
        return list(valid_ids), {"status": "SMOKE_STUB", "model": model_id}
    from research_engine.hot_three_books import grok_keep
    try:
        keep = grok_keep.ask_keep(payload, valid_ids, model_id=model_id, timeout_s=LAYER_A_TIMEOUT_S,
                                  name="TradeMind Fusion LayerA Anon")
        return keep, {"status": "OK", "model": model_id}
    except Exception as exc:
        return [], {"status": "GROK_TIMEOUT", "model": model_id, "error": str(exc)[:300]}


# ----------------------------------------------------------------------------- Layer B (web)
def _pending_plans_brief() -> List[Dict[str, Any]]:
    out = []
    try:
        from app.service import paper_fusion_fill as ff
        for pth in ff.plan_files():
            pl = _load(pth, None)
            if isinstance(pl, dict) and not pl.get("settled_at"):
                out.append({"plan_id": pl.get("job_id"), "session": pl.get("session"), "generated_at": pl.get("generated_at"),
                            "fill_date": pl.get("fill_date"),
                            "actions": [{"symbol": a.get("symbol"), "action": a.get("action"), "kind": a.get("kind"), "lots": a.get("lots")}
                                        for a in pl.get("actions") or [] if a.get("action") != "HOLD"]})
    except Exception:
        pass
    return out[-3:]


def resolve_fill_date(fresh: Dict[str, Any], days: Optional[List[str]] = None) -> Optional[str]:
    """Next session we can honestly fill: the next calendar trading day after wall-clock today.
    Owner only updates :9000 in the evening, so this is never 'today's already-printed open'.
    If the local calendar is truncated (no future dates), walk weekdays — holiday miss is OK,
    settle waits until that bar exists."""
    nxt = fresh.get("next_trading_day")
    if nxt:
        return nxt
    today = fresh.get("today") or ""
    future = [d for d in (days or []) if today and d > today]
    if future:
        return future[0]
    if not today:
        return None
    try:
        d = date.fromisoformat(today) + timedelta(days=1)
    except ValueError:
        return None
    for _ in range(10):
        if d.weekday() < 5:
            return d.isoformat()
        d += timedelta(days=1)
    return None


def clocks_block(fresh: Dict[str, Any], fill_date: Optional[str] = None) -> Dict[str, Any]:
    """Split the three clocks so Grok cannot treat T-1 last_close as today's print."""
    asof = fresh.get("asof_session") or ""
    today = fresh.get("today") or ""
    stale_n = int(fresh.get("stale_sessions") or 0)
    local_is_today = bool(asof and today and asof == today)
    return {
        "wall": fresh.get("clock"),
        "today": today,
        "local_asof": asof,
        "local_stale_sessions": stale_n,
        "local_marks_are_today": local_is_today,
        "web": "Grok 可看网上今天的新闻/报价；那不是成交价",
        "fill_date": fill_date or resolve_fill_date(fresh),
        "fill_rule": "下一交易日开盘，等主人晚上点 :9000 更新后才能在 live/bars 里结算；盘中不编价",
        "conflict": "EXPECTED" if (not local_is_today) else "ALIGNED",
        "conflict_note": "本地日线通常是 T-1（主人只在工作日晚上更新）。盯市/名单用本地 asof；Grok 用网上今天；成交用 fill_date 开盘。三套时钟不一致是设计，不是故障。",
    }


def _snapshot(kept: List[Dict[str, Any]], account: Dict[str, Any], fresh: Dict[str, Any], pool: Dict[str, Any],
              layer_a: Dict[str, Any], session: Optional[str] = None) -> Dict[str, Any]:
    fill_date = resolve_fill_date(fresh)
    clocks = clocks_block(fresh, fill_date)
    snap: Dict[str, Any] = {
        "session": session, "session_label": SESSION_LABEL.get(session or "", session), "clock": fresh.get("clock"),
        "clocks": clocks,
        "today": fresh.get("today"), "asof": fresh.get("asof_session"), "fill_date": fill_date,
        "account": {
            "cash": account.get("cash"), "equity": account.get("equity"), "market_value": account.get("market_value"),
            "positions": [{"symbol": p.get("symbol"), "name": p.get("name"), "lots": p.get("lots"),
                           "avg_price": p.get("avg_price"), "mark_price": p.get("mark_price"),
                           "unrealized": p.get("unrealized"), "buy_date": p.get("buy_date"),
                           "sellable_at_fill": p.get("sellable_at_fill")} for p in account.get("positions") or []],
        },
        "layer_a": {"n_in": layer_a.get("n_in"), "n_keep": layer_a.get("n_keep"), "status": layer_a.get("status")},
        "kept_names": [{"symbol": k["symbol"], "name": k.get("name"), "source": k.get("source"),
                        "pool_age": k.get("pool_age"), "ml1_rank": k.get("rank"),
                        "ml1_score": k.get("score"), "last_close": k.get("last_close")} for k in kept],
        "pool_meta": {"signal_date": pool.get("signal_date"), "previous_signal_date": pool.get("previous_signal_date"),
                      "pool_rotated": pool.get("pool_rotated"), "n_shortlist": pool.get("n_shortlist"),
                      "n_extended": pool.get("n_extended"), "n_new": pool.get("n_new"), "n_old": pool.get("n_old"),
                      "owner": pool.get("owner"), "status": pool.get("status"), "generation": pool.get("generation"),
                      "writes_9000": False,
                      "refill_rule": pool.get("refill_rule") or REFILL_RULE},
        "hard_rules": {
            "market": "CN_A_SHARE_MAIN_BOARD_ONLY", "account": "普通账户 T+1，无量化权限，本金约 ¥20k",
            "fill": "next_open", "max_names": MAX_NAMES, "max_price": MAX_PRICE, "lot": po.LOT,
            "commission": "max(¥5, 0.03%)", "stamp_tax_sell": "0.05%", "cash_reserve": CASH_RESERVE,
            "buy_only_from_kept_names": True, "sell_only_held": True,
            "hot_pool_file": "live/paper_hot/POOL.json", "writes_9000": False,
            "refresh_if_unsuitable": True, "no_second_grok_same_session": True,
            "auto_journal_next_open": True,
            "notional_cap": "exposure_pct × equity", "not_a_backtest": True, "not_a_promise": True,
        },
    }
    if session in LIVE_SESSIONS:
        held = [p.get("symbol") for p in account.get("positions") or []]
        snap["universe"] = sorted(set([k["symbol"] for k in kept] + [h for h in held if h]))
        snap["pending_plans"] = _pending_plans_brief()
        snap["hard_rules"]["actions"] = list(SESSION_ACTIONS)
        snap["hard_rules"]["universe"] = ":9001 POOL.json + current holdings only (never invent names; never write :9000)"
        snap["hard_rules"]["refill"] = REFILL_RULE
        snap["hard_rules"]["fill"] = "next_trading_day_open (never today's already-printed open; evening update settles it)"
        snap["hard_rules"]["clocks"] = "local last_close = asof (usually T-1); web = today; fill = fill_date open. Do not treat last_close as today's print."
    return snap


LIVE_SESSIONS = ("open", "lunch", "close")
SESSION_LABEL = {"open": "开盘计划 09:35", "lunch": "午休计划 11:30", "close": "收盘计划 15:05", "daily": "晚间至少看一次 19:30", "settle": "仅结算"}


def session_plan_path(asof: str, session: str) -> Path:
    return HOT / ("FUSION_PLAN_%s_%s.json" % (asof, session))


def layer_b_prompt(snap: Dict[str, Any]) -> str:
    sess = snap.get("session")
    if sess in LIVE_SESSIONS:
        return (
            "你是 :9001 纸面热台的自动执行参谋（%s）。输出会被规则截断后按下一开盘记台账，不是等人批准、不是问句。\n"
            "允许联网：公告、资金流、板块、地缘、宏观。这不是回测，是 2 个月纸面观察。\n"
            "名字来源已定：只能在 snapshot.universe 里的股票（:9001 自有池 POOL.json + 手里的票）上给动作。"
            "不得推荐池外任何代码；池外一律被系统丢弃。卖出后空出的现金也只能买 snapshot.kept_names。"
            "池内合适就买。池内都不合适 → 全部 HOLD；系统会刷新 :9001 池（只写 paper_hot/POOL.json，不写 :9000），本场不再调你第二次。\n"
            "动作枚举：BUY（新买，只能池内）、SELL（清仓，只能持仓且 sellable_at_fill=true）、ADD（持仓加仓，lots_hint 手）、REDUCE（持仓减仓，lots_hint 手）、"
            "REPLACE（卖出持仓 symbol 换入池内 replace_with）、HOLD。默认 HOLD；names 可以为空只给 avoid。\n"
            "每条非 HOLD 必须标 claim_class（hard_event / narrative）和 priced_in（今晚/今早已公开、很可能已进下一开盘的信息 → true；系统会把 priced_in=true 的 BUY 丢弃、SELL 改 HOLD）。\n"
            "时钟分裂（必读）：snapshot.clocks.local_asof 才是本地日线/盯市/名单的日期，通常是 T-1（主人只在工作日晚上更新 :9000）。"
            "last_close 不是今收、不是现价。你看网上的今天新闻/报价可以写进 reason，但成交仍是 snapshot.fill_date 开盘，不要把网上现价当成已经成交。\n"
            "成交假设 = 下一交易日开盘（snapshot.fill_date），今天盘中不成交；已有 snapshot.pending_plans 的动作可以确认或改写（后出的计划覆盖先出的）。\n"
            "一手 = 100 股；最多 %d 只；总名义 ≤ exposure_pct × equity；买入 ≤ 现金 + 卖出净额 − ¥200。\n"
            "每条 reason 写来源类型与时效；写不出来源不要给非 HOLD。只输出一个 JSON 对象，不要前言：\n"
            '{"asof":"YYYY-MM-DD","session":"%s","exposure_pct":0-100,"regime":"一句话市场判断",'
            '"themes":[{"tag":"板块或事件","note":"为何","source":"信息类型"}],'
            '"names":[{"symbol":"sh.600000","name":"","action":"BUY|SELL|ADD|REDUCE|REPLACE|HOLD","replace_with":"sz.000000(仅 REPLACE)","lots_hint":1,"reason":"","tag":"龙头|跟风|防守|回避","source":"资金流|公告|板块|宏观|技术","claim_class":"hard_event|narrative","priced_in":false}],'
            '"avoid":["不要碰的理由"],"confidence":0-100,"disclaimer":"纸面、未回测、不是承诺"}\n'
            "snapshot:\n" % (SESSION_LABEL.get(sess, sess), MAX_NAMES, sess) + json.dumps(snap, ensure_ascii=False)
        )
    return (
        "你是融合台 Layer B 联网参谋。允许联网：资金流、板块、地缘、公告、宏观。这不是回测，是纸面实验。\n"
        "候选只能从 snapshot.kept_names 里挑（它们已经过本地 ML1 打分 + 匿名价格过滤）。不要另推其它股票。\n"
        "SELL 只能针对 snapshot.account.positions 里的持仓；sellable_at_fill=false 的不能 SELL（T+1）。\n"
        "成交假设 = 下一交易日开盘价（snapshot.fill_date）。最多 %d 只 BUY/HOLD。总名义 ≤ exposure_pct × equity。\n"
        "每条 reason 必须写出信息来源类型（资金流/公告/板块/宏观/技术）和时效（几日内）；写不出来源就不要给 BUY。\n"
        "默认 HOLD；names 可以为空、只给 avoid。每条非 HOLD 必须标 claim_class（hard_event=停牌/公司行为/不可成交等硬事件；narrative=板块/资金流/地缘叙事）"
        "和 priced_in（今晚已公开、很可能已进下一开盘的信息 → true；系统会把 priced_in=true 的 BUY/SELL 改成不动）。\n"
        "只输出一个 JSON 对象，不要前言：\n"
        '{"asof":"YYYY-MM-DD","exposure_pct":0-100,"regime":"一句话市场判断",'
        '"themes":[{"tag":"板块或事件","note":"为何热","source":"信息类型"}],'
        '"names":[{"symbol":"sh.600000","name":"","action":"BUY|HOLD|SELL","lots_hint":1,"reason":"","tag":"龙头|跟风|防守|回避","source":"资金流|公告|板块|宏观|技术","claim_class":"hard_event|narrative","priced_in":false}],'
        '"avoid":["不要碰的理由"],"confidence":0-100,"disclaimer":"纸面、未回测、不是承诺"}\n'
        "snapshot:\n" % MAX_NAMES + json.dumps(snap, ensure_ascii=False)
    )


def _smoke_layer_b(snap: Dict[str, Any]) -> Dict[str, Any]:
    kept = snap.get("kept_names") or []
    names = []
    for k in kept[:3]:
        names.append({"symbol": k["symbol"], "name": k.get("name") or "", "action": "BUY", "lots_hint": 1,
                      "reason": "SMOKE_STUB", "tag": "跟风", "source": "技术"})
    for p in (snap.get("account") or {}).get("positions") or []:
        names.append({"symbol": p["symbol"], "name": p.get("name") or "", "action": "SELL", "lots_hint": p.get("lots"),
                      "reason": "SMOKE_STUB sell", "tag": "回避", "source": "技术"})
    if snap.get("session") in LIVE_SESSIONS:
        names.append({"symbol": "sh.999999", "action": "BUY", "lots_hint": 1, "reason": "SMOKE invented ticker (must be dropped)"})
    return {"asof": snap.get("asof"), "exposure_pct": 60, "regime": "SMOKE_STUB", "themes": [{"tag": "冒烟", "note": "stub", "source": "技术"}],
            "names": names, "avoid": [], "confidence": 0, "disclaimer": "smoke"}


def layer_b_call(snap: Dict[str, Any], model_id: str, job_id: str, started: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if _smoke():
        return _smoke_layer_b(snap), {"status": "SMOKE_STUB", "model": model_id}
    catalog, api_id, params = cc.resolve_model(model_id)
    created = cc.create_agent(layer_b_prompt(snap), api_id, params, name="TradeMind Fusion LayerB Web")
    agent = created.get("agent") or created
    run = created.get("run") or {}
    agent_id = agent.get("id") or created.get("id") or ""
    run_id = run.get("id") or agent.get("latestRunId") or created.get("runId") or ""
    meta = {"model": catalog, "agent_id": agent_id, "run_id": run_id}
    try:
        if not agent_id or not run_id:
            raise RuntimeError("Cursor 没有返回 agent/run id")
        _save_run({"running": True, "job_id": job_id, "stage": "Layer B：Grok 联网中", "started_at": started,
                   "agent_id": agent_id, "run_id": run_id, "model": catalog})
        done = cc.wait_run(agent_id, run_id, timeout_s=LAYER_B_TIMEOUT_S)
        meta["duration_ms"] = done.get("durationMs")
        if done.get("status") != "FINISHED":
            if str(done.get("status")) == "TIMEOUT":
                try:
                    cc.cancel_run(agent_id, run_id)
                except Exception:
                    pass
            meta["status"] = "GROK_TIMEOUT" if str(done.get("status")) == "TIMEOUT" else str(done.get("status"))
            meta["error"] = str(done.get("error") or done.get("status"))[:300]
            return {}, meta
        text = done.get("result") or ""
        if isinstance(text, dict):
            text = text.get("text") or text.get("result") or json.dumps(text, ensure_ascii=False)
        brief = hot._parse_brief(str(text))
        meta["status"] = "OK" if brief and not brief.get("parse_error") else "PARSE_ERROR"
        return brief, meta
    finally:
        if agent_id:
            cc.archive_agent(agent_id)


# ----------------------------------------------------------------------------- hard rules
def _norm_sym(sym: Any) -> str:
    s = str(sym or "").strip()
    if not s:
        return ""
    if "." not in s:
        s = ("sh." if s.startswith("6") else "sz.") + s
    return s.lower()


def _claim_class(v: Any) -> str:
    s = str(v or "").strip().lower()
    if s in ("hard_event", "hard", "event", "硬事件"):
        return "hard_event"
    if s in ("narrative", "story", "叙事"):
        return "narrative"
    return "unspecified"


def _truthy(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return str(v or "").strip().lower() in ("1", "true", "yes", "y", "是")


def prompt_hash() -> str:
    """Version stamp for the two prompts: any prompt change = new series (consult item iv-12)."""
    import hashlib
    txt = anon.PROMPT + "\n---\n" + layer_b_prompt({"__template__": True})
    return hashlib.sha1(txt.encode("utf-8")).hexdigest()[:12]


SESSION_ACTIONS = ("BUY", "SELL", "HOLD", "ADD", "REDUCE", "REPLACE")


def _expand_actions(names: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """ADD → BUY(kind=ADD, must be held); REDUCE → SELL(kind=REDUCE, partial lots);
    REPLACE{symbol=old, replace_with=new} → SELL old (REPLACE_OUT) + BUY new (REPLACE_IN). T_BUY/T_SELL aliases kept."""
    out: List[Dict[str, Any]] = []
    for n in names or []:
        act = str(n.get("action") or "HOLD").upper()
        if act == "T_BUY":
            act = "BUY"
        if act == "T_SELL":
            act = "SELL"
        if act == "ADD":
            out.append(dict(n, action="BUY", kind="ADD"))
        elif act == "REDUCE":
            out.append(dict(n, action="SELL", kind="REDUCE"))
        elif act == "REPLACE":
            new = n.get("replace_with") or n.get("with") or ""
            out.append(dict(n, action="SELL", kind="REPLACE_OUT", replace_with=new))
            if new:
                out.append({"symbol": new, "name": n.get("replace_with_name") or "", "action": "BUY", "kind": "REPLACE_IN",
                            "lots_hint": n.get("lots_hint"), "reason": n.get("reason"), "tag": n.get("tag"), "source": n.get("source"),
                            "claim_class": n.get("claim_class"), "priced_in": n.get("priced_in"), "replaces": n.get("symbol")})
        else:
            out.append(dict(n, action=act, kind=act if act in ("BUY", "SELL", "HOLD") else "BAD"))
    return out


def enforce(brief: Dict[str, Any], kept: List[Dict[str, Any]], account: Dict[str, Any], fill_date: Optional[str],
            layer_b_status: str) -> Dict[str, Any]:
    """Truncate Grok's output to the hard rules. Deterministic; unit-tested in smoke 25.
    Universe = kept (ML1 pool) ∪ holdings; anything else is OUT_OF_UNIVERSE."""
    kept_by = {k["symbol"]: k for k in kept}
    held_by = {p["symbol"]: p for p in account.get("positions") or []}
    equity = float(account.get("equity") or 0.0)
    cash = float(account.get("cash") or 0.0)
    expo = brief.get("exposure_pct")
    try:
        expo = max(0, min(100, int(round(float(expo))))) if expo is not None else 0
    except (TypeError, ValueError):
        expo = 0
    if layer_b_status != "OK":
        expo = 0
    cap = expo / 100.0 * equity
    actions: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []
    seen = set()
    for n in _expand_actions(brief.get("names") or []):
        sym = _norm_sym(n.get("symbol"))
        act = str(n.get("action") or "HOLD").upper()
        kind = n.get("kind") or act
        row = {"symbol": sym, "name": n.get("name") or (kept_by.get(sym) or held_by.get(sym) or {}).get("name") or "",
               "action": act, "kind": kind, "lots": None, "reason": str(n.get("reason") or "")[:300], "tag": n.get("tag") or "",
               "source": n.get("source") or "", "held": sym in held_by, "in_pool": sym in kept_by,
               "claim_class": _claim_class(n.get("claim_class")), "priced_in": _truthy(n.get("priced_in"))}
        if n.get("replace_with"):
            row["replace_with"] = _norm_sym(n.get("replace_with"))
        if n.get("replaces"):
            row["replaces"] = _norm_sym(n.get("replaces"))
        if not sym or sym in seen:
            dropped.append(dict(row, why="DUP_OR_EMPTY"))
            continue
        seen.add(sym)
        if kind == "BAD" or act not in ("BUY", "HOLD", "SELL"):
            dropped.append(dict(row, why="BAD_ACTION"))
            continue
        if sym not in kept_by and sym not in held_by:
            dropped.append(dict(row, why="OUT_OF_UNIVERSE"))  # Grok cannot invent tickers outside ML1 pool ∪ holdings
            continue
        pos = held_by.get(sym)
        if kind == "ADD" and not pos:
            dropped.append(dict(row, why="ADD_NOT_HELD"))
            continue
        # Consult-adopted rule: if Grok itself says the information is already in the next open, a BUY/SELL on it is
        # buying/selling the news price under our fill assumption → BUY dropped, SELL downgraded to HOLD.
        if row["priced_in"] and act in ("BUY", "SELL"):
            if act == "BUY" or not pos:
                dropped.append(dict(row, why="PRICED_IN_NEXT_OPEN"))
                continue
            row["action"] = "HOLD"
            row["blocked"] = "信息已进下一开盘（Grok 自报 priced_in）：不按新闻价卖"
            row["lots"] = pos.get("lots")
            row["price_ref"] = pos.get("mark_price")
            actions.append(row)
            continue
        if act == "SELL":
            if not pos:
                dropped.append(dict(row, why="SELL_NOT_HELD"))
                continue
            if not pos.get("sellable_at_fill"):
                row["action"] = "HOLD"
                row["blocked"] = "T+1：买入日 %s ≥ 成交日 %s" % (pos.get("buy_date"), fill_date)
                row["lots"] = pos.get("lots")
                actions.append(row)
                continue
            held_lots = int(pos.get("lots") or 0)
            if kind == "REDUCE":
                try:
                    hint = int(n.get("lots_hint") or 0)
                except (TypeError, ValueError):
                    hint = 0
                lots = min(held_lots, hint) if hint > 0 else max(1, held_lots // 2)
                if lots >= held_lots:
                    row["kind"] = "SELL"  # reducing everything is a SELL
                row["lots"] = lots
            else:
                row["lots"] = held_lots
            row["price_ref"] = pos.get("mark_price")
            actions.append(row)
            continue
        if act == "BUY":
            if not _is_main_board(sym):
                dropped.append(dict(row, why="NOT_MAIN_BOARD"))
                continue
            if sym not in kept_by and not (kind == "ADD" and pos):
                dropped.append(dict(row, why="BUY_OUT_OF_POOL"))
                continue
            px = (kept_by.get(sym) or {}).get("last_close") or (pos or {}).get("mark_price")
            try:
                px = float(px or 0)
            except (TypeError, ValueError):
                px = 0.0
            if px <= 0 or px > MAX_PRICE:
                dropped.append(dict(row, why="PRICE_OUT_OF_RANGE"))
                continue
            try:
                lots = int(n.get("lots_hint") or 0)
            except (TypeError, ValueError):
                lots = 0
            if lots <= 0:
                lots = max(1, int(math.floor(2000.0 / (po.LOT * px))))
            row["lots"] = lots
            row["price_ref"] = px
            actions.append(row)
            continue
        # HOLD
        if pos:
            row["lots"] = pos.get("lots")
            row["price_ref"] = pos.get("mark_price")
        elif sym not in kept_by:
            dropped.append(dict(row, why="HOLD_NOT_HELD_NOT_POOL"))
            continue
        actions.append(row)
    # held positions Grok did not mention → HOLD by default (nothing auto-sells)
    for sym, pos in held_by.items():
        if sym not in seen:
            actions.append({"symbol": sym, "name": pos.get("name") or "", "action": "HOLD", "lots": pos.get("lots"),
                            "price_ref": pos.get("mark_price"), "reason": "Grok 未提及，默认持有", "tag": "", "source": "",
                            "held": True, "in_pool": sym in kept_by, "default": True})
    # max names among BUY/HOLD
    keep_rows, n_pos = [], 0
    for r in actions:
        if r["action"] in ("BUY", "HOLD"):
            if n_pos >= MAX_NAMES and r["action"] == "BUY" and r.get("kind") != "ADD":
                dropped.append(dict(r, why="MAX_%d_NAMES" % MAX_NAMES))
                continue
            n_pos += 1
        keep_rows.append(r)
    actions = keep_rows
    # exposure cap: retained notional (HOLD mv + kept part of REDUCE + BUY lots) ≤ cap; buys also ≤ cash + sell proceeds − reserve
    held_notional = 0.0
    sell_proceeds = 0.0
    for r in actions:
        if r["action"] == "HOLD" and r.get("held"):
            mv = (held_by.get(r["symbol"]) or {}).get("market_value") or 0.0
            held_notional += float(mv)
        elif r["action"] == "SELL" and r.get("held"):
            pos = held_by.get(r["symbol"]) or {}
            px_s = float(r.get("price_ref") or 0)
            sold = float(r.get("lots") or 0) * po.LOT * px_s
            keep_part = max(0.0, float(pos.get("lots") or 0) - float(r.get("lots") or 0)) * po.LOT * px_s
            held_notional += keep_part
            sell_proceeds += sold - max(po.COMMISSION_MIN, sold * po.COMMISSION_RATE) - sold * po.STAMP_TAX
    buy_budget_cash = max(0.0, cash + sell_proceeds - CASH_RESERVE)  # settle executes SELL before BUY
    buy_budget_cap = max(0.0, cap - held_notional)
    budget = min(buy_budget_cash, buy_budget_cap)
    planned, est_fees = 0.0, 0.0
    final = []
    for r in actions:
        if r["action"] != "BUY":
            final.append(r)
            continue
        px = float(r.get("price_ref") or 0)
        lots = int(r.get("lots") or 0)
        while lots > 0 and lots * po.LOT * px + max(po.COMMISSION_MIN, lots * po.LOT * px * po.COMMISSION_RATE) > budget - planned:
            lots -= 1
        if lots <= 0:
            dropped.append(dict(r, why="EXPOSURE_CAP_OR_CASH"))
            continue
        amt = lots * po.LOT * px
        fee = max(po.COMMISSION_MIN, amt * po.COMMISSION_RATE)
        planned += amt + fee
        est_fees += fee
        r["lots"] = lots
        r["est_yuan"] = round(amt, 2)
        r["est_fee"] = round(fee, 2)
        final.append(r)
    for r in final:
        if r["action"] == "SELL":
            amt = float(r.get("lots") or 0) * po.LOT * float(r.get("price_ref") or 0)
            r["est_yuan"] = round(amt, 2)
            r["est_fee"] = round(max(po.COMMISSION_MIN, amt * po.COMMISSION_RATE) + amt * po.STAMP_TAX, 2)
            est_fees += r["est_fee"]
    n_buy = sum(1 for r in final if r["action"] == "BUY")
    n_sell = sum(1 for r in final if r["action"] == "SELL")
    n_hold = sum(1 for r in final if r["action"] == "HOLD")
    kinds = {}
    for r in final:
        if r["action"] != "HOLD":
            kinds[r.get("kind") or r["action"]] = kinds.get(r.get("kind") or r["action"], 0) + 1
    n_narr = sum(1 for r in final if r["action"] != "HOLD" and r.get("claim_class") == "narrative")
    n_unspec = sum(1 for r in final if r["action"] != "HOLD" and r.get("claim_class") == "unspecified")
    _tag_action_sources(final, kept_by, held_by)
    policy = _cash_policy(n_buy, n_sell)
    return {
        "audit": {"hold_all": (n_buy + n_sell) == 0, "n_narrative_actions": n_narr, "n_unspecified_actions": n_unspec,
                  "truncation_rate": round(len(dropped) / max(1, len(dropped) + len(final)), 3),
                  "invested_pct_after_plan": round(100.0 * (held_notional + planned) / equity, 1) if equity else None,
                  "exposure_pct_asked": expo, "cash_policy": policy},
        "cash_policy": policy,
        "exposure_pct": expo, "actions": final, "dropped": dropped,
        "budget": {"equity": round(equity, 2), "cash": round(cash, 2), "cap_notional": round(cap, 2),
                   "held_notional": round(held_notional, 2), "sell_proceeds_net": round(sell_proceeds, 2), "buy_budget": round(budget, 2),
                   "planned_buy_notional": round(planned, 2), "est_fees": round(est_fees, 2),
                   "post_plan_notional": round(held_notional + planned, 2),
                   "fee_pct_of_equity": round(est_fees / equity, 5) if equity else None},
        "counts": {"buy": n_buy, "sell": n_sell, "hold": n_hold, "dropped": len(dropped), "kinds": kinds},
    }


# ----------------------------------------------------------------------------- Book2 gate
def book2_status() -> Dict[str, Any]:
    b2 = _load(B2_PATH, None) or {}
    n = int(b2.get("n_periods") or 0)
    total = int(b2.get("total_expected") or B2_TOTAL_EXPECTED)
    complete = bool(b2.get("complete")) or n >= total
    return {"n_periods": n, "total_expected": total, "n_timeout": b2.get("n_timeout") or 0, "complete": complete,
            "twr": b2.get("twr") if complete else None, "candidate": False,
            "note": ("账本2 已读完 %d 期；匿名过滤增量只在对照账里看，仍不是 Candidate。" % n) if complete
            else ("账本2 未读完（%d/%d），匿名过滤增量未知。" % (n, total))}


# ----------------------------------------------------------------------------- account
def _account(fresh: Dict[str, Any], days: List[str]) -> Dict[str, Any]:
    journal = hot.load_journal()
    account = hot.derive_account(journal, days)  # seeded with initial_capital (FUSION_SETTINGS)
    fill = fresh.get("next_trading_day") or ""
    for p in account.get("positions") or []:
        p["sellable_today"] = hot._sellable(p.get("buy_date"), fresh)
        p["sellable_at_fill"] = bool(p.get("buy_date") and fill and p["buy_date"] < fill)
    return account


# ----------------------------------------------------------------------------- pipeline
def run_pipeline(model_id: str = "", job_id: str = "", write: bool = True, session: Optional[str] = None) -> Dict[str, Any]:
    """session=None → legacy two-layer plan. session ∈ LIVE_SESSIONS → named diagnosis overlay: Layer A skipped
    (Book2 fact: anon filter subtracts), universe = ML1 pool ∪ holdings, one Grok call, fill at next trading day open."""
    started = po._now().strftime("%Y-%m-%dT%H:%M:%S")
    job_id = job_id or uuid.uuid4().hex[:10]
    live = session in LIVE_SESSIONS
    if _smoke():
        catalog = model_id or "grok-4.6?effort=xhigh&fast=true"
    else:
        catalog, _api, _params = cc.resolve_model(model_id)
    days = po._days()
    status = po._load(po.STATUS, {}) or {}
    fresh = po.freshness(days, status, with_gap=False)
    asof = fresh.get("asof_session") or fresh.get("last_completed_session") or fresh.get("today")
    fill_date = resolve_fill_date(fresh, days)
    account = _account(fresh, days)
    warnings = [
        DISCLAIMER,
        "A 股普通账户 T+1：今天买的今天不能卖。成交按下一开盘登记，系统不发单。",
        "A 股池与 :9000 分开。热台只写 live/paper_hot/POOL.json。:9000 SIGNAL/SHORTLIST 只读。",
    ]
    _save_run({"running": True, "job_id": job_id, "stage": "组池（:9001 POOL 或周一前只读 ML1）", "started_at": started, "model": catalog, "session": session})
    pool = stamp_pool(resolve_pool(fresh))
    syms = [n["symbol"] for n in pool["names"]]
    if live:
        # Layer A intentionally skipped: Book2 29/29 TWR +3.3% vs Book1 +39.0% → anon filter subtracts. Pool stays whole.
        kept = list(pool["names"])
        layer_a = {"n_in": len(syms), "n_keep": len(syms), "keep_ids": [], "status": "SKIPPED_LIVE_SESSION",
                   "model": None, "error": None, "leak_hits": [], "skipped_no_bars": [], "lookback": LOOKBACK,
                   "note": "账本2 已读完：匿名过滤减分，实时诊股不再用它缩池。"}
        warnings.append("实时诊股不用 Layer A（账本2：匿名过滤 +3.3% vs 账本1 +39.0%，减分）。名字来源 = :9001 池 + 持仓。")
    else:
        # Layer A
        _save_run({"running": True, "job_id": job_id, "stage": "Layer A：匿名 K 线 → Grok keep[]", "started_at": started, "model": catalog})
        payload, mapping, used = anon_payload(syms, asof)
        valid = [s["id"] for s in payload["series"]]
        keep_ids, a_meta = layer_a_keep(payload, valid, catalog) if valid else ([], {"status": "EMPTY_POOL", "model": catalog})
        kept_syms = [mapping[u] for u in keep_ids if u in mapping]
        if a_meta.get("status") != "OK" and a_meta.get("status") != "SMOKE_STUB":
            warnings.append("Layer A 失败（%s）：本次没有匿名过滤，不下 BUY；只对持仓给 HOLD/SELL 判断。" % a_meta.get("status"))
        kept = [n for n in pool["names"] if n["symbol"] in set(kept_syms)]
        layer_a = {"n_in": len(valid), "n_keep": len(keep_ids), "keep_ids": keep_ids, "status": a_meta.get("status"),
                   "model": a_meta.get("model"), "error": a_meta.get("error"), "leak_hits": anon.leak_hits(json.dumps(payload)),
                   "skipped_no_bars": [s for s in syms if s not in used], "lookback": LOOKBACK}
        if write:
            alog = _load(ANON_LOG, None) or {"items": []}
            alog.setdefault("items", []).append({"asof": asof, "job_id": job_id, "sent": payload, "keep": keep_ids, "map": mapping,
                                                 "status": a_meta.get("status")})
            alog["items"] = alog["items"][-60:]
            _dump(ANON_LOG, alog)
    # Layer B
    _save_run({"running": True, "job_id": job_id, "stage": ("%s：Grok 联网诊股（1 次）" % SESSION_LABEL.get(session or "", "")) if live else "Layer B：联网叠加（第 2 次 Grok）",
               "started_at": started, "model": catalog, "session": session})
    snap = _snapshot(kept, account, fresh, pool, layer_a, session=session)
    try:
        brief, b_meta = layer_b_call(snap, catalog, job_id, started)
    except Exception as exc:  # transport / create failure → plan still written, exposure 0
        log.warning("layer B call failed: %s", exc)
        brief, b_meta = {}, {"status": "TRANSPORT_ERROR", "model": catalog, "error": str(exc)[:300]}
    b_status = b_meta.get("status") or "ERROR"
    if b_status not in ("OK", "SMOKE_STUB"):
        warnings.append("Layer B 失败（%s）：exposure 记 0，没有 BUY。" % b_status)
    enforced = enforce(brief or {}, kept, account, fill_date, "OK" if b_status in ("OK", "SMOKE_STUB") else b_status)
    b2 = book2_status()
    warnings.append(b2["note"])
    if enforced["budget"].get("fee_pct_of_equity"):
        warnings.append("本计划估费 ¥%.2f = 权益 %.2f%%。激进 = 费用先走。" % (enforced["budget"]["est_fees"], 100 * enforced["budget"]["fee_pct_of_equity"]))
    policy = enforced.get("cash_policy") or "HOLD_CASH"
    pool_refresh = {"status": "NOT_NEEDED", "refreshed": False, "writes_9000": False}
    if policy == "HOLD_CASH":
        warnings.append("池内没有合适买卖：现金放着。")
    elif policy == "SELL_TO_CASH":
        warnings.append("只卖不买：卖出后现金放着。")
    if write and hot_pool_owned(fresh) and policy in ("HOLD_CASH", "SELL_TO_CASH"):
        pool_refresh = refresh_hot_pool(fresh, reason=policy)
        if pool_refresh.get("refreshed"):
            warnings.append("已刷新 :9001 池 generation %s。下场用新池。未写 :9000。" % pool_refresh.get("generation"))
        elif pool_refresh.get("status") == "WAIT_MONDAY":
            warnings.append("周一新行情（asof>=%s）之前不刷新池。持仓不动。" % HOT_POOL_OWNED_ASOF)
        elif pool_refresh.get("status") == "SKIPPED_REFRESH_BUDGET":
            warnings.append("今天已刷新 %s 次，不再刷。现金继续拿着。" % pool_refresh.get("n_today"))
        elif pool_refresh.get("status") == "WELL_EXHAUSTED":
            warnings.append("只读井已经用完这一份 SIGNAL。等 :9000 写出新 SIGNAL 再刷。现金拿着。")
    if not hot_pool_owned(fresh):
        warnings.append("热台自有池周一 asof>=%s 才启用。现在持仓和读法保持原样。" % HOT_POOL_OWNED_ASOF)
    warnings.append(REFILL_RULE)
    plan = {
        "profile": PROFILE, "candidate": False, "level1": False, "promise": False,
        "session": session, "session_label": SESSION_LABEL.get(session or "", None), "session_date": fresh.get("today"),
        "asof": asof, "fill_date": fill_date, "generated_at": po._now().strftime("%Y-%m-%dT%H:%M:%S"), "job_id": job_id,
        "model": catalog, "pool": {k: v for k, v in pool.items() if k != "names"}, "pool_names": pool["names"],
        "layer_a": layer_a,
        "layer_b": {"status": b_status, "model": b_meta.get("model"), "agent_id": b_meta.get("agent_id"), "run_id": b_meta.get("run_id"),
                    "duration_ms": b_meta.get("duration_ms"), "error": b_meta.get("error"),
                    "raw_exposure_pct": (brief or {}).get("exposure_pct"), "confidence": (brief or {}).get("confidence"),
                    "n_names_raw": len((brief or {}).get("names") or [])},
        "regime": (brief or {}).get("regime") or "", "themes": (brief or {}).get("themes") or [],
        "avoid": (brief or {}).get("avoid") or [],
        "exposure_pct": enforced["exposure_pct"], "actions": enforced["actions"], "dropped": enforced["dropped"],
        "budget": enforced["budget"], "counts": enforced["counts"], "audit": enforced.get("audit"),
        "cash_policy": policy,
        "pool_refresh": pool_refresh,
        "prompt_hash": prompt_hash(), "anon_protocol": anon.PROTOCOL,
        "book2": b2, "warnings": warnings, "disclaimer": DISCLAIMER, "orders_sent": False,
        "t_plus_one": True, "max_names": MAX_NAMES,
    }
    if write and asof:
        if live:
            _dump(session_plan_path(fresh.get("today") or asof, session), plan)
        else:
            _dump(plan_path(asof), plan)
        _dump(LAST_PATH, plan)
    return plan


# ----------------------------------------------------------------------------- thread + status
def _thread_alive() -> bool:
    t = _thread
    return t is not None and t.is_alive()


def run_state() -> Dict[str, Any]:
    cur = _load(RUN_PATH, {}) or {"running": False}
    if cur.get("running") and not _thread_alive() and hot._run_age_s(cur) > 5:
        cur["running"] = False
        cur["stage"] = "失败"
        if not cur.get("error"):
            cur["error"] = "后台线程已退出（写状态文件失败或进程重启）。可以再跑一次融合台。"
        _save_run(cur)
    return cur


def _worker(model_id: str, job_id: str) -> None:
    started = po._now().strftime("%Y-%m-%dT%H:%M:%S")
    try:
        plan = run_pipeline(model_id, job_id, write=True)
        la, lb = plan["layer_a"].get("status"), plan["layer_b"].get("status")
        ok = la in ("OK", "SMOKE_STUB") and lb in ("OK", "SMOKE_STUB")
        run = {"running": False, "job_id": job_id, "stage": "完成" if ok else "完成（有层失败，计划保守：无 BUY）",
               "started_at": started, "model": plan.get("model"),
               "finished_at": po._now().strftime("%Y-%m-%dT%H:%M:%S"), "asof": plan.get("asof"),
               "layer_a": la, "layer_b": lb}
        if not ok:
            run["error"] = "Layer A=%s · Layer B=%s：%s" % (la, lb, (plan["layer_b"].get("error") or plan["layer_a"].get("error") or "")[:200])
        _save_run(run)
    except Exception as exc:
        log.exception("fusion worker failed")
        _save_run({"running": False, "job_id": job_id, "stage": "失败", "started_at": started, "model": model_id,
                   "error": str(exc)[:400]})


def start(model_id: str = "") -> Dict[str, Any]:
    global _thread
    if not _smoke():
        if not cc.key_present():
            raise RuntimeError("没有 Cursor 密钥。应在 D:\\Cursor\\APIKey.txt")
        catalog, _a, _p = cc.resolve_model(model_id)
    else:
        catalog = model_id or "grok-4.6?effort=xhigh&fast=true"
    with _lock:
        cur = run_state()
        if cur.get("running") and _thread_alive():
            return cur
        job_id = uuid.uuid4().hex[:10]
        started = po._now().strftime("%Y-%m-%dT%H:%M:%S")
        t = threading.Thread(target=_worker, args=(catalog, job_id), daemon=True)
        _thread = t
        _save_run({"running": True, "job_id": job_id, "model": catalog, "stage": "已提交", "started_at": started})
        t.start()
    return run_state()


def stop() -> Dict[str, Any]:
    cur = run_state()
    if cur.get("agent_id") and cur.get("run_id") and cur.get("running"):
        try:
            cc.cancel_run(cur["agent_id"], cur["run_id"])
        except Exception as exc:
            cur["error"] = str(exc)[:200]
    cur["running"] = False
    cur["stage"] = "已停止"
    _save_run(cur)
    return cur


def view() -> Dict[str, Any]:
    """GET /api/v1/hot/fusion: last plan + run status + live account (MTM from live/bars) + book2 gate."""
    days = po._days()
    status = po._load(po.STATUS, {}) or {}
    fresh = po.freshness(days, status, with_gap=False)
    account = _account(fresh, days)
    plan = _load(LAST_PATH, None) or None
    if plan:
        held = {p["symbol"]: p for p in account.get("positions") or []}
        for r in plan.get("actions") or []:
            pos = held.get(r.get("symbol"))
            r["held_now"] = bool(pos)
            r["sellable_today"] = bool(pos and pos.get("sellable_today"))
            r["mark_price"] = (pos or {}).get("mark_price") or r.get("price_ref")
        plan["stale"] = bool(plan.get("asof") and fresh.get("asof_session") and plan["asof"] < fresh["asof_session"])
    from app.service import paper_fusion_fill as ff  # lazy: ff imports this module
    try:
        auto_fill = ff.auto_fill_view()
    except Exception as exc:  # never let the audit block break the page
        auto_fill = {"enabled": None, "error": str(exc)[:200]}
    hp = ensure_hot_pool_file()
    return {
        "profile": PROFILE, "candidate": False, "orders_sent": False, "risk": "HIGH",
        "freshness": fresh, "account": account, "plan": plan, "run": run_state(), "book2": book2_status(),
        "auto_fill": auto_fill,
        "hot_pool": {"owned": hot_pool_owned(fresh), "starts_asof": HOT_POOL_OWNED_ASOF,
                     "status": hp.get("status"), "generation": hp.get("generation"), "n": len(hp.get("names") or []),
                     "well_signal_date": hp.get("well_signal_date"), "writes_9000": False,
                     "path": "live/paper_hot/POOL.json"},
        "disclaimer": DISCLAIMER, "max_names": MAX_NAMES, "ext_pool_n": EXT_POOL_N,
        "clocks": clocks_block(fresh, resolve_fill_date(fresh, days)),
        "honesty": [
            "工作日自动诊股、自动纸面记账。不用点「开跑」。",
            ":9001 池与 :9000 分开。周一新行情后无合适就刷新热台池。不是 Candidate。",
        ],
    }
