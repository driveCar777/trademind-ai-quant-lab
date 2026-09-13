"""Routes for the :9001 hot desk only. Not included by the :9000 app."""
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.model.schemas import ErrorCode, api_error, api_success
from app.service import cursor_cloud as cc
from app.service import paper_hot as hot

router = APIRouter()


class HotBriefRequest(BaseModel):
    model: str = ""


class HotBook2Request(BaseModel):
    limit: Optional[int] = None
    tail: Optional[int] = None


class HotJournalRequest(BaseModel):
    type: Optional[str] = None
    date: Optional[str] = None
    symbol: Optional[str] = None
    lots: Optional[int] = None
    price: Optional[float] = None
    fee: Optional[float] = None
    amount: Optional[float] = None
    note: Optional[str] = None


def _html() -> HTMLResponse:
    path = Path(__file__).resolve().parents[4] / "dashboard" / "paper_hot.html"
    if not path.is_file():
        return HTMLResponse("<h1>paper_hot.html missing</h1>", status_code=404)
    return HTMLResponse(
        content=path.read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"},
    )


def _journal_payload(last: Optional[Dict[str, Any]] = None):
    j = hot.load_journal()
    from app.service import paper_ops as po
    account = hot.derive_account(j, po._days())
    return {"events": list(reversed(j["events"])), "account": account, "last_event": last}


@router.get("/paper", response_class=HTMLResponse)
def serve_paper():
    return _html()


@router.get("/api/v1/hot/desk")
def hot_desk():
    return api_success(hot.desk(), message="高风险实验台（不发单，不改 :9000）。")


@router.get("/api/v1/hot/symbol/{symbol}/curve")
def hot_symbol_curve(symbol: str):
    return api_success(hot.symbol_curve(symbol), message="该股收盘曲线（已有 live/bars，不是新家族）。")


@router.get("/api/v1/hot/models")
def hot_models():
    if not cc.key_present():
        return api_error(ErrorCode.WORKER_OFFLINE, "没有 Cursor 密钥。应在 D:\\Cursor\\APIKey.txt")
    try:
        return api_success({"models": cc.list_models()})
    except Exception as exc:
        return api_error(ErrorCode.WORKER_OFFLINE, str(exc)[:300])


@router.post("/api/v1/hot/brief")
def hot_brief(request: Optional[HotBriefRequest] = None):
    try:
        run = hot.start_brief((request.model if request else "") or "")
    except ValueError:
        return api_error(ErrorCode.WORKER_NOT_FOUND, "模型不在 Cursor 目录里，请从下拉框选。")
    except RuntimeError as exc:
        return api_error(ErrorCode.WORKER_OFFLINE, str(exc))
    return api_success(run, message=run.get("stage") or "已提交")


@router.get("/api/v1/hot/brief/status")
def hot_brief_status():
    return api_success(hot.brief_status())


@router.post("/api/v1/hot/brief/stop")
def hot_brief_stop():
    return api_success(hot.stop_brief(), message="已停止")


@router.post("/api/v1/hot/book1/run")
def hot_book1_run():
    return api_success(hot.start_book1(), message="账本1 已提交")


@router.post("/api/v1/hot/book2/run")
def hot_book2_run(request: Optional[HotBook2Request] = None):
    lim = request.limit if request else None
    tail = request.tail if request else None
    return api_success(hot.start_book2(lim, tail), message="账本2 已提交")


@router.post("/api/v1/hot/book2/stop")
def hot_book2_stop():
    return api_success(hot.stop_book2(), message="已停止")


class HotFusionRequest(BaseModel):
    model: str = ""


@router.get("/api/v1/hot/fusion")
def hot_fusion():
    from app.service import paper_fusion as fu
    return api_success(fu.view(), message="融合台（纸面，不是 Candidate，不发单）。")


@router.post("/api/v1/hot/fusion/run")
def hot_fusion_run(request: Optional[HotFusionRequest] = None):
    from app.service import paper_fusion as fu
    try:
        run = fu.start((request.model if request else "") or "")
    except ValueError:
        return api_error(ErrorCode.WORKER_NOT_FOUND, "模型不在 Cursor 目录里，请从下拉框选。")
    except RuntimeError as exc:
        return api_error(ErrorCode.WORKER_OFFLINE, str(exc))
    return api_success(run, message=run.get("stage") or "已提交")


@router.post("/api/v1/hot/fusion/stop")
def hot_fusion_stop():
    from app.service import paper_fusion as fu
    return api_success(fu.stop(), message="已停止")


class HotFusionSettingsRequest(BaseModel):
    auto_fill: Optional[bool] = None
    initial_capital: Optional[float] = None


@router.post("/api/v1/hot/fusion/daily")
def hot_fusion_daily(request: Optional[HotFusionRequest] = None):
    """Daily driver: settle pending plans at next open (simulated), then run the pipeline if bars are fresh."""
    from app.service import paper_fusion_fill as ff
    try:
        st = ff.start_daily((request.model if request else "") or "")
    except ValueError:
        return api_error(ErrorCode.WORKER_NOT_FOUND, "模型不在 Cursor 目录里。")
    except RuntimeError as exc:
        return api_error(ErrorCode.WORKER_OFFLINE, str(exc))
    return api_success(st, message=st.get("stage") or "已提交")


