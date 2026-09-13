"""Cursor Cloud Agents API (no-repo). Key never logged."""
from __future__ import annotations

import base64
import json
import os
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode

API = "https://api.cursor.com/v1"
_models_cache: Tuple[float, list] = (0.0, [])
KEY_FILES = (
    Path(os.environ.get("TRADEMIND_CURSOR_API_KEY_FILE") or ""),
    Path(r"D:\Cursor\APIKey.txt"),
    Path(r"C:\Cursor\APIKey.txt"),
)


def load_key() -> str:
    env = (os.environ.get("TRADEMIND_CURSOR_API_KEY") or "").strip()
    if env:
        return env
    for p in KEY_FILES:
        if not p or not str(p) or not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if text:
            return text
    return ""


def key_present() -> bool:
    return bool(load_key())


def _headers(key: str) -> Dict[str, str]:
    basic = base64.b64encode((key + ":").encode("utf-8")).decode("ascii")
    return {
        "Authorization": "Basic " + basic,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _proxy_listen(url: str) -> bool:
    host, _, port = url.replace("http://", "").replace("https://", "").partition(":")
    host = host.split("/")[0] or "127.0.0.1"
    try:
        p = int((port or "7890").split("/")[0])
    except ValueError:
        return False
    sock = socket.socket()
    sock.settimeout(0.4)
    try:
        sock.connect((host, p))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _openers():
    out = [("direct", urllib.request.build_opener(urllib.request.ProxyHandler({})))]
    proxy = (os.environ.get("TRADEMIND_HTTPS_PROXY") or "http://127.0.0.1:7890").strip()
    if proxy and _proxy_listen(proxy):
        out.append(("proxy", urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))))
    return out


TRANSPORT_RETRIES = 5       # 2026-09-11: ~1 in 2 requests dies with SSL UNEXPECTED_EOF / record layer failure; flaps clear in seconds
TRANSPORT_SLEEP_S = 8.0


