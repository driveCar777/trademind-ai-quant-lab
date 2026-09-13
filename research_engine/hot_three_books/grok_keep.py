"""Call Cursor with an anonymous payload. Never log the API key."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from research_engine.hot_three_books import anon

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "master" / "api"
if str(API) not in sys.path:
    sys.path.insert(0, str(API))

ATTEMPTS = 2          # one retry per period; transport flaps are handled below this in cursor_cloud._request
TIMEOUT_S = 900.0     # 2026-09-11: 420 s was not the bottleneck (create_agent never got through), but xhigh runs can be slow
RETRY_SLEEP_S = 20.0


class GrokTimeout(RuntimeError):
    """All attempts timed out or errored. Caller must record GROK_TIMEOUT, not keep-all / keep-none."""


def _one_call(prompt: str, api_id: str, params, name: str, timeout_s: float) -> str:
    from app.service import cursor_cloud as cc
    created = cc.create_agent(prompt, api_id, params, name=name)
    agent = created.get("agent") or created
    run = created.get("run") or {}
    agent_id = agent.get("id") or created.get("id") or ""
    run_id = run.get("id") or agent.get("latestRunId") or created.get("runId") or ""
    try:
        if not agent_id or not run_id:
            raise RuntimeError("no agent/run")
        done = cc.wait_run(agent_id, run_id, timeout_s=timeout_s)
        st = str(done.get("status") or "")
        if st != "FINISHED":
            if st == "TIMEOUT":
                try:
                    cc.cancel_run(agent_id, run_id)
                except Exception:
                    pass
            raise RuntimeError(str(done.get("error") or st))
        text = done.get("result") or ""
        if isinstance(text, dict):
            text = text.get("text") or text.get("result") or json.dumps(text, ensure_ascii=False)
        return str(text)
    finally:
        if agent_id:
            cc.archive_agent(agent_id)


def ask_keep(payload: Dict[str, Any], valid_ids: List[str], model_id: str = "grok-4.6",
             attempts: int = ATTEMPTS, timeout_s: float = TIMEOUT_S, name: str = "TradeMind Book2 Anon") -> List[str]:
    from app.service import cursor_cloud as cc
    prompt = anon.PROMPT + anon.assert_clean(payload)
    errors: List[str] = []
    for i in range(max(1, int(attempts))):
        if i:
            time.sleep(RETRY_SLEEP_S)  # transport flaps (SSL EOF / 502) usually clear within a minute
        try:
            catalog, api_id, params = cc.resolve_model(model_id)
            text = _one_call(prompt, api_id, params, name, timeout_s)
            return anon.parse_keep(text, valid_ids)
        except Exception as exc:  # timeout / transport / non-FINISHED
            errors.append(str(exc)[:160])
    raise GrokTimeout("GROK_TIMEOUT after %d attempts: %s" % (attempts, " | ".join(errors)))
