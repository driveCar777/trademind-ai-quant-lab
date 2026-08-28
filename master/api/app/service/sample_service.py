"""Local sample CSV for research presets. Not live market data."""

from __future__ import print_function

import csv
import re
from typing import Any, Dict, List, Optional, Tuple

from app.config.settings import get_settings
from app.service.exceptions import TaskFailedError, WorkerNotFoundError

SAMPLE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
MIN_ROWS = 15
MAX_ROWS = 500
DEFAULT_BY_PRESET = {
    "indicator": "eurusd",
    "factor": "moutai",
    "backtest": "xauusd",
}


def _samples_dir():
    path = get_settings().data_root / "samples"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _csv_path(sample_id: str):
    return _samples_dir() / ("%s.csv" % sample_id)


def normalize_sample_id(sample_id: Optional[str]) -> Optional[str]:
    if sample_id in (None, ""):
        return None
    text = str(sample_id).strip().lower()
    if not SAMPLE_ID_RE.match(text):
        raise WorkerNotFoundError("sample")
    return text


def _read_csv(sample_id: str) -> Tuple[List[str], List[Dict[str, str]]]:
    sid = normalize_sample_id(sample_id)
    if not sid:
        raise WorkerNotFoundError("sample")
    path = _csv_path(sid)
    if not path.is_file():
        raise TaskFailedError("样本文件不存在：%s.csv" % sid)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TaskFailedError("读不了样本：%s" % exc)
    try:
        reader = csv.DictReader(raw.splitlines())
        names = [name.strip() for name in (reader.fieldnames or [])]
        rows = []
        for row in reader:
            if not row:
                continue
            cleaned = {}
            for key, value in row.items():
                if key is None:
                    continue
                cleaned[key.strip()] = (value or "").strip()
            if any(cleaned.values()):
                rows.append(cleaned)
    except csv.Error as exc:
        raise TaskFailedError("样本格式不对：%s" % exc)
    return names, rows


def detect_kind(fieldnames: List[str]) -> Optional[str]:
    names = set(fieldnames or [])
    if "close" in names:
        return "indicator"
    if "stock" in names and "date" in names:
        return "factor"
    if "strategy" in names and "symbol" in names:
        return "backtest"
    return None


def peek_kind(sample_id: str) -> Optional[str]:
    path = _csv_path(sample_id)
    if not path.is_file():
        return None
    try:
        names, _rows = _read_csv(sample_id)
    except (TaskFailedError, WorkerNotFoundError):
        return None
    return detect_kind(names)


def resolve_sample_id(preset: str, sample_id: Optional[str]) -> Optional[str]:
    sid = normalize_sample_id(sample_id)
    if preset not in DEFAULT_BY_PRESET:
        if sid:
            raise WorkerNotFoundError("sample")
        return None
    chosen = sid or DEFAULT_BY_PRESET[preset]
    if not _csv_path(chosen).is_file():
        return chosen
    kind = peek_kind(chosen)
    if kind != preset:
        raise WorkerNotFoundError("sample")
    return chosen


def load_indicator_payload(sample_id: str) -> Dict[str, Any]:
    names, rows = _read_csv(sample_id)
    if detect_kind(names) != "indicator":
        raise TaskFailedError("样本不是指标收盘价")
    closes = []
    symbol = sample_id.upper()
    try:
        for row in rows:
            close_text = row.get("close") or ""
            if not close_text:
                continue
            closes.append(float(close_text))
            if row.get("symbol"):
                symbol = row["symbol"]
    except ValueError as exc:
        raise TaskFailedError("样本格式不对：%s" % exc)
    if len(closes) < MIN_ROWS:
        raise TaskFailedError("样本至少需要 %s 根收盘价" % MIN_ROWS)
    if len(closes) > MAX_ROWS:
        raise TaskFailedError("样本最多 %s 根收盘价" % MAX_ROWS)
    return {"symbol": symbol, "close": closes}


def load_factor_payload(sample_id: str) -> Dict[str, Any]:
    names, rows = _read_csv(sample_id)
    if detect_kind(names) != "factor" or not rows:
        raise TaskFailedError("样本不是因子选股")
    stock = rows[0].get("stock") or ""
    date = rows[0].get("date") or ""
    if not stock or not date:
        raise TaskFailedError("因子样本缺少 stock/date")
    return {"stock": stock, "date": date}


def load_backtest_payload(sample_id: str) -> Dict[str, Any]:
    names, rows = _read_csv(sample_id)
    if detect_kind(names) != "backtest" or not rows:
        raise TaskFailedError("样本不是回测参数")
    strategy = rows[0].get("strategy") or ""
    symbol = rows[0].get("symbol") or ""
    start = rows[0].get("start") or ""
    if not strategy or not symbol or not start:
        raise TaskFailedError("回测样本缺少 strategy/symbol/start")
    return {"strategy": strategy, "symbol": symbol, "start": start}


def load_payload(preset: str, sample_id: str) -> Dict[str, Any]:
    if preset == "indicator":
        return load_indicator_payload(sample_id)
    if preset == "factor":
        return load_factor_payload(sample_id)
    if preset == "backtest":
        return load_backtest_payload(sample_id)
    raise WorkerNotFoundError("sample")


def list_samples() -> List[Dict[str, Any]]:
    items = []
    for path in sorted(_samples_dir().glob("*.csv")):
        sid = path.stem.lower()
        if not SAMPLE_ID_RE.match(sid):
            continue
        kind = peek_kind(sid)
        if kind is None:
            continue
        try:
            payload = load_payload(kind, sid)
        except (TaskFailedError, WorkerNotFoundError):
            continue
        symbol = str(payload.get("symbol") or payload.get("stock") or "")
        rows = len(payload.get("close") or [payload])
        items.append({
            "sample_id": sid,
            "filename": path.name,
            "kind": kind,
            "rows": rows,
            "symbol": symbol,
        })
    return items
