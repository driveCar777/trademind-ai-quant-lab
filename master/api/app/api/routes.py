"""FastAPI route definitions for TradeMind Master API v1.3."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.config.settings import get_settings
from app.model.schemas import (
    AIChatRequest,
    AIDescribeRequest,
    AIGenerateRequest,
    AISignalRequest,
    DeskTodayData,
    DeskTodayResponse,
    HealthResponse,
    MT5QuotesData,
    MT5QuotesResponse,
    MT5StatusData,
    MT5StatusResponse,
    OpsActionResponse,
    OrderData,
    OrderListData,
    OrderListResponse,
    OrderPreviewRequest,
    OrderResponse,
    OrderSubmitRequest,
    PaperDeskData,
    PaperDeskResponse,
    PaperPreviewData,
    PaperPreviewRequest,
    PaperPreviewResponse,
    PaperSettingsRequest,
    ResearchData,
    ResearchListData,
    ResearchListResponse,
    ResearchResponse,
    ResearchRunRequest,
    SampleListData,
    SampleListResponse,
    TaskCreateResponse,
    TaskDetailResponse,
    TaskRequest,
    TasksListData,
    TasksListResponse,
    WorkersData,
    WorkersResponse,
    api_error,
    api_success,
    ErrorCode,
)
from app.model.schemas import (
    PaperJournalData,
    PaperJournalEventRequest,
    PaperJournalResponse,
    PaperOpsData,
    PaperOpsResponse,
    PaperRunData,
    PaperRunResponse,
    PaperUpdateRequest,
)
from app.service import paper_ops
from app.service.paper_service import desk as paper_desk
from app.service.paper_service import preview as paper_preview
from app.service.paper_service import save_settings as paper_save_settings
from app.service.ai_gateway_proxy import AIGatewayProxy
from app.service.ops_service import restart_master, start_worker
from app.service.mt5_service import list_quotes
from app.service.order_service import desk_today, get_order, list_orders, preview_order, probe_mt5, submit_order
from app.service.research_service import get_research, list_research, run_research
from app.service.sample_service import list_samples
from app.service.task_service import TaskService
from app.service.worker_registry import WorkerRegistry

router = APIRouter()
_start_time = datetime.utcnow()
_task_service = TaskService()
_worker_registry = WorkerRegistry()
_ai_gateway = AIGatewayProxy()


@router.get("/health", response_model=HealthResponse)
def health_check():
    settings = get_settings()
    now = datetime.utcnow()
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.version,
        uptime_seconds=round((now - _start_time).total_seconds(), 3),
        timestamp=now,
    )


@router.get("/workers", response_model=WorkersResponse)
def list_workers():
    workers = _worker_registry.list_workers()
    return api_success(WorkersData(workers=workers, count=len(workers)))


@router.post("/task", response_model=TaskCreateResponse)
def submit_task(request: TaskRequest):
    data = _task_service.submit_task(request)
    message = "Task completed." if data.status.value == "COMPLETED" else "Task submitted."
    return api_success(data, message=message)


@router.get("/task/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: str):
    data = _task_service.get_task(task_id)
    return api_success(data)


@router.get("/tasks", response_model=TasksListResponse)
def list_tasks(limit: int = 50):
    tasks = _task_service.list_tasks(limit=limit)
    return api_success(TasksListData(tasks=tasks, count=len(tasks)))


def _html(name):
    html_path = Path(__file__).resolve().parents[4] / "dashboard" / name
    if not html_path.exists():
        return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)
    return HTMLResponse(
        content=html_path.read_text(encoding="utf-8"),
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@router.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    return _html("index.html")


@router.get("/paper", response_class=HTMLResponse)
def serve_paper():
    return _html("paper.html")


@router.get("/paper/v1", response_class=HTMLResponse)
def serve_paper_v1():
    return _html("paper_v1.html")


@router.get("/api/v1/ai/health")
def proxy_ai_health():
    return _ai_gateway.forward("GET", "/health")


@router.get("/api/v1/ai/models")
def proxy_ai_models():
    return _ai_gateway.forward("GET", "/models")


@router.post("/api/v1/ai/generate")
def proxy_ai_generate(request: AIGenerateRequest):
    return _ai_gateway.forward("POST", "/api/v1/ai/generate", request.model_dump())


@router.post("/api/v1/ai/describe")
def proxy_ai_describe(request: AIDescribeRequest):
    return _ai_gateway.forward("POST", "/api/v1/ai/describe", request.model_dump())


@router.post("/api/v1/ai/signal")
def proxy_ai_signal(request: AISignalRequest):
    return _ai_gateway.forward("POST", "/api/v1/ai/signal", request.model_dump())


@router.post("/api/v1/ai/chat")
def proxy_ai_chat(request: AIChatRequest):
    return _ai_gateway.forward("POST", "/api/v1/ai/chat", request.model_dump())


@router.post("/api/v1/ops/worker/{worker_id}/start", response_model=OpsActionResponse)
def ops_start_worker(worker_id: str):
    return start_worker(worker_id, restart=False)


@router.post("/api/v1/ops/worker/{worker_id}/restart", response_model=OpsActionResponse)
def ops_restart_worker(worker_id: str):
    return start_worker(worker_id, restart=True)


@router.post("/api/v1/ops/master/restart", response_model=OpsActionResponse)
def ops_restart_master():
    return restart_master()


@router.post("/api/v1/research/run", response_model=ResearchResponse)
def research_run(request: ResearchRunRequest = ResearchRunRequest()):
    record = run_research(
        request.preset,
        chain=request.chain,
        sample_id=request.sample_id,
        source=request.source,
        symbol=request.symbol,
        registry=_worker_registry,
        tasks=_task_service,
    )
    hint = "研究完成（未问模型）。" if record.get("ai_skipped") else "研究完成。"
    return api_success(ResearchData(**record), message=hint)


@router.get("/api/v1/samples", response_model=SampleListResponse)
def samples_list():
    items = list_samples()
    return api_success(SampleListData(items=items, count=len(items)))


@router.get("/api/v1/research", response_model=ResearchListResponse)
def research_list(limit: int = 20):
    items = list_research(limit=limit)
    return api_success(ResearchListData(items=items, count=len(items)))


@router.get("/api/v1/research/{research_id}", response_model=ResearchResponse)
def research_detail(research_id: str):
    return api_success(ResearchData(**get_research(research_id)))


@router.get("/api/v1/desk/today", response_model=DeskTodayResponse)
def desk_today_view():
    return api_success(DeskTodayData(**desk_today()))


@router.get("/api/v1/mt5/status", response_model=MT5StatusResponse)
def mt5_status():
    return api_success(MT5StatusData(**probe_mt5()))


@router.get("/api/v1/mt5/quotes", response_model=MT5QuotesResponse)
def mt5_quotes():
    return api_success(MT5QuotesData(**list_quotes()))


@router.post("/api/v1/orders/preview", response_model=OrderResponse)
def order_preview(request: OrderPreviewRequest):
    return api_success(OrderData(**preview_order(request.research_id)), message="拟单（未落盘）。")


@router.post("/api/v1/orders/submit", response_model=OrderResponse)
def order_submit(request: OrderSubmitRequest):
    record = submit_order(request.research_id, request.confirm, side=request.side)
    hint = "已挂模拟单。" if record.get("status") == "ACCEPTED" else "已拒绝，记录已保存。"
    return api_success(OrderData(**record), message=hint)


@router.get("/api/v1/orders", response_model=OrderListResponse)
def order_list(limit: int = 20):
    items = list_orders(limit=limit)
    return api_success(OrderListData(items=items, count=len(items)))


@router.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
def order_detail(order_id: str):
    return api_success(OrderData(**get_order(order_id)))


@router.get("/api/v1/paper/desk", response_model=PaperDeskResponse)
def paper_desk_view():
    return api_success(PaperDeskData(**paper_desk()), message="A股纸面台（不发单）。")


@router.post("/api/v1/paper/preview", response_model=PaperPreviewResponse)
def paper_preview_view(request: PaperPreviewRequest):
    try:
        data = paper_preview(request.model_dump())
    except FileNotFoundError:
        return api_error(ErrorCode.TASK_FAILED, "没有 SIGNAL，先跑 daily.py。")
    except ValueError as exc:
        return api_error(ErrorCode.TASK_FAILED, str(exc))
    return api_success(PaperPreviewData(**data), message="手数预览，不是改合同。")


@router.put("/api/v1/paper/settings", response_model=PaperDeskResponse)
def paper_settings_view(request: PaperSettingsRequest):
    try:
        paper_save_settings(request.model_dump(exclude_none=True))
    except ValueError as exc:
        return api_error(ErrorCode.TASK_FAILED, str(exc))
    return api_success(PaperDeskData(**paper_desk()), message="已记下预览默认资金。")


# ---- Paper Ops Desk V2 (SPEC §29.5-29.8). No orders; daily.py runs with repository defaults only.
@router.get("/api/v1/paper/ops", response_model=PaperOpsResponse)
def paper_ops_view():
    return api_success(PaperOpsData(**paper_ops.ops()), message="今天的操作计划（不发单）。")


@router.post("/api/v1/paper/update", response_model=PaperRunResponse)
def paper_update_start(request: Optional[PaperUpdateRequest] = None):
    try:
        run = paper_ops.start_update(force=bool(request and request.force))
    except RuntimeError as exc:
        return api_error(ErrorCode.WORKER_BUSY, str(exc))
    except OSError as exc:
        return api_error(ErrorCode.TASK_FAILED, "启动失败：%s" % exc)
    msg = "已有一次更新在跑，给你看它的进度。" if run.get("reused") else "已在后台开始更新（约 35 分钟）。"
    return api_success(PaperRunData(**run), message=msg)


@router.get("/api/v1/paper/update/status", response_model=PaperRunResponse)
def paper_update_status():
    return api_success(PaperRunData(**paper_ops.run_status()))


@router.get("/api/v1/paper/journal", response_model=PaperJournalResponse)
def paper_journal_view():
    j = paper_ops.load_journal()
    return api_success(PaperJournalData(events=list(reversed(j["events"])), account=paper_ops.derive_account(j, paper_ops._days())))


@router.post("/api/v1/paper/journal", response_model=PaperJournalResponse)
def paper_journal_add(request: PaperJournalEventRequest):
    try:
        ev = paper_ops.add_event(request.model_dump(exclude_none=True))
    except ValueError as exc:
        return api_error(ErrorCode.TASK_FAILED, str(exc))
    j = paper_ops.load_journal()
    return api_success(PaperJournalData(events=list(reversed(j["events"])), account=paper_ops.derive_account(j, paper_ops._days()), last_event=ev),
                       message="已登记。")


@router.delete("/api/v1/paper/journal/{event_id}", response_model=PaperJournalResponse)
def paper_journal_delete(event_id: str):
    try:
        paper_ops.delete_event(event_id)
    except KeyError:
        return api_error(ErrorCode.TASK_FAILED, "没有这条记录。")
    j = paper_ops.load_journal()
    return api_success(PaperJournalData(events=list(reversed(j["events"])), account=paper_ops.derive_account(j, paper_ops._days())), message="已删除。")