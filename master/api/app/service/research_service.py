"""V4.0: one research run = one existing task + at most one AI call."""

from __future__ import print_function

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from app.config.settings import get_settings
from app.model.schemas import TaskRequest
from app.service.exceptions import (
    TaskFailedError,
    TaskNotFoundError,
    TaskTimeoutError,
    WorkerBusyError,
    WorkerNotFoundError,
    WorkerOfflineError,
)
from app.service.mt5_service import fetch_closes, fetch_history
from app.service.sample_service import load_payload, resolve_sample_id
from app.service.walkforward_service import (
    CANDIDATES,
    attribute_regimes,
    describe as wf_describe,
    fold_regimes,
    judge,
    payload_for,
    pick_is,
    score_is,
    split_closes,
    stamp_trades,
    summarize as wf_summarize,
    window_of,
)
from app.service.task_service import TaskService
from app.service.worker_registry import WorkerRegistry

RUN_LOCK = threading.Lock()

PRESETS = {
    "indicator": {
        "worker_type": "indicator-worker",
        "indicator": "RSI",
        "data": {},
        "params": {"period": 14},
    },
    "factor": {
        "worker_type": "stock-factor-worker",
        "indicator": "factor",
        "data": {},
        "params": {},
    },
    "backtest": {
        "worker_type": "backtest-worker",
        "indicator": "backtest",
        "data": {},
        "params": {},
    },
    "monitor": {
        "worker_type": "monitor-worker",
        "indicator": "status",
        "data": {"type": "metrics"},
        "params": {},
    },
}

_PRESET_ORDER = ("indicator", "factor", "backtest", "monitor")


def _research_dir() -> Path:
    path = get_settings().data_root / "research"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _next_id() -> str:
    day = datetime.utcnow().strftime("%Y%m%d")
    prefix = "tm-research-%s-" % day
    highest = 0
    for item in _research_dir().glob(prefix + "*.json"):
        try:
            highest = max(highest, int(item.stem.split("-")[-1]))
        except ValueError:
            continue
    return "%s%06d" % (prefix, highest + 1)


def _save(record: Dict[str, Any]) -> None:
    path = _research_dir() / ("%s.json" % record["research_id"])
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def _load(research_id: str) -> Dict[str, Any]:
    path = _research_dir() / ("%s.json" % research_id)
    if not path.is_file():
        raise TaskNotFoundError(research_id)
    return json.loads(path.read_text(encoding="utf-8"))


def recommend_preset(workers: List[Any]) -> Optional[str]:
    online_types = set()
    for worker in workers:
        status = getattr(worker, "status", None)
        status_value = status.value if hasattr(status, "value") else status
        if str(status_value) == "ONLINE":
            online_types.add(getattr(worker, "worker_type", ""))
    for name in _PRESET_ORDER:
        if PRESETS[name]["worker_type"] in online_types:
            return name
    return None


def summarize_result(preset: str, result: Dict[str, Any]) -> str:
    if preset == "indicator":
        inner = result.get("result") or {}
        latest = inner.get("latest")
        symbol = result.get("symbol") or ""
        indicator = result.get("indicator") or "RSI"
        if latest is not None:
            return "%s %s 最新 %s" % (symbol, indicator, round(float(latest), 2))
    if preset == "factor":
        score = result.get("score") or {}
        return "%s 评分 %s %s" % (
            result.get("stock") or "",
            score.get("total", "—"),
            score.get("grade") or "",
        )
    if preset == "backtest":
        return "%s 收益 %s 回撤 %s 胜率 %s" % (
            result.get("symbol") or "",
            result.get("profit"),
            result.get("max_drawdown"),
            result.get("win_rate"),
        )
    if preset == "monitor":
        cluster = result.get("cluster") or {}
        return "集群健康 %s/%s" % (
            cluster.get("healthy_nodes", "?"),
            cluster.get("total_nodes", "?"),
        )
    return "已完成"


