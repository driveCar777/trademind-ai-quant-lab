"""Pydantic schemas for TradeMind Master API v1.1."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorCode(str, Enum):
    """V1.2 error codes."""

    SUCCESS = "TM-0000"
    WORKER_NOT_FOUND = "TM-1001"
    WORKER_OFFLINE = "TM-1002"
    TASK_FAILED = "TM-1003"
    TIMEOUT = "TM-1004"
    WORKER_BUSY = "TM-1005"


class TaskStatus(str, Enum):
    """Task lifecycle states (uppercase only)."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WorkerStatus(str, Enum):
    """Worker runtime states (uppercase only)."""

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class ApiResponse(BaseModel, Generic[T]):
    """Unified API response wrapper for all business endpoints."""

    success: bool
    message: str = ""
    code: ErrorCode
    data: Optional[T] = None


class HealthResponse(BaseModel):
    """Health probe response (not wrapped in ApiResponse)."""

    status: str
    service: str
    version: str
    uptime_seconds: float
    timestamp: datetime


class WorkerInfo(BaseModel):
    """Worker registration + runtime status."""

    id: str
    name: str
    worker_type: str
    host: str
    port: int
    description: str = ""
    status: WorkerStatus = WorkerStatus.OFFLINE
    latency_ms: Optional[float] = None


class WorkersData(BaseModel):
    """Payload for GET /workers."""

    workers: List[WorkerInfo]
    count: int


class OpsActionData(BaseModel):
    """Payload for POST /api/v1/ops/*."""

    worker_id: Optional[str] = None
    action: str
    accepted: bool
    hint: str = ""


class AIChatMessage(BaseModel):
    """Single chat message for AI Gateway proxy."""

    role: str
    content: str


class AIGenerateRequest(BaseModel):
    """POST /api/v1/ai/generate body (proxied to AI Gateway)."""

    type: str = Field(default="research_report", min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)


class AIDescribeRequest(BaseModel):
    """POST /api/v1/ai/describe body (proxied to AI Gateway)."""

    type: str = Field(default="strategy_description", min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)


class AISignalRequest(BaseModel):
    """POST /api/v1/ai/signal body (proxied to AI Gateway)."""

    type: str = Field(default="signal_interpretation", min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)


class AIChatRequest(BaseModel):
    """POST /api/v1/ai/chat body (proxied to AI Gateway)."""

    messages: List[AIChatMessage] = Field(..., min_length=1)
    params: Dict[str, Any] = Field(default_factory=dict)


class TaskRequest(BaseModel):
    """POST /task request body."""

    worker_type: str = Field(default="indicator-worker", min_length=1, max_length=32)
    indicator: str = Field(..., min_length=2, max_length=16)
    data: Dict[str, Any]
    params: Dict[str, Any] = Field(default_factory=dict)


class TaskCreateData(BaseModel):
    """Payload for POST /task response data."""

    task_id: str
    status: TaskStatus
    worker_id: Optional[str] = None


class TaskDetailData(BaseModel):
    """Payload for GET /task/{id} response data."""

    task_id: str
    status: TaskStatus
    worker_type: str
    worker_id: Optional[str] = None
    request: Dict[str, Any]
    result_path: Optional[str] = None
    result_exists: bool = False
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


class TasksListData(BaseModel):
    """Payload for GET /tasks response."""

    tasks: List[TaskDetailData]
    count: int


class ResearchRunRequest(BaseModel):
    """POST /api/v1/research/run body."""

    preset: Optional[str] = None
    chain: Optional[List[str]] = None
    sample_id: Optional[str] = None
    source: Optional[str] = None
    symbol: Optional[str] = None


class ResearchStepData(BaseModel):
    """One step inside a research run."""

    preset: str
    task_id: str
    summary: str


class ResearchTradeData(BaseModel):
    """One stamped backtest fill. Not an order."""

    split: str = ""
    side: str = ""
    idx: int = 0
    time: str = ""
    price: Optional[float] = None
    pnl_pct: Optional[float] = None
    regime: str = ""


