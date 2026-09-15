"""Read-only data layer for the A-share desktop app.

Everything here is DISPLAY ONLY. It reads the frozen ML1 paper-trading
artifacts (STATUS / SHORTLIST / LEDGER) produced by the existing research
pipeline. It never writes, never fetches the network, never sends orders.
"""
from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def _repo_root() -> Path:
    # ashare-desktop/ashare_desktop/data.py -> repo root is two parents up
    here = Path(__file__).resolve()
    for p in [here.parents[2], here.parents[1], Path.cwd()]:
        if (p / "data" / "market" / "cn_a_share" / "live").exists():
            return p
    return here.parents[2]


def live_dir() -> Path:
    env = os.environ.get("TRADEMIND_ASHARE_LIVE")
    if env:
        return Path(env)
    return _repo_root() / "data" / "market" / "cn_a_share" / "live"


def _load(path: Path) -> Optional[dict]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def _latest(pattern: str) -> Optional[Path]:
    files = sorted(glob.glob(pattern))
    return Path(files[-1]) if files else None


@dataclass
class Name:
    rank: int
    symbol: str
    score: float
    last_close: float
    lots: int
    est_yuan: float


@dataclass
class Snapshot:
    """Everything the UI needs, already parsed and defensive to missing files."""
    asof: str = "—"
    contract: str = "—"
    boards: str = "—"
    equity_shadow: Optional[float] = None
    capital_top20: Optional[float] = None
    exposure: Optional[float] = None
    orders_sent: bool = False
    money: str = "NONE (shadow)"
    next_signal: str = "—"
    ledger_state: str = "—"
    n_periods_open: int = 0
    n_periods_closed: int = 0
    # live pack
    frozen_id: str = "—"
    frozen_hash: str = ""
    frozen_end: str = "—"
    n_symbols: Optional[int] = None
    n_dates: Optional[int] = None
    built_at: str = "—"
    steps: dict = field(default_factory=dict)
    # shortlist
    shortlist_date: str = "—"
    act: str = ""
    est_invested: Optional[float] = None
    n_names: int = 0
    names: list[Name] = field(default_factory=list)
    # ledger periods
    periods: list[dict] = field(default_factory=list)
    ok: bool = False
    source_dir: str = ""


def load_snapshot() -> Snapshot:
    d = live_dir()
    snap = Snapshot(source_dir=str(d))
    status = _load(d / "STATUS.json") or {}
    if status:
        snap.ok = True
        snap.asof = status.get("asof_session", status.get("asof_requested", "—"))
        snap.steps = status.get("steps", {}) or {}
        lp = status.get("live_pack", {}) or {}
        snap.frozen_id = lp.get("frozen_dataset_id", "—")
        snap.frozen_hash = lp.get("frozen_dataset_hash", "")
        snap.frozen_end = lp.get("frozen_end", "—")
        snap.n_symbols = lp.get("n_symbols")
        snap.n_dates = lp.get("n_dates")
        snap.built_at = lp.get("built_at", "—")
        led = status.get("ledger", {}) or {}
        snap.equity_shadow = led.get("equity")
        snap.next_signal = led.get("next_signal_date", "—")
        snap.ledger_state = led.get("state", "—")
        snap.n_periods_open = led.get("n_periods_open", 0)
        snap.n_periods_closed = led.get("n_periods_closed", 0)
        snap.orders_sent = bool(led.get("orders_sent", False))
        snap.money = led.get("money", "NONE (shadow)")
        t20 = status.get("ledger_top20", {}) or {}
        snap.contract = t20.get("contract", "—")
        snap.boards = t20.get("boards", "—")
        snap.capital_top20 = t20.get("capital_yuan")
        snap.exposure = t20.get("exposure")

    sl_path = _latest(str(d / "signals" / "SHORTLIST_2*.json"))
    sl = _load(sl_path) if sl_path else None
    if sl:
        snap.shortlist_date = sl_path.stem.replace("SHORTLIST_", "") if sl_path else "—"
        snap.act = sl.get("act", "")
        snap.est_invested = sl.get("est_invested_yuan")
        snap.n_names = sl.get("n_names", len(sl.get("names", [])))
        if snap.contract == "—":
            snap.contract = sl.get("contract", "—")
        for n in sl.get("names", []):
            snap.names.append(Name(
                rank=int(n.get("rank", 0)),
                symbol=str(n.get("symbol", "")),
                score=float(n.get("score", 0.0)),
                last_close=float(n.get("last_close", 0.0)),
                lots=int(n.get("lots_100_est", 0)),
                est_yuan=float(n.get("est_yuan", 0.0)),
            ))
        snap.names.sort(key=lambda x: x.rank)

    led_top = _load(d / "ledger" / "LEDGER_TOP20.json") or _load(d / "ledger" / "LEDGER.json") or {}
    snap.periods = led_top.get("periods", []) or []
    return snap