def _request_once(method: str, path: str, data: Optional[bytes], key: str, timeout: float) -> Any:
    errors = []
    raw = ""
    for name, opener in _openers():
        req = urllib.request.Request(API + path, data=data, headers=_headers(key), method=method)
        try:
            with opener.open(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
            break
        except urllib.error.HTTPError as exc:
            err = exc.read().decode("utf-8", errors="replace")[:400]
            raise RuntimeError("Cursor HTTP %s: %s" % (exc.code, err)) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            errors.append("%s=%s" % (name, exc))
            continue
    else:
        raise RuntimeError("Cursor unreachable: " + "; ".join(errors))
    if not raw:
        return {}
    return json.loads(raw)


def _retryable(exc: Exception) -> bool:
    s = str(exc)
    return s.startswith("Cursor unreachable") or "Cursor HTTP 502" in s or "Cursor HTTP 503" in s or "Cursor HTTP 504" in s


def _request(method: str, path: str, body: Optional[Dict[str, Any]] = None, timeout: float = 30.0, retries: int = TRANSPORT_RETRIES) -> Any:
    key = load_key()
    if not key:
        raise RuntimeError("CURSOR_KEY_MISSING")
    data = None if body is None else json.dumps(body).encode("utf-8")
    last: Optional[Exception] = None
    for i in range(max(1, retries)):
        if i:
            time.sleep(TRANSPORT_SLEEP_S)
        try:
            return _request_once(method, path, data, key, timeout)
        except RuntimeError as exc:
            last = exc
            if not _retryable(exc):
                raise
    raise last  # type: ignore[misc]


def parse_catalog_id(catalog_id: str) -> Tuple[str, List[Dict[str, str]]]:
    catalog_id = (catalog_id or "").strip()
    if "?" not in catalog_id:
        return catalog_id, []
    api_id, _, qs = catalog_id.partition("?")
    params = [{"id": k, "value": v} for k, v in parse_qsl(qs, keep_blank_values=False) if k and v]
    return api_id, params


def catalog_key(api_id: str, params: Optional[List[Dict[str, str]]] = None) -> str:
    params = params or []
    if not params:
        return api_id
    return api_id + "?" + urlencode([(p["id"], p["value"]) for p in params])


def _param_label(param_defs: List[Dict[str, Any]], pid: str, val: str) -> str:
    for p in param_defs or []:
        if p.get("id") != pid:
            continue
        for v in p.get("values") or []:
            if str(v.get("value")) == str(val):
                return str(v.get("displayName") or val)
    return str(val)


def _has_param_value(param_defs: List[Dict[str, Any]], pid: str, val: str) -> bool:
    for p in param_defs or []:
        if p.get("id") != pid:
            continue
        return any(str(v.get("value")) == str(val) for v in (p.get("values") or []))
    return False


def _row(api_id: str, display: str, params: List[Dict[str, str]], param_defs: List[Dict[str, Any]]) -> Dict[str, Any]:
    bits = [display or api_id]
    for p in params:
        bits.append(_param_label(param_defs, p["id"], p["value"]))
    return {
        "id": catalog_key(api_id, params),
        "api_id": api_id,
        "params": list(params),
        "label": " · ".join(bits),
    }


def _preset_params(param_defs: List[Dict[str, Any]]) -> List[List[Dict[str, str]]]:
    extras: List[List[Dict[str, str]]] = []
    has_xhigh = _has_param_value(param_defs, "effort", "xhigh")
    has_fast = _has_param_value(param_defs, "fast", "true")
    if has_xhigh and has_fast:
        extras.append([{"id": "effort", "value": "xhigh"}, {"id": "fast", "value": "true"}])
    if has_xhigh:
        extras.append([{"id": "effort", "value": "xhigh"}])
    if has_fast:
        extras.append([{"id": "fast", "value": "true"}])
    return extras


def list_models() -> List[Dict[str, Any]]:
    global _models_cache
    now = time.time()
    if _models_cache[1] and now - _models_cache[0] < 60:
        return list(_models_cache[1])
    data = _request("GET", "/models")
    items = data.get("items") or data.get("data") or []
    out: List[Dict[str, Any]] = []
    for it in items:
        mid = (it or {}).get("id")
        if not mid:
            continue
        display = (it or {}).get("displayName") or mid
        defs = (it or {}).get("parameters") or []
        out.append(_row(mid, display, [], defs))
        grok = str(mid).startswith("grok-") or "Grok" in str(display)
        if grok:
            for params in _preset_params(defs):
                out.append(_row(mid, display, params, defs))
    _models_cache = (now, out)
    return list(out)


def preferred_model(models: Optional[List[Dict[str, Any]]] = None) -> str:
    rows = models if models is not None else []
    for want in ("grok-4.6?effort=xhigh&fast=true", "grok-4.6?effort=xhigh", "grok-4.6"):
        if any(m.get("id") == want for m in rows):
            return want
    return str((rows[0] or {}).get("id") or "") if rows else ""


def resolve_model(catalog_id: str) -> Tuple[str, str, List[Dict[str, str]]]:
    """Return (catalog_key, api_id, params). Raises ValueError if unknown."""
    models = list_models()
    mid = (catalog_id or "").strip()
    by_id = {m["id"]: m for m in models if m.get("id")}
    api_ids = {m.get("api_id") or parse_catalog_id(m["id"])[0] for m in models}
    if not mid:
        mid = preferred_model(models) or "composer-2.5"
    if mid in by_id:
        row = by_id[mid]
        api = row.get("api_id") or parse_catalog_id(row["id"])[0]
        return row["id"], api, list(row.get("params") or [])
    api, params = parse_catalog_id(mid)
    if api and api in api_ids:
        return catalog_key(api, params), api, params
    raise ValueError("unknown model id")


def list_agents(limit: int = 10) -> List[Dict[str, Any]]:
    r = _request("GET", "/agents?limit=%d" % int(limit), None, timeout=30.0)
    items = r.get("agents") or r.get("items") or r.get("data") or []
    return [a for a in items if isinstance(a, dict)]


def _iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


def _adopt_created(name: str, since_iso: str) -> Optional[Dict[str, Any]]:
    """POST /agents often succeeds server-side while the TLS read of the response dies. Before re-posting
    (which would create a duplicate, billable agent), look for an agent with our name created after `since`."""
    try:
        agents = list_agents(10)
    except Exception:
        return None
    cands = [a for a in agents if a.get("name") == name and str(a.get("createdAt") or "")[:19] >= since_iso]
    if not cands:
        return None
    cands.sort(key=lambda a: str(a.get("createdAt") or ""))
    a = cands[-1]
    run_id = a.get("latestRunId") or ""
    if not run_id:
        try:
            full = _request("GET", "/agents/%s" % a["id"], None, timeout=30.0)
            run_id = full.get("latestRunId") or ((full.get("run") or {}).get("id")) or ""
            a = full or a
        except Exception:
            pass
    return {"agent": a, "run": {"id": run_id}, "adopted": True}


def create_agent(prompt: str, model_id: str, params: Optional[List[Dict[str, str]]] = None, name: str = "TradeMind Hot Brief") -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "prompt": {"text": prompt},
        "name": name or "TradeMind Hot Brief",
        "mode": "agent",
    }
    if model_id:
        model: Dict[str, Any] = {"id": model_id}
        if params:
            model["params"] = params
        body["model"] = model
    since = _iso_now()
    last: Optional[Exception] = None
    for i in range(TRANSPORT_RETRIES):
        if i:
            time.sleep(TRANSPORT_SLEEP_S)
            adopted = _adopt_created(body["name"], since)
            if adopted:
                return adopted
        try:
            return _request("POST", "/agents", body, timeout=90.0, retries=1)
        except RuntimeError as exc:
            last = exc
            if not _retryable(exc):
                raise
    adopted = _adopt_created(body["name"], since)
    if adopted:
        return adopted
    raise last  # type: ignore[misc]


def get_run(agent_id: str, run_id: str) -> Dict[str, Any]:
    return _request("GET", "/agents/%s/runs/%s" % (agent_id, run_id), timeout=30.0)


def cancel_run(agent_id: str, run_id: str) -> Dict[str, Any]:
    return _request("POST", "/agents/%s/runs/%s/cancel" % (agent_id, run_id), {}, timeout=30.0)


def archive_agent(agent_id: str) -> None:
    try:
        _request("POST", "/agents/%s/archive" % agent_id, timeout=20.0)
    except Exception:
        pass


def wait_run(agent_id: str, run_id: str, timeout_s: float = 900.0) -> Dict[str, Any]:
    """Poll until terminal status or deadline. A failed poll (transport flap) is not a failed run: keep polling."""
    deadline = time.time() + timeout_s
    last: Dict[str, Any] = {}
    poll_errors = 0
    while time.time() < deadline:
        try:
            last = get_run(agent_id, run_id)
        except RuntimeError as exc:
            poll_errors += 1
            last["poll_error"] = str(exc)[:200]
            last["poll_errors"] = poll_errors
            time.sleep(6.0)
            continue
        st = str(last.get("status") or "")
        if st in ("FINISHED", "ERROR", "CANCELLED", "EXPIRED"):
            if poll_errors:
                last["poll_errors"] = poll_errors
            return last
        time.sleep(4.0)
    last["status"] = "TIMEOUT"
    last["error"] = "run timed out after %.0fs (poll_errors=%d)" % (timeout_s, poll_errors)
    return last