class ResearchData(BaseModel):
    """One research record."""

    research_id: str
    task_id: str
    preset: str
    summary: str
    ai_text: str
    ai_skipped: bool = False
    created_at: str
    steps: List[ResearchStepData] = Field(default_factory=list)
    sample_id: str = ""
    source: str = ""
    symbol: str = ""
    verdict: str = ""
    bars: int = 0
    timeframe: str = ""
    window_from: str = ""
    window_to: str = ""
    trades: List[ResearchTradeData] = Field(default_factory=list)
    cut: int = 0
    carry: bool = False
    basket: List[Dict[str, Any]] = Field(default_factory=list)
    regime_counts: Dict[str, Any] = Field(default_factory=dict)
    regime_table: List[Dict[str, Any]] = Field(default_factory=list)
    mine: List[Dict[str, Any]] = Field(default_factory=list)
    picked: str = ""
    mine_workers: List[str] = Field(default_factory=list)


class ResearchListData(BaseModel):
    """GET /api/v1/research list payload."""

    items: List[ResearchData]
    count: int


class SampleItem(BaseModel):
    """One local CSV sample."""

    sample_id: str
    filename: str
    rows: int
    symbol: str = ""
    kind: str = ""


class SampleListData(BaseModel):
    """GET /api/v1/samples payload."""

    items: List[SampleItem]
    count: int


class OrderPreviewRequest(BaseModel):
    """POST /api/v1/orders/preview body."""

    research_id: str = Field(..., min_length=3)


class OrderSubmitRequest(BaseModel):
    """POST /api/v1/orders/submit body."""

    research_id: str = Field(..., min_length=3)
    confirm: bool = False
    side: Optional[str] = None


class OrderData(BaseModel):
    """One paper order or preview."""

    order_id: str = ""
    research_id: str
    symbol: str
    side: str
    volume: float
    status: str
    mode: str = "paper"
    reason: str = ""
    mt5_connected: bool = False
    account_mode: str = "offline"
    created_at: str
    mt5_ticket: str = ""
    wire_test: bool = False


class OrderListData(BaseModel):
    """GET /api/v1/orders list payload."""

    items: List[OrderData]
    count: int


class DeskTodayData(BaseModel):
    """GET /api/v1/desk/today payload."""

    date: str
    research: List[ResearchData] = Field(default_factory=list)
    orders: List[OrderData] = Field(default_factory=list)
    research_count: int = 0
    order_count: int = 0


class MT5StatusData(BaseModel):
    """GET /api/v1/mt5/status payload."""

    available: bool = False
    connected: bool = False
    account_mode: str = "offline"
    login_masked: str = ""
    reason: str = ""
    symbols: List[Dict[str, Any]] = Field(default_factory=list)


class MT5QuotesData(BaseModel):
    """GET /api/v1/mt5/quotes payload."""

    account_mode: str = "offline"
    items: List[Dict[str, Any]] = Field(default_factory=list)


class PaperPreviewRequest(BaseModel):
    """POST /api/v1/paper/preview — resize lots from last SIGNAL. Does not retune ML1."""

    capital: float = Field(..., gt=0)
    monthly_contrib: Optional[float] = None
    max_price: Optional[float] = None
    n_target: Optional[int] = None
    boards: Optional[str] = None


class PaperSettingsRequest(BaseModel):
    """PUT /api/v1/paper/settings — persist preview defaults only."""

    capital: Optional[float] = None
    monthly_contrib: Optional[float] = None
    max_price: Optional[float] = None
    n_target: Optional[int] = None
    boards: Optional[str] = None


class PaperDeskData(BaseModel):
    asof_session: Optional[str] = None
    contract: Optional[str] = None
    status: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)
    shortlist: Optional[Dict[str, Any]] = None
    shortlist_file: Optional[str] = None
    signal_file: Optional[str] = None
    holdings: List[Dict[str, Any]] = Field(default_factory=list)
    holdings_official: List[Dict[str, Any]] = Field(default_factory=list)
    holdings_august: List[Dict[str, Any]] = Field(default_factory=list)
    holdings_august_official: List[Dict[str, Any]] = Field(default_factory=list)
    books: Dict[str, Any] = Field(default_factory=dict)
    window: Dict[str, Any] = Field(default_factory=dict)
    curves: Dict[str, Any] = Field(default_factory=dict)
    preset_replay: Optional[Dict[str, Any]] = None
    ledger: Optional[Dict[str, Any]] = None
    august: Optional[Dict[str, Any]] = None
    orders_sent: bool = False