class HotFusionSessionRequest(BaseModel):
    session: str = "settle"
    model: str = ""


@router.post("/api/v1/hot/fusion/session")
def hot_fusion_session(request: HotFusionSessionRequest):
    """Scheduled sessions: open 09:35 / lunch 11:30 / close 15:05 (one Grok call each, at most) / daily 19:30 (settle; Grok only
    if the close plan is missing) / settle (never Grok). Paper only."""
    from app.service import paper_fusion_fill as ff
    try:
        st = ff.start_session(request.session, request.model or "")
    except ValueError as exc:
        return api_error(ErrorCode.TASK_FAILED, str(exc))
    except RuntimeError as exc:
        return api_error(ErrorCode.WORKER_OFFLINE, str(exc))
    return api_success(st, message=st.get("stage") or "已提交")


@router.post("/api/v1/hot/fusion/settle")
def hot_fusion_settle():
    """Settle only (no Grok). Idempotent."""
    from app.service import paper_fusion_fill as ff
    return api_success(ff.settle_pending(), message="已结算（模拟成交，按下一开盘）。")


@router.get("/api/v1/hot/fusion/settings")
def hot_fusion_settings_get():
    from app.service import paper_fusion_fill as ff
    return api_success(ff.settings())


@router.post("/api/v1/hot/fusion/settings")
def hot_fusion_settings_set(request: HotFusionSettingsRequest):
    from app.service import paper_fusion_fill as ff
    if request.auto_fill is None and request.initial_capital is None:
        return api_error(ErrorCode.TASK_FAILED, "auto_fill 或 initial_capital 至少一个")
    try:
        out = ff.settings()
        if request.auto_fill is not None:
            out = ff.set_auto_fill(request.auto_fill)
        if request.initial_capital is not None:
            out = ff.set_initial_capital(request.initial_capital)
    except ValueError as exc:
        return api_error(ErrorCode.TASK_FAILED, str(exc))
    return api_success(out, message="已保存（纸面账户设置）")


@router.get("/api/v1/hot/journal")
def hot_journal():
    return api_success(_journal_payload())


@router.post("/api/v1/hot/journal")
def hot_journal_add(request: HotJournalRequest):
    try:
        ev = hot.add_event(request.model_dump(exclude_none=True))
    except ValueError as exc:
        return api_error(ErrorCode.TASK_FAILED, str(exc))
    return api_success(_journal_payload(ev), message="已登记。")


@router.put("/api/v1/hot/journal/{event_id}")
def hot_journal_update(event_id: str, request: HotJournalRequest):
    try:
        ev = hot.update_event(event_id, request.model_dump(exclude_none=True))
    except KeyError:
        return api_error(ErrorCode.TASK_FAILED, "没有这条记录。")
    except ValueError as exc:
        return api_error(ErrorCode.TASK_FAILED, str(exc))
    return api_success(_journal_payload(ev), message="已修改。")


@router.delete("/api/v1/hot/journal/{event_id}")
def hot_journal_delete(event_id: str):
    try:
        hot.delete_event(event_id)
    except KeyError:
        return api_error(ErrorCode.TASK_FAILED, "没有这条记录。")
    return api_success(_journal_payload(), message="已删除。")


class HotMt5SessionRequest(BaseModel):
    session: str = "settle"
    model: str = ""


class HotMt5SettingsRequest(BaseModel):
    demo_send: Optional[bool] = None
    volume: Optional[float] = None


@router.get("/api/v1/hot/mt5")
def hot_mt5():
    from app.service import paper_hot_mt5 as mx
    return api_success(mx.view(), message="热台 MT5（Ava demo，分品种，不是 Candidate）。")


@router.get("/api/v1/hot/mt5/gold_follow")
def hot_mt5_gold_follow():
    from app.service import paper_hot_mt5 as mx
    return api_success(mx.gold_follow(True), message="黄金 V4 跟盘（不是 Candidate，不写 Grok）。")


@router.post("/api/v1/hot/mt5/session")
def hot_mt5_session(request: Optional[HotMt5SessionRequest] = None):
    from app.service import paper_hot_mt5 as mx
    req = request or HotMt5SessionRequest()
    try:
        st = mx.start_session(req.session, req.model or "")
    except ValueError as exc:
        return api_error(ErrorCode.TASK_FAILED, str(exc))
    except RuntimeError as exc:
        return api_error(ErrorCode.WORKER_OFFLINE, str(exc))
    return api_success(st, message=st.get("stage") or "已提交")


@router.get("/api/v1/hot/mt5/settings")
def hot_mt5_settings_get():
    from app.service import paper_hot_mt5 as mx
    return api_success(mx.settings())


@router.post("/api/v1/hot/mt5/settings")
def hot_mt5_settings_set(request: HotMt5SettingsRequest):
    from app.service import paper_hot_mt5 as mx
    if request.demo_send is None and request.volume is None:
        return api_error(ErrorCode.TASK_FAILED, "demo_send 或 volume 至少一个")
    try:
        out = mx.save_settings({"demo_send": request.demo_send, "volume": request.volume})
    except ValueError as exc:
        return api_error(ErrorCode.TASK_FAILED, str(exc))
    return api_success(out, message="已保存（demo 发单开关）")