def context_for_ai(preset: str, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if preset == "indicator":
        inner = result.get("result") or {}
        latest = inner.get("latest")
        period = inner.get("period") or 14
        name = str(result.get("indicator") or "RSI").lower()
        indicators = {}
        if latest is not None:
            indicators["%s_%s" % (name, period)] = round(float(latest), 4)
        return {
            "symbol": result.get("symbol") or "UNKNOWN",
            "indicators": indicators,
            "source": "worker_result",
            "note": "来自节点计算结果，不是实时行情",
        }
    if preset == "factor":
        return {
            "stock": result.get("stock"),
            "date": result.get("date"),
            "score": result.get("score"),
            "source": "worker_result",
            "note": "来自内置因子库，不是实时行情",
        }
    if preset == "backtest":
        note = "合成K线回测，不是历史真行情"
        if result.get("verdict"):
            note = "MT5 样本内/外回测。survived 只表示本次未证伪，不是收益保证。"
        inner = {
            "profit": result.get("profit"),
            "max_drawdown": result.get("max_drawdown"),
            "win_rate": result.get("win_rate"),
            "total_trades": result.get("total_trades"),
            "sharpe_ratio": result.get("sharpe_ratio"),
            "profit_factor": result.get("profit_factor"),
        }
        return {
            "strategy": result.get("strategy") or "RSI",
            "symbol": result.get("symbol"),
            "params": {
                "timeframe": result.get("timeframe") or "",
                "bars": result.get("bars") or 0,
            },
            "result": inner,
            "benchmark": {
                "verdict": result.get("verdict") or "",
                "is_profit": result.get("is_profit"),
                "oos_profit": result.get("oos_profit"),
                "is_trades": result.get("is_trades"),
                "oos_trades": result.get("oos_trades"),
                "note": note,
            },
            "source": "worker_result",
            "note": note,
        }
    return None


def _call_ai(preset: str, context: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    if preset == "indicator":
        path, body = "/api/v1/ai/signal", {
            "type": "signal_interpretation",
            "context": context,
            "params": {"max_tokens": 512},
        }
    elif preset == "factor":
        path, body = "/api/v1/ai/generate", {
            "type": "research_report",
            "context": context,
            "params": {"max_tokens": 768},
        }
    elif preset == "backtest":
        path, body = "/api/v1/ai/describe", {
            "type": "strategy_description",
            "context": context,
            "params": {"max_tokens": 512},
        }
    else:
        return {"ai_skipped": True, "ai_text": "监控结果只保留摘要，不自动问模型。"}

    try:
        resp = requests.post(
            settings.ai_gateway.url.rstrip("/") + path,
            json=body,
            timeout=int(settings.ai_gateway.timeout_seconds),
        )
    except requests.Timeout:
        return {"ai_skipped": True, "ai_text": "通义千问超时，数字已保存。"}
    except requests.RequestException:
        return {"ai_skipped": True, "ai_text": "通义千问离线，数字已保存。"}

    if resp.status_code == 503:
        return {"ai_skipped": True, "ai_text": "通义千问忙碌或未加载，数字已保存。"}
    if resp.status_code != 200:
        return {"ai_skipped": True, "ai_text": "通义千问返回 %s，数字已保存。" % resp.status_code}

    try:
        payload = resp.json()
    except ValueError:
        return {"ai_skipped": True, "ai_text": "通义千问响应无法解析，数字已保存。"}

    data = payload.get("data") or {}
    text = data.get("report") or data.get("description") or data.get("interpretation") or data.get("reply") or ""
    if not text:
        return {"ai_skipped": True, "ai_text": "通义千问没有正文，数字已保存。"}
    return {"ai_skipped": False, "ai_text": text}


def _backtest_accepts_close(workers: List[Any]) -> bool:
    for worker in workers:
        status = getattr(worker, "status", None)
        status_value = status.value if hasattr(status, "value") else status
        if getattr(worker, "worker_type", "") != "backtest-worker" or str(status_value) != "ONLINE":
            continue
        try:
            resp = requests.get("http://%s:%s/version" % (worker.host, worker.port), timeout=5)
            body = resp.json() if resp.status_code == 200 else {}
        except (requests.RequestException, ValueError):
            return False
        version = str(body.get("version") or "")
        return version >= "2.1.4"
    return False


def _backtest_nodes(workers: List[Any]) -> List[Any]:
    nodes = []
    for worker in workers:
        status = getattr(worker, "status", None)
        status_value = status.value if hasattr(status, "value") else status
        if getattr(worker, "worker_type", "") == "backtest-worker" and str(status_value) == "ONLINE":
            nodes.append(worker)
    return nodes


def _direct_backtest(worker: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = "http://%s:%s/backtest" % (worker.host, worker.port)
    resp = requests.post(url, json=payload, timeout=90)
    try:
        body = resp.json()
    except ValueError:
        raise TaskFailedError("回测节点返回不是 JSON")
    if resp.status_code != 200 or (body.get("is") is None and not body.get("success")):
        raise TaskFailedError(body.get("error") or "回测节点失败")
    if body.get("is") is None or body.get("oos") is None:
        raise TaskFailedError("回测节点没有连续切分结果，需要 2.1.4")
    return body


def _fanout_backtests(nodes: List[Any], jobs: List[Any]) -> List[Any]:
    if not nodes:
        raise WorkerOfflineError("backtest-worker")
    out = [None] * len(jobs)
    workers_n = min(8, max(len(nodes) * 2, 4), len(jobs))

    def work(index):
        cand, payload = jobs[index]
        node = nodes[index % len(nodes)]
        body = _direct_backtest(node, payload)
        return index, cand, body, getattr(node, "id", "")

    with ThreadPoolExecutor(max_workers=workers_n) as pool:
        futs = [pool.submit(work, i) for i in range(len(jobs))]
        for fut in as_completed(futs):
            index, cand, body, worker_id = fut.result()
            out[index] = (cand, body, worker_id)
    return out


def _run_one_backtest(tasks: TaskService, payload: Dict[str, Any]) -> Dict[str, Any]:
    request = TaskRequest(
        worker_type="backtest-worker",
        indicator="backtest",
        data=payload,
        params={},
    )
    created = tasks.submit_task(request)
    detail = tasks.get_task(created.task_id)
    if detail.status.value != "COMPLETED" or not detail.result:
        raise TaskFailedError("回测没有结果正文")
    return {"task_id": created.task_id, "result": detail.result}


def _pack_wf(pulled, run, cut, verdict, basket, regime_table=None, regime_counts=None):
    closes = pulled.get("close") or []
    times = pulled.get("time") or []
    broker = pulled.get("symbol") or ""
    body = run["result"] or {}
    is_row = body.get("is") or {}
    oos_row = body.get("oos") or {}
    ledger = []
    if len(times) == len(closes) and cut > 0:
        ledger = stamp_trades(is_row.get("trades") or [], times, "样本内")
        ledger.extend(stamp_trades(oos_row.get("trades") or [], times, "样本外"))
    window_from, window_to = window_of(times)
    merged = {
        "symbol": broker,
        "strategy": (run.get("strategy") or body.get("strategy") or "RSI"),
        "verdict": verdict,
        "is_profit": is_row.get("profit"),
        "oos_profit": oos_row.get("profit"),
        "is_drawdown": is_row.get("max_drawdown"),
        "oos_drawdown": oos_row.get("max_drawdown"),
        "is_trades": is_row.get("total_trades"),
        "oos_trades": oos_row.get("total_trades"),
        "total_trades": oos_row.get("total_trades"),
        "bars": len(closes),
        "timeframe": pulled.get("timeframe") or "",
        "profit": oos_row.get("profit"),
        "max_drawdown": oos_row.get("max_drawdown"),
        "window_from": window_from,
        "window_to": window_to,
        "trades": ledger,
        "cut": cut,
        "carry": True,
        "basket": basket,
        "regime_counts": regime_counts or body.get("regime_counts") or {},
        "regime_table": regime_table or [],
        "mine": run.get("mine") or [],
        "picked": run.get("picked") or "",
        "mine_workers": run.get("mine_workers") or [],
    }
    return {
        "preset": "backtest",
        "task_id": run["task_id"],
        "summary": wf_summarize(
            broker,
            verdict,
            is_row,
            oos_row,
            len(closes),
            pulled.get("timeframe") or "",
            strategy=merged["strategy"],
        ),
        "result": merged,
        "source": "mt5",
        "symbol": broker,
        "sample_id": "",
        "verdict": verdict,
        "bars": len(closes),
        "timeframe": pulled.get("timeframe") or "",
        "window_from": window_from,
        "window_to": window_to,
        "trades": ledger,
        "cut": cut,
        "carry": True,
        "basket": basket,
        "regime_counts": regime_counts or body.get("regime_counts") or {},
        "regime_table": regime_table or [],
        "mine": run.get("mine") or [],
        "picked": run.get("picked") or "",
        "mine_workers": run.get("mine_workers") or [],
        "steps_extra": [
            {"preset": "backtest", "task_id": run["task_id"], "summary": "样本内筛选 %s 选中 %s 内%s 外%s" % (pulled.get("timeframe"), run.get("picked") or merged["strategy"], is_row.get("profit"), oos_row.get("profit"))},
        ],
    }


def _run_mt5_backtest_step(tasks: TaskService, symbol: Optional[str] = None) -> Dict[str, Any]:
    last = None
    nodes = _backtest_nodes(tasks._registry.list_workers())
    for timeframe, bars in (("H1", 2000), ("M15", 2000), ("H4", 1000)):
        pulled = fetch_history(symbol or "XAUUSD", bars=bars, timeframe=timeframe)
        closes = pulled.get("close") or []
        try:
            is_closes, _oos_closes = split_closes(closes)
        except ValueError:
            continue
        cut = len(is_closes)
        broker = pulled.get("symbol") or ""
        jobs = []
        for cand in CANDIDATES:
            payload = payload_for(
                broker,
                closes,
                "%s-%s" % (cand["id"], timeframe),
                cut=cut,
                strategy=cand["strategy"],
                params=cand.get("params") or {},
            )
            jobs.append((cand, payload))
        mined = _fanout_backtests(nodes, jobs)
        basket = []
        attr_rows = []
        mine_rows = []
        used = []
        for cand, body, worker_id in mined:
            verd = judge(body.get("is") or {}, body.get("oos") or {})
            is_row = body.get("is") or {}
            oos_row = body.get("oos") or {}
            attr_rows.extend(attribute_regimes(cand["id"], body))
            row = {
                "id": cand["id"],
                "strategy": cand["strategy"],
                "params": cand.get("params") or {},
                "worker_id": worker_id,
                "verdict": verd,
                "is_profit": is_row.get("profit"),
                "oos_profit": oos_row.get("profit"),
                "is_drawdown": is_row.get("max_drawdown"),
                "oos_drawdown": oos_row.get("max_drawdown"),
                "is_trades": is_row.get("total_trades"),
                "oos_trades": oos_row.get("total_trades"),
                "is_score": score_is(is_row),
                "picked": False,
            }
            mine_rows.append(row)
            basket.append(row)
            if worker_id and worker_id not in used:
                used.append(worker_id)
        picked = pick_is(mine_rows)
        if picked is None:
            picked = mine_rows[0] if mine_rows else None
        if picked is None:
            continue
        picked["picked"] = True
        winner_body = None
        for cand, body, _wid in mined:
            if cand["id"] == picked["id"]:
                winner_body = body
                break
        if winner_body is None:
            continue
        verd = judge(winner_body.get("is") or {}, winner_body.get("oos") or {})
        run = {
            "task_id": "tm-mine-%s" % picked["id"],
            "result": winner_body,
            "strategy": picked["strategy"],
            "mine": mine_rows,
            "picked": picked["id"],
            "mine_workers": used,
        }
        last = _pack_wf(
            pulled,
            run,
            cut,
            verd,
            basket,
            regime_table=fold_regimes(attr_rows),
            regime_counts=winner_body.get("regime_counts") or {},
        )
        if verd != "insufficient":
            return last
    if last is None:
        raise TaskFailedError("MT5 历史不够切样本内/外")
    return last


def _is_online(workers: List[Any], worker_type: str) -> bool:
    for worker in workers:
        status = getattr(worker, "status", None)
        status_value = status.value if hasattr(status, "value") else status
        if getattr(worker, "worker_type", "") == worker_type and str(status_value) == "ONLINE":
            return True
    return False


def _resolve_names(
    preset: Optional[str],
    chain: Optional[List[str]],
    workers: List[Any],
) -> List[str]:
    names = [str(item) for item in (chain or []) if item]
    if names:
        if preset not in (None, "") and names != [preset]:
            raise WorkerNotFoundError("chain")
        if len(names) < 1 or len(names) > 2:
            raise WorkerNotFoundError("chain")
        for name in names:
            if name not in PRESETS:
                raise WorkerNotFoundError(name)
        return names
    if preset in ("", None):
        chosen = recommend_preset(workers)
        if chosen is None:
            raise WorkerOfflineError("research")
        return [chosen]
    if preset not in PRESETS:
        raise WorkerNotFoundError(str(preset))
    return [preset]


def _run_step(
    tasks: TaskService,
    name: str,
    sample_id: Optional[str] = None,
    source: Optional[str] = None,
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    spec = PRESETS[name]
    payload = dict(spec["data"])
    used_sample = None
    used_source = "csv"
    used_symbol = ""
    if (source or "").strip().lower() == "mt5":
        if name == "backtest":
            return _run_mt5_backtest_step(tasks, symbol)
        if name != "indicator":
            raise WorkerNotFoundError("source")
        pulled = fetch_closes(symbol or "EURUSD")
        payload = {
            "symbol": pulled.get("symbol") or "",
            "close": pulled.get("close") or [],
        }
        used_source = "mt5"
        used_symbol = payload.get("symbol") or ""
    else:
        used_sample = resolve_sample_id(name, sample_id)
        if used_sample:
            payload = load_payload(name, used_sample)
            used_symbol = str(payload.get("symbol") or payload.get("stock") or "")
    request = TaskRequest(
        worker_type=spec["worker_type"],
        indicator=spec["indicator"],
        data=payload,
        params=dict(spec["params"]),
    )
    created = tasks.submit_task(request)
    detail = tasks.get_task(created.task_id)
    if detail.status.value != "COMPLETED" or not detail.result:
        raise TaskFailedError("研究计算没有结果正文")
    return {
        "preset": name,
        "task_id": created.task_id,
        "summary": summarize_result(name, detail.result),
        "result": detail.result,
        "source": used_source,
        "symbol": used_symbol,
        "sample_id": used_sample or "",
    }


def run_research(
    preset: Optional[str] = None,
    chain: Optional[List[str]] = None,
    sample_id: Optional[str] = None,
    source: Optional[str] = None,
    symbol: Optional[str] = None,
    registry: Optional[WorkerRegistry] = None,
    tasks: Optional[TaskService] = None,
) -> Dict[str, Any]:
    if chain and (len(chain) > 2 or any(name not in PRESETS for name in chain if name)):
        raise WorkerNotFoundError("chain")
    if preset not in (None, "") and preset not in PRESETS and not chain:
        raise WorkerNotFoundError(str(preset))

    if not RUN_LOCK.acquire(blocking=False):
        raise WorkerBusyError("research")

    try:
        registry = registry or WorkerRegistry()
        tasks = tasks or TaskService(registry=registry)
        workers = registry.list_workers()
        names = _resolve_names(preset, chain, workers)
        if (source or "").strip().lower() == "mt5":
            if names not in (["indicator"], ["backtest"]):
                raise WorkerNotFoundError("source")
            if names == ["backtest"] and not _backtest_accepts_close(workers):
                raise TaskFailedError("回测节点还不会行情分段，需要 2.1.4")
        else:
            for name in names:
                sid = resolve_sample_id(name, sample_id)
                if sid:
                    load_payload(name, sid)
        for name in names:
            wanted = PRESETS[name]["worker_type"]
            if not _is_online(workers, wanted):
                raise WorkerOfflineError(wanted)

        steps = []
        last = None
        for name in names:
            try:
                last = _run_step(tasks, name, sample_id=sample_id, source=source, symbol=symbol)
            except TaskTimeoutError:
                raise
            except (WorkerOfflineError, WorkerNotFoundError, TaskFailedError):
                raise
            extra = last.get("steps_extra") or []
            if extra:
                steps.extend(extra)
            else:
                steps.append({
                    "preset": last["preset"],
                    "task_id": last["task_id"],
                    "summary": last["summary"],
                })

        if last.get("verdict"):
            ai = {"ai_skipped": True, "ai_text": wf_describe(last.get("result") or {})}
        else:
            context = context_for_ai(last["preset"], last["result"])
            if context is None:
                ai = {"ai_skipped": True, "ai_text": last["summary"] + "（未问模型）"}
            else:
                ai = _call_ai(last["preset"], context)

        record = {
            "research_id": _next_id(),
            "task_id": last["task_id"],
            "preset": last["preset"],
            "summary": last["summary"],
            "ai_text": ai["ai_text"],
            "ai_skipped": ai["ai_skipped"],
            "created_at": _now_iso(),
            "steps": steps,
            "sample_id": last.get("sample_id") or "",
            "source": last.get("source") or "csv",
            "symbol": last.get("symbol") or "",
            "verdict": last.get("verdict") or "",
            "bars": last.get("bars") or 0,
            "timeframe": last.get("timeframe") or "",
            "window_from": last.get("window_from") or "",
            "window_to": last.get("window_to") or "",
            "trades": last.get("trades") or [],
            "cut": last.get("cut") or 0,
            "carry": bool(last.get("carry")),
            "basket": last.get("basket") or [],
            "regime_counts": last.get("regime_counts") or {},
            "regime_table": last.get("regime_table") or [],
            "mine": last.get("mine") or [],
            "picked": last.get("picked") or "",
            "mine_workers": last.get("mine_workers") or [],
        }
        _save(record)
        return record
    finally:
        RUN_LOCK.release()


def get_research(research_id: str) -> Dict[str, Any]:
    return _load(research_id)


def list_research(limit: int = 20) -> List[Dict[str, Any]]:
    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50
    rows = []
    for path in sorted(_research_dir().glob("tm-research-*.json")):
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            continue
    return rows[-limit:]