class PaperPreviewData(BaseModel):
    contract: str
    capital: float
    unit_yuan: float
    n_target: int
    n_names: int
    est_invested_yuan: float
    cash_yuan: float
    skipped_price_too_high: int = 0
    preview: bool = True
    boards: str
    max_price: float
    names: List[Dict[str, Any]]
    note: str = ""
    monthly_contrib: Optional[float] = None
    signal_date: Optional[str] = None
    replay: Optional[Dict[str, Any]] = None


class PaperOpsData(BaseModel):
    """GET /api/v1/paper/ops — SPEC §29.6. Plan for today on the real calendar; no orders."""

    freshness: Dict[str, Any] = Field(default_factory=dict)
    run: Dict[str, Any] = Field(default_factory=dict)
    plan: Dict[str, Any] = Field(default_factory=dict)
    account: Dict[str, Any] = Field(default_factory=dict)
    model_positions: List[Dict[str, Any]] = Field(default_factory=list)
    model_summary: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    journal_events: List[Dict[str, Any]] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)
    faq: List[Dict[str, Any]] = Field(default_factory=list)
    orders_sent: bool = False


class PaperRunData(BaseModel):
    """POST /api/v1/paper/update, GET /api/v1/paper/update/status — SPEC §29.7."""

    running: bool = False
    reused: Optional[bool] = None
    pid: Optional[int] = None
    started_at: Optional[str] = None
    elapsed_s: Optional[float] = None
    stage: Optional[str] = None
    log: Optional[str] = None
    log_tail: List[str] = Field(default_factory=list)
    last_run: Dict[str, Any] = Field(default_factory=dict)
    last_failed: Optional[Dict[str, Any]] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)
    python: Optional[str] = None


class PaperUpdateRequest(BaseModel):
    force: bool = False


class PaperJournalEventRequest(BaseModel):
    """POST /api/v1/paper/journal — SPEC §29.8. Append-only."""

    type: str
    date: Optional[str] = None
    symbol: Optional[str] = None
    lots: Optional[int] = None
    price: Optional[float] = None
    fee: Optional[float] = None
    amount: Optional[float] = None
    note: Optional[str] = None


class PaperJournalData(BaseModel):
    events: List[Dict[str, Any]] = Field(default_factory=list)
    account: Dict[str, Any] = Field(default_factory=dict)
    last_event: Optional[Dict[str, Any]] = None


def api_success(
    data: T,
    message: str = "",
    code: ErrorCode = ErrorCode.SUCCESS,
) -> ApiResponse[T]:
    """Build a successful unified API response."""
    return ApiResponse(success=True, message=message, code=code, data=data)


def api_error(
    code: ErrorCode,
    message: str,
    data: Optional[T] = None,
) -> ApiResponse[T]:
    """Build a failed unified API response."""
    return ApiResponse(success=False, message=message, code=code, data=data)


# Type aliases for route response_model declarations.
WorkersResponse = ApiResponse[WorkersData]
TaskCreateResponse = ApiResponse[TaskCreateData]
TaskDetailResponse = ApiResponse[TaskDetailData]
TasksListResponse = ApiResponse[TasksListData]
OpsActionResponse = ApiResponse[OpsActionData]
ResearchResponse = ApiResponse[ResearchData]
ResearchListResponse = ApiResponse[ResearchListData]
OrderResponse = ApiResponse[OrderData]
OrderListResponse = ApiResponse[OrderListData]
DeskTodayResponse = ApiResponse[DeskTodayData]
MT5StatusResponse = ApiResponse[MT5StatusData]
MT5QuotesResponse = ApiResponse[MT5QuotesData]
SampleListResponse = ApiResponse[SampleListData]
PaperDeskResponse = ApiResponse[PaperDeskData]
PaperPreviewResponse = ApiResponse[PaperPreviewData]
PaperOpsResponse = ApiResponse[PaperOpsData]
PaperRunResponse = ApiResponse[PaperRunData]
PaperJournalResponse = ApiResponse[PaperJournalData]
