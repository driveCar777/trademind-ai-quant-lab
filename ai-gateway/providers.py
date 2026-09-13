"""Remote model catalog for the AI Gateway.

Page may only pick ids from list_models(). DeepSeek is chat-completions.
Cursor GET /v1/models is listed for the dropdown; Cursor's HTTP API is an Agent
API, not a chat completion — those ids stay unavailable for /chat.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
LOCAL_ID = "local:qwen2.5-14b-instruct"
LOCAL_LABEL = "Qwen2.5-14B-Instruct"

DEEPSEEK_OFFICIAL = (
    ("deepseek-chat", "DeepSeek Chat"),
    ("deepseek-reasoner", "DeepSeek Reasoner"),
)
CURSOR_FALLBACK = (
    ("auto-smart", "Cursor Auto"),
    ("composer-2.5", "Composer 2.5"),
    ("composer-2", "Composer 2"),
    ("grok-4.5", "Grok 4.5"),
    ("claude-4.6-sonnet-thinking", "Claude 4.6 Sonnet Thinking"),
)
_CACHE_SEC = 60.0
_ds_cache: Tuple[float, Optional[List[Dict[str, Any]]]] = (0.0, None)
_cu_cache: Tuple[float, Optional[List[Dict[str, Any]]]] = (0.0, None)


def _read_dotenv() -> None:
    path = ROOT / ".env"
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k.startswith("TRADEMIND_") and k not in os.environ and v:
            os.environ[k] = v


_read_dotenv()


def deepseek_key() -> str:
    return (os.environ.get("TRADEMIND_DEEPSEEK_API_KEY") or "").strip()


def cursor_key() -> str:
    return (os.environ.get("TRADEMIND_CURSOR_API_KEY") or "").strip()


def _get_json(url: str, key: str, timeout: float = 8.0) -> Any:
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + key, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _row(mid: str, provider: str, label: str, available: bool, reason: str = "") -> Dict[str, Any]:
    return {"id": mid, "provider": provider, "label": label, "name": label, "available": available, "reason": reason}


def _deepseek_rows() -> List[Dict[str, Any]]:
    global _ds_cache
    now = time.time()
    if _ds_cache[1] is not None and now - _ds_cache[0] < _CACHE_SEC:
        return [dict(r) for r in _ds_cache[1]]
    key = deepseek_key()
    reason = "" if key else "未配置 TRADEMIND_DEEPSEEK_API_KEY"
    names: List[Tuple[str, str]] = list(DEEPSEEK_OFFICIAL)
    if key:
        try:
            data = _get_json("https://api.deepseek.com/models", key)
            items = data.get("data") if isinstance(data, dict) else None
            fetched = []
            for it in items or []:
                mid = (it or {}).get("id")
                if mid:
                    fetched.append((mid, mid))
            if fetched:
                names = fetched
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            reason = reason or "DeepSeek 目录暂时拉不到，用官方两只"
    rows = [_row("deepseek:" + api, "deepseek", label, bool(key), reason) for api, label in names]
    _ds_cache = (now, rows)
    return [dict(r) for r in rows]


def _cursor_rows() -> List[Dict[str, Any]]:
    global _cu_cache
    now = time.time()
    if _cu_cache[1] is not None and now - _cu_cache[0] < _CACHE_SEC:
        return [dict(r) for r in _cu_cache[1]]
    key = cursor_key()
    reason = "Cursor 的 API 是编程 Agent，不是聊天补全。问数字请用本机或 DeepSeek。"
    if not key:
        reason = "未配置 TRADEMIND_CURSOR_API_KEY。" + reason
    names: List[Tuple[str, str]] = list(CURSOR_FALLBACK)
    if key:
        try:
            data = _get_json("https://api.cursor.com/v1/models", key)
            items = data.get("items") or data.get("data") or []
            fetched = []
            for it in items:
                mid = (it or {}).get("id")
                if not mid:
                    continue
                fetched.append((mid, (it or {}).get("displayName") or mid))
            if fetched:
                names = fetched
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            pass
    # listed for the dropdown; never available for /chat (Agent API)
    rows = [_row("cursor:" + api, "cursor", label, False, reason) for api, label in names]
    _cu_cache = (now, rows)
    return [dict(r) for r in rows]


def list_models(local_loaded: bool, local_name: str = LOCAL_LABEL) -> List[Dict[str, Any]]:
    local_reason = "" if local_loaded else "本机通义未加载。用桌面 TradeMind-Lab 开，或改选 DeepSeek。"
    out = [_row(LOCAL_ID, "local", local_name, local_loaded, local_reason)]
    out.extend(_deepseek_rows())
    out.extend(_cursor_rows())
    return out


def find_model(model_id: Optional[str], local_loaded: bool, local_name: str = LOCAL_LABEL) -> Optional[Dict[str, Any]]:
    mid = (model_id or "").strip() or LOCAL_ID
    for row in list_models(local_loaded, local_name):
        if row["id"] == mid:
            return row
    return None


def deepseek_chat(api_model: str, messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> Dict[str, Any]:
    key = deepseek_key()
    if not key:
        raise RuntimeError("DEEPSEEK_KEY_MISSING")
    body = json.dumps({"model": api_model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    choice = ((data.get("choices") or [{}])[0].get("message") or {})
    usage = data.get("usage") or {}
    return {
        "text": choice.get("content") or "",
        "tokens_used": int(usage.get("total_tokens") or 0),
        "latency_ms": None,
        "model": api_model,
    }
